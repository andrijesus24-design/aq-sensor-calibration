"""Quality-assurance flags for low-cost PM2.5 sensor data.

Every function returns a boolean Series where True means "flagged" (suspect).
Thresholds are parameters on purpose: they depend on the sensor, the site and
the client's QA plan, and should be agreed and documented per project.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


def flag_missing(s: pd.Series) -> pd.Series:
    return s.isna()


def flag_range(s: pd.Series, lo: float = 0.0, hi: float = 1000.0) -> pd.Series:
    """Values outside the physically plausible / sensor-rated range."""
    return (s < lo) | (s > hi)


def flag_stuck(s: pd.Series, min_run: int = 6) -> pd.Series:
    """Runs of >= min_run identical consecutive values (frozen output)."""
    changed = s.ne(s.shift())
    run_id = changed.cumsum()
    run_len = s.groupby(run_id).transform("size")
    return (run_len >= min_run) & s.notna()


def flag_spike(
    s: pd.Series, window: int = 25, k: float = 6.0, min_abs: float = 20.0
) -> pd.Series:
    """Hampel-type spike detector.

    Flags points whose distance to the centred rolling median exceeds
    k * 1.4826 * MAD and also exceeds min_abs (avoids flagging noise at
    very low concentrations).
    """
    med = s.rolling(window, center=True, min_periods=window // 2).median()
    mad = (s - med).abs().rolling(window, center=True, min_periods=window // 2).median()
    dev = (s - med).abs()
    return (dev > k * 1.4826 * mad) & (dev > min_abs)


def flag_channel_disagreement(
    a: pd.Series, b: pd.Series, abs_tol: float = 5.0, rel_tol: float = 0.7
) -> pd.Series:
    """Dual-channel check: flag when channels differ by more than abs_tol
    (ug/m3) AND by more than rel_tol relative to their mean."""
    diff = (a - b).abs()
    mean = (a + b) / 2
    rel = diff / mean.where(mean > 0)
    return (diff > abs_tol) & (rel > rel_tol)


def flag_high_rh(rh: pd.Series, max_rh: float = 95.0) -> pd.Series:
    """Very high humidity: optical sensors are least reliable here (fog)."""
    return rh > max_rh


@dataclass
class QAConfig:
    lo: float = 0.0
    hi: float = 1000.0
    stuck_min_run: int = 6
    spike_window: int = 25
    spike_k: float = 6.0
    spike_min_abs: float = 20.0
    channel_abs_tol: float = 5.0
    channel_rel_tol: float = 0.7
    max_rh: float = 95.0
    drop_high_rh: bool = False


@dataclass
class QAResult:
    data: pd.DataFrame  # original data + 'pm25_sensor' (clean, combined)
    flags: pd.DataFrame  # one boolean column per check
    summary: pd.DataFrame = field(default_factory=pd.DataFrame)


def run_qa(
    df: pd.DataFrame,
    a: str = "pm25_a",
    b: str | None = "pm25_b",
    rh: str | None = "rh",
    cfg: QAConfig | None = None,
) -> QAResult:
    """Apply all checks and build a cleaned combined sensor series.

    Per-channel checks (missing, range, stuck, spike) invalidate that channel
    only. If both channels survive but disagree, the hour is dropped. The
    cleaned value is the mean of the valid channels.
    """
    cfg = cfg or QAConfig()
    flags = pd.DataFrame(index=df.index)
    channels = [a] + ([b] if b else [])
    valid = {}
    for ch in channels:
        s = df[ch]
        flags[f"{ch}_missing"] = flag_missing(s)
        flags[f"{ch}_range"] = flag_range(s, cfg.lo, cfg.hi)
        flags[f"{ch}_stuck"] = flag_stuck(s, cfg.stuck_min_run)
        flags[f"{ch}_spike"] = flag_spike(s, cfg.spike_window, cfg.spike_k, cfg.spike_min_abs)
        bad = flags[[c for c in flags.columns if c.startswith(f"{ch}_")]].any(axis=1)
        valid[ch] = s.where(~bad)

    if b:
        both = valid[a].notna() & valid[b].notna()
        disagree = flag_channel_disagreement(valid[a], valid[b], cfg.channel_abs_tol,
                                             cfg.channel_rel_tol) & both
        flags["channel_disagreement"] = disagree
        combined = pd.concat([valid[a], valid[b]], axis=1).mean(axis=1, skipna=True)
        combined = combined.where(~disagree)
    else:
        combined = valid[a]

    if rh and rh in df:
        flags["high_rh"] = flag_high_rh(df[rh], cfg.max_rh)
        if cfg.drop_high_rh:
            combined = combined.where(~flags["high_rh"])

    out = df.copy()
    out["pm25_sensor"] = combined

    n = len(df)
    summary = pd.DataFrame(
        {"flagged_hours": flags.sum(), "percent": (flags.sum() / n * 100).round(2)}
    )
    summary.loc["usable_sensor_hours"] = [int(combined.notna().sum()),
                                          round(combined.notna().mean() * 100, 2)]
    return QAResult(data=out, flags=flags, summary=summary)


def to_hourly(
    df: pd.DataFrame, time: str = "time", min_coverage: float = 0.75, expected_per_hour: int | None = None
) -> pd.DataFrame:
    """Average sub-hourly records to hourly means, keeping only hours with at
    least min_coverage of the expected records (default 75 %).

    expected_per_hour is inferred from the median sampling interval when not given.
    """
    d = df.copy()
    d[time] = pd.to_datetime(d[time], utc=True)
    d = d.set_index(time).sort_index()
    if expected_per_hour is None:
        step = d.index.to_series().diff().median()
        expected_per_hour = max(1, int(round(pd.Timedelta("1h") / step))) if pd.notna(step) else 1
    num = d.select_dtypes("number")
    means = num.resample("1h").mean()
    counts = num.resample("1h").count()
    means = means.where(counts >= np.ceil(min_coverage * expected_per_hour))
    return means.reset_index()

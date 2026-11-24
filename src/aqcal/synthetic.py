"""Synthetic co-location data for demos and tests.

The generator mimics a dual-channel optical PM2.5 sensor (channels A and B)
co-located with a reference monitor. It is NOT real data. It exists so the
pipeline can be run end to end, and so the tests know the ground truth.

Built-in behaviour (all parameters are illustrative, not measured):
- reference PM2.5: log-normal background with a diurnal cycle and pollution episodes
- sensor response: over-reads by ~1.7-2x and grows with relative humidity
  (hygroscopic growth), plus random noise per channel
- injected faults: missing gaps, a stuck channel, spikes, and drift on channel B
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def make_colocation(
    days: int = 90,
    seed: int = 42,
    start: str = "2025-01-01",
    inject_faults: bool = True,
) -> pd.DataFrame:
    """Return an hourly DataFrame with columns
    time, pm25_ref, pm25_a, pm25_b, rh, temp.
    """
    rng = np.random.default_rng(seed)
    n = days * 24
    time = pd.date_range(start, periods=n, freq="h", tz="UTC")
    hour = time.hour.to_numpy()
    doy = time.dayofyear.to_numpy()

    # Meteorology
    temp = 8 + 6 * np.sin(2 * np.pi * (hour - 9) / 24) + 4 * np.sin(2 * np.pi * doy / 365) \
        + rng.normal(0, 1.5, n)
    rh = 70 - 20 * np.sin(2 * np.pi * (hour - 9) / 24) + rng.normal(0, 6, n)
    rh = np.clip(rh, 20, 99)

    # Reference PM2.5: background + diurnal + episodes (AR(1) in log space)
    log_bg = np.empty(n)
    log_bg[0] = np.log(8)
    for i in range(1, n):
        log_bg[i] = 0.97 * log_bg[i - 1] + 0.03 * np.log(8) + rng.normal(0, 0.08)
    diurnal = 1 + 0.35 * np.exp(-((hour - 8) ** 2) / 4) + 0.45 * np.exp(-((hour - 20) ** 2) / 6)
    episodes = np.zeros(n)
    for _ in range(max(1, days // 15)):
        c = rng.integers(0, n)
        width = rng.integers(12, 48)
        amp = rng.uniform(15, 45)
        idx = np.arange(n)
        episodes += amp * np.exp(-((idx - c) ** 2) / (2 * width ** 2))
    ref = np.exp(log_bg) * diurnal + episodes
    ref = np.clip(ref + rng.normal(0, 0.8, n), 0.5, None)

    # Sensor response with hygroscopic growth (kappa-Koehler-like shape)
    rh_frac = np.clip(rh / 100, 0, 0.98)
    growth = 1 + 0.25 * rh_frac ** 4 / (1 - rh_frac + 0.05)
    base = 1.8 * ref * growth + 1.0
    a = base * (1 + rng.normal(0, 0.06, n)) + rng.normal(0, 1.0, n)
    b = base * 0.95 * (1 + rng.normal(0, 0.06, n)) + rng.normal(0, 1.0, n)

    df = pd.DataFrame(
        {"time": time, "pm25_ref": ref, "pm25_a": a, "pm25_b": b, "rh": rh, "temp": temp}
    )

    if inject_faults:
        # 1) Missing gap in all sensor channels (power cut)
        g0 = n // 5
        df.loc[g0:g0 + 30, ["pm25_a", "pm25_b"]] = np.nan
        # 2) Channel B stuck at a constant value for 2 days
        s0 = n // 3
        df.loc[s0:s0 + 48, "pm25_b"] = df.loc[s0, "pm25_b"]
        df.attrs["stuck_rows"] = (s0, s0 + 48)
        # 3) Isolated spikes on channel A
        spikes = rng.choice(np.arange(48, n - 48), size=max(3, days // 10), replace=False)
        df.loc[spikes, "pm25_a"] = df.loc[spikes, "pm25_a"] * 8 + 200
        df.attrs["spike_rows"] = sorted(int(i) for i in spikes)
        # 4) Gradual drift on channel B in the last fifth of the record
        d0 = int(n * 0.8)
        drift = np.linspace(1.0, 1.9, n - d0)
        df.loc[d0:, "pm25_b"] = df.loc[d0:, "pm25_b"].to_numpy() * drift
        # 5) Reference gaps (instrument maintenance)
        r0 = n // 2
        df.loc[r0:r0 + 12, "pm25_ref"] = np.nan

    return df

import numpy as np
import pandas as pd

from aqcal.qa import (flag_channel_disagreement, flag_range, flag_spike, flag_stuck, run_qa,
                      to_hourly)
from aqcal.synthetic import make_colocation


def test_stuck_detects_constant_run():
    s = pd.Series([1, 2, 5, 5, 5, 5, 5, 5, 3, 4], dtype=float)
    f = flag_stuck(s, min_run=6)
    assert f.tolist() == [False, False] + [True] * 6 + [False, False]


def test_spike_detects_isolated_outlier_only():
    rng = np.random.default_rng(0)
    s = pd.Series(10 + rng.normal(0, 1, 200))
    s[100] = 300
    f = flag_spike(s)
    assert f[100]
    assert f.sum() == 1


def test_range_and_disagreement():
    assert flag_range(pd.Series([-1.0, 5.0, 2000.0])).tolist() == [True, False, True]
    a = pd.Series([10.0, 10.0, 50.0])
    b = pd.Series([11.0, 2.0, 10.0])
    assert flag_channel_disagreement(a, b).tolist() == [False, True, True]


def test_run_qa_catches_injected_faults():
    df = make_colocation(days=60, seed=1)
    res = run_qa(df)
    s = res.summary["flagged_hours"]
    assert s["pm25_b_stuck"] >= 48          # 2-day stuck channel
    assert s["pm25_a_spike"] >= 3           # injected spikes
    assert s["pm25_a_missing"] >= 30        # power cut
    # Every injected spike is flagged, and none survives in the cleaned series
    spikes = df.attrs["spike_rows"]
    assert res.flags.loc[spikes, "pm25_a_spike"].all()
    clean = res.data.loc[spikes, "pm25_sensor"]
    raw_b = df.loc[spikes, "pm25_b"]
    assert (((clean - raw_b).abs() < 1e-9) | clean.isna()).all()


def test_to_hourly_coverage_rule():
    t = pd.date_range("2025-01-01", periods=120, freq="2min", tz="UTC")  # 4 hours
    v = np.ones(120)
    v[30:60] = np.nan  # hour 2 has 0 % coverage of non-missing values
    v[60:75] = np.nan  # hour 3 has 50 %
    out = to_hourly(pd.DataFrame({"time": t, "x": v}))
    assert out["x"].notna().tolist() == [True, False, False, True]

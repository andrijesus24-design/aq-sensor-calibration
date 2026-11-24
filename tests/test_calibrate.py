import numpy as np
import pandas as pd

from aqcal.calibrate import cross_validate, metrics, prepare
from aqcal.cli import main, pick_best
from aqcal.qa import run_qa
from aqcal.synthetic import make_colocation


def test_metrics_perfect_prediction():
    y = np.array([1.0, 5.0, 10.0, 20.0])
    m = metrics(y, y)
    assert abs(m["r2"] - 1) < 1e-12 and abs(m["slope"] - 1) < 1e-12 and m["rmse"] == 0


def test_calibration_beats_raw_and_recovers_humidity_effect():
    df = make_colocation(days=90, seed=3)
    d = prepare(run_qa(df).data)
    table, preds = cross_validate(d)
    assert table.loc["mlr_rh", "rmse"] < 0.5 * table.loc["raw", "rmse"]
    assert table.loc["mlr_rh", "rmse"] < table.loc["linear", "rmse"]
    assert preds[["linear", "mlr_rh"]].notna().all().all()


def test_cv_folds_are_whole_weeks():
    # A model trained on one week only must still predict all hours once
    df = make_colocation(days=21, seed=5, inject_faults=False)
    d = prepare(run_qa(df).data)
    table, preds = cross_validate(d, models=["linear"], n_splits=3)
    assert preds["linear"].notna().all()


def test_cli_demo_writes_report(tmp_path):
    assert main(["demo", "--out", str(tmp_path), "--days", "30"]) == 0
    assert (tmp_path / "report.md").exists()
    assert (tmp_path / "figures" / "scatter.png").exists()


def test_cli_run_on_csv(tmp_path):
    df = make_colocation(days=30, seed=7).rename(
        columns={"time": "datetime", "pm25_ref": "ref_ugm3", "pm25_a": "pa_cf1_a",
                 "pm25_b": "pa_cf1_b", "rh": "humidity", "temp": "temperature"})
    f = tmp_path / "in.csv"
    df.to_csv(f, index=False)
    rc = main(["run", "--input", str(f), "--time", "datetime", "--ref", "ref_ugm3",
               "--a", "pa_cf1_a", "--b", "pa_cf1_b", "--rh", "humidity",
               "--temp", "temperature", "--out", str(tmp_path / "out")])
    assert rc == 0 and (tmp_path / "out" / "model_metrics.csv").exists()


def test_pick_best_prefers_simple_model_when_close():
    t = pd.DataFrame({"rmse": [10.0, 3.0, 3.1, 2.98]}, index=["raw", "linear", "mlr_rh", "rf"])
    assert pick_best(t) == "linear"

"""Calibration models and time-blocked validation against a reference monitor.

Models compared:
- raw          : sensor reading as-is (no correction)
- linear       : ref = a + b * sensor
- mlr_rh       : ref = a + b * sensor + c * RH
- mlr_rh_temp  : ref = a + b * sensor + c * RH + d * T
- hygro        : ref = a + b * sensor + c * sensor * h / (1 - h), h = RH/100.
                 The interaction term follows the shape of kappa-Koehler
                 hygroscopic growth, so humidity scales the error instead of
                 shifting it. Physically motivated and still auditable.
- epa_us       : fixed US-wide PurpleAir correction (Barkjohn et al., 2021),
                 PM2.5 = 0.524 * PA_cf1 - 0.0862 * RH + 5.75. Not fitted.
                 Only meaningful for PurpleAir cf_1 data in its validated range.
- rf           : random forest on sensor, RH and T (non-linear benchmark)

Validation is time-blocked (folds are whole weeks), because random
train/test splits of autocorrelated hourly data overstate performance.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import GroupKFold

# Reference target values for PM2.5 sensors from US EPA (2021),
# "Performance Testing Protocols, Metrics, and Target Values for Fine
# Particulate Matter Air Sensors" (EPA/600/R-20/280). Check the document
# before quoting these to a client.
EPA_TARGETS = {
    "r2_min": 0.70,
    "slope_range": (0.65, 1.35),
    "intercept_range": (-5.0, 5.0),
    "rmse_max": 7.0,
    "nrmse_max_pct": 30.0,
}

FEATURES = {
    "linear": ["sensor"],
    "mlr_rh": ["sensor", "rh"],
    "mlr_rh_temp": ["sensor", "rh", "temp"],
    "hygro": ["sensor", "sensor_hyg"],
    "rf": ["sensor", "rh", "temp"],
}


def metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    y_true = np.asarray(y_true, float)
    y_pred = np.asarray(y_pred, float)
    m = np.isfinite(y_true) & np.isfinite(y_pred)
    y_true, y_pred = y_true[m], y_pred[m]
    n = len(y_true)
    if n < 3:
        return {"n": n}
    resid = y_pred - y_true
    rmse = float(np.sqrt(np.mean(resid ** 2)))
    # OLS of prediction on reference (EPA convention: sensor = slope * ref + b)
    slope, intercept = np.polyfit(y_true, y_pred, 1)
    r = np.corrcoef(y_true, y_pred)[0, 1]
    return {
        "n": n,
        "r2": float(r ** 2),
        "slope": float(slope),
        "intercept": float(intercept),
        "rmse": rmse,
        "nrmse_pct": float(rmse / np.mean(y_true) * 100),
        "mae": float(np.mean(np.abs(resid))),
        "mean_bias": float(np.mean(resid)),
    }


def meets_targets(m: dict, t: dict = EPA_TARGETS) -> dict:
    if "r2" not in m:
        return {}
    return {
        "r2_ok": m["r2"] >= t["r2_min"],
        "slope_ok": t["slope_range"][0] <= m["slope"] <= t["slope_range"][1],
        "intercept_ok": t["intercept_range"][0] <= m["intercept"] <= t["intercept_range"][1],
        "error_ok": (m["rmse"] <= t["rmse_max"]) or (m["nrmse_pct"] <= t["nrmse_max_pct"]),
    }


def _make_model(name: str, seed: int):
    if name == "rf":
        return RandomForestRegressor(n_estimators=300, min_samples_leaf=5, random_state=seed, n_jobs=-1)
    return LinearRegression()


def prepare(df: pd.DataFrame, sensor="pm25_sensor", ref="pm25_ref", rh="rh", temp="temp",
            time="time") -> pd.DataFrame:
    cols = {sensor: "sensor", ref: "ref", time: "time"}
    if rh and rh in df:
        cols[rh] = "rh"
    if temp and temp in df:
        cols[temp] = "temp"
    d = df[list(cols)].rename(columns=cols).copy()
    d["time"] = pd.to_datetime(d["time"], utc=True)
    if "rh" in d:
        h = (d["rh"] / 100).clip(0, 0.97)
        d["sensor_hyg"] = d["sensor"] * h / (1 - h)
    return d.dropna().reset_index(drop=True)


def cross_validate(d: pd.DataFrame, models=None, n_splits: int = 5, seed: int = 0):
    """Time-blocked K-fold CV (groups = ISO weeks).

    Returns (metrics_table, predictions) where predictions holds the
    out-of-fold prediction of every model for every hour.
    """
    available = set(d.columns)
    if models is None:
        models = ["raw", "linear", "mlr_rh", "mlr_rh_temp", "hygro", "epa_us", "rf"]
    models = [m for m in models
              if m in ("raw", "epa_us") or set(FEATURES[m]) <= available]
    if "epa_us" in models and "rh" not in available:
        models.remove("epa_us")

    weeks = d["time"].dt.tz_convert(None).dt.to_period("W").astype(str)
    n_groups = weeks.nunique()
    splits = min(n_splits, n_groups)
    if splits < 2:
        raise ValueError("Need at least two weeks of co-located data for blocked CV.")
    gkf = GroupKFold(n_splits=splits)

    preds = pd.DataFrame({"time": d["time"], "ref": d["ref"]})
    for name in models:
        if name == "raw":
            preds[name] = d["sensor"].to_numpy()
            continue
        if name == "epa_us":
            preds[name] = 0.524 * d["sensor"] - 0.0862 * d["rh"] + 5.75
            continue
        out = np.full(len(d), np.nan)
        X = d[FEATURES[name]].to_numpy()
        y = d["ref"].to_numpy()
        for tr, te in gkf.split(X, y, groups=weeks):
            mdl = _make_model(name, seed).fit(X[tr], y[tr])
            out[te] = mdl.predict(X[te])
        preds[name] = out

    rows = []
    for name in models:
        m = metrics(preds["ref"], preds[name])
        m.update(meets_targets(m))
        m["model"] = name
        rows.append(m)
    table = pd.DataFrame(rows).set_index("model")
    return table, preds


def fit_final(d: pd.DataFrame, name: str, seed: int = 0):
    """Fit the chosen model on all co-location data (for deployment)."""
    if name in ("raw", "epa_us"):
        return None
    mdl = _make_model(name, seed).fit(d[FEATURES[name]].to_numpy(), d["ref"].to_numpy())
    return mdl


def describe_linear(mdl, name: str) -> str:
    if not isinstance(mdl, LinearRegression):
        return ""
    terms = " ".join(f"{c:+.4f}*{f}" for c, f in zip(mdl.coef_, FEATURES[name]))
    return f"ref = {mdl.intercept_:.3f} {terms}"

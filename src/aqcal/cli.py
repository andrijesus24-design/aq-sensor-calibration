"""Command line entry point.

    aqcal demo --out results/demo
    aqcal run --input data.csv --time time --ref pm25_ref --a pm25_a --b pm25_b \
              --rh rh --temp temp --out results/site1
"""

from __future__ import annotations

import argparse
import sys

import pandas as pd

from .calibrate import cross_validate, describe_linear, fit_final, prepare
from .qa import QAConfig, run_qa, to_hourly
from .report import write_report
from .synthetic import make_colocation


def pick_best(table: pd.DataFrame) -> str:
    """Lowest out-of-fold RMSE among fitted models; prefer a linear model when
    it is within 5 % of the best (simpler, easier to audit and explain)."""
    fitted = table.drop(index=[i for i in ("raw",) if i in table.index])
    best = fitted["rmse"].idxmin()
    linear = [m for m in ("linear", "mlr_rh", "hygro", "mlr_rh_temp") if m in fitted.index]
    for m in linear:
        if fitted.loc[m, "rmse"] <= fitted.loc[best, "rmse"] * 1.05:
            return m
    return best


def _pipeline(df, a, b, rh, temp, out, title, note, hourly):
    if hourly:
        df = to_hourly(df, time="time")
    qa = run_qa(df, a=a, b=b, rh=rh, cfg=QAConfig())
    d = prepare(qa.data, rh=rh, temp=temp)
    table, preds = cross_validate(d)
    best = pick_best(table)
    eq = describe_linear(fit_final(d, best), best)
    path = write_report(out, qa, d, table, preds, best, eq, a, b, title, note)
    print(table.round(3).to_string())
    print(f"\nBest model: {best}\nReport: {path}")
    return path


def main(argv=None):
    p = argparse.ArgumentParser(prog="aqcal", description="Low-cost PM2.5 sensor QA and calibration")
    sub = p.add_subparsers(dest="cmd", required=True)

    pd_ = sub.add_parser("demo", help="Run on synthetic data")
    pd_.add_argument("--out", default="results/demo")
    pd_.add_argument("--days", type=int, default=90)

    pr = sub.add_parser("run", help="Run on your own co-location CSV")
    pr.add_argument("--input", required=True)
    pr.add_argument("--time", default="time")
    pr.add_argument("--ref", required=True, help="Reference PM2.5 column")
    pr.add_argument("--a", required=True, help="Sensor channel A column")
    pr.add_argument("--b", default=None, help="Sensor channel B column (optional)")
    pr.add_argument("--rh", default=None, help="Relative humidity column (optional)")
    pr.add_argument("--temp", default=None, help="Temperature column (optional)")
    pr.add_argument("--hourly", action="store_true", help="Average sub-hourly data to hourly first")
    pr.add_argument("--out", default="results/run")
    pr.add_argument("--title", default="PM2.5 sensor QA and calibration report")
    pr.add_argument("--note", default="")

    args = p.parse_args(argv)
    if args.cmd == "demo":
        df = make_colocation(days=args.days)
        note = ("> **Synthetic data.** This demo uses simulated data with known, injected faults "
                "(gaps, a stuck channel, spikes, drift). It shows the method, not a real site.")
        _pipeline(df, "pm25_a", "pm25_b", "rh", "temp", args.out,
                  "Demo: PM2.5 sensor QA and calibration", note, hourly=False)
        return 0

    raw = pd.read_csv(args.input)
    rename = {args.time: "time", args.ref: "pm25_ref"}
    df = raw.rename(columns=rename)
    _pipeline(df, args.a, args.b, args.rh, args.temp, args.out, args.title, args.note, args.hourly)
    return 0


if __name__ == "__main__":
    sys.exit(main())

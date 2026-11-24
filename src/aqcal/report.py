"""Figures and a Markdown report for a co-location / calibration run."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from .calibrate import EPA_TARGETS  # noqa: E402

LABELS = {
    "raw": "Raw sensor",
    "linear": "Linear",
    "mlr_rh": "Linear + RH",
    "mlr_rh_temp": "Linear + RH + T",
    "hygro": "Hygroscopic growth model",
    "epa_us": "US EPA fixed correction",
    "rf": "Random forest",
}


def _fig_timeseries(qa_data, a, b, out):
    fig, ax = plt.subplots(figsize=(11, 3.6))
    t = pd.to_datetime(qa_data["time"])
    ax.plot(t, qa_data[a], lw=0.6, alpha=0.6, label="Channel A (raw)")
    if b:
        ax.plot(t, qa_data[b], lw=0.6, alpha=0.6, label="Channel B (raw)")
    ax.plot(t, qa_data["pm25_ref"], lw=0.9, color="black", label="Reference")
    ax.set_ylabel("PM2.5 (µg/m³)")
    ax.set_ylim(0, max(1.0, qa_data["pm25_ref"].quantile(0.999) * 3))
    ax.legend(loc="upper right", ncol=3, fontsize=8)
    ax.set_title("Raw sensor channels vs reference")
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def _fig_scatter(preds, best, out):
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.2), sharey=True)
    lim = max(preds["ref"].max(), preds["raw"].max()) * 1.05
    for ax, name in zip(axes, ["raw", best]):
        ax.scatter(preds["ref"], preds[name], s=3, alpha=0.35)
        ax.plot([0, lim], [0, lim], color="black", lw=0.8)
        ax.set_xlim(0, lim)
        ax.set_ylim(0, lim)
        ax.set_xlabel("Reference PM2.5 (µg/m³)")
        ax.set_title(LABELS.get(name, name) + (" (out-of-fold)" if name != "raw" else ""))
    axes[0].set_ylabel("Sensor PM2.5 (µg/m³)")
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def _fig_residual_rh(d, preds, best, out):
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(d["rh"], preds["raw"] - preds["ref"], s=3, alpha=0.3, label="Raw")
    ax.scatter(d["rh"], preds[best] - preds["ref"], s=3, alpha=0.3, label=LABELS.get(best, best))
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xlabel("Relative humidity (%)")
    ax.set_ylabel("Sensor − reference (µg/m³)")
    ax.legend(fontsize=8)
    ax.set_title("Error vs humidity")
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def _fig_drift(qa_data, a, b, out):
    """7-day rolling median of the A/B ratio: a drifting channel shows up here."""
    d = qa_data.set_index(pd.to_datetime(qa_data["time"]))
    ratio = (d[a] / d[b]).where((d[a] > 1) & (d[b] > 1))
    roll = ratio.rolling("7D", min_periods=48).median()
    fig, ax = plt.subplots(figsize=(11, 3))
    ax.plot(roll.index, roll, lw=1)
    ax.axhline(1, color="black", lw=0.6, ls="--")
    ax.set_ylabel("A / B (7-day median)")
    ax.set_title("Channel agreement over time (drift check)")
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def _fmt_table(table: pd.DataFrame) -> str:
    cols = ["n", "r2", "slope", "intercept", "rmse", "nrmse_pct", "mae", "mean_bias",
            "r2_ok", "slope_ok", "intercept_ok", "error_ok"]
    cols = [c for c in cols if c in table.columns]
    head = "| Model | " + " | ".join(cols) + " |"
    sep = "|---" * (len(cols) + 1) + "|"
    lines = [head, sep]
    for name, row in table[cols].iterrows():
        vals = []
        for c in cols:
            v = row[c]
            if isinstance(v, (bool,)) or str(v) in ("True", "False"):
                vals.append("✅" if bool(v) else "❌")
            elif c == "n":
                vals.append(f"{int(v)}")
            else:
                vals.append(f"{v:.2f}")
        lines.append(f"| {LABELS.get(name, name)} | " + " | ".join(vals) + " |")
    return "\n".join(lines)


def write_report(out_dir, qa, d, table, preds, best, equation, a, b, title, data_note):
    out = Path(out_dir)
    fig_dir = out / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    _fig_timeseries(qa.data, a, b, fig_dir / "timeseries.png")
    _fig_scatter(preds, best, fig_dir / "scatter.png")
    has_rh = "rh" in d
    if has_rh:
        _fig_residual_rh(d, preds, best, fig_dir / "error_vs_rh.png")
    if b:
        _fig_drift(qa.data, a, b, fig_dir / "drift.png")

    qa_rows = "\n".join(
        f"| {idx} | {int(r.flagged_hours)} | {r.percent:.1f} % |" for idx, r in qa.summary.iterrows()
    )
    raw = table.loc["raw"]
    bm = table.loc[best]
    t = EPA_TARGETS
    md = f"""# {title}

{data_note}

## Summary

- Co-located hours used for calibration: **{int(bm['n'])}**
- Raw sensor vs reference: R² {raw['r2']:.2f}, slope {raw['slope']:.2f}, RMSE {raw['rmse']:.1f} µg/m³
- Best model (**{LABELS.get(best, best)}**, out-of-fold): R² {bm['r2']:.2f}, slope {bm['slope']:.2f}, RMSE {bm['rmse']:.1f} µg/m³
- Error reduced by **{(1 - bm['rmse'] / raw['rmse']) * 100:.0f} %** (RMSE)
{('- Fitted equation: `' + equation + '`') if equation else ''}

## 1. Data quality checks

Each channel is checked for missing values, out-of-range values, stuck output
and spikes; hours where both channels survive but disagree are removed.

| Check | Hours flagged | Share |
|---|---|---|
{qa_rows}

![Raw channels vs reference](figures/timeseries.png)
{'''
![Channel drift check](figures/drift.png)

A ratio that moves away from 1 over time means one channel is drifting and
needs attention before its data are trusted.
''' if b else ''}
## 2. Calibration models (time-blocked cross-validation)

Folds are whole weeks, so every score is measured on weeks the model never saw.
Targets (✅/❌) are the US EPA (2021) PM2.5 sensor targets: R² ≥ {t['r2_min']},
slope {t['slope_range'][0]}–{t['slope_range'][1]}, intercept {t['intercept_range'][0]} to
+{t['intercept_range'][1]} µg/m³, RMSE ≤ {t['rmse_max']} µg/m³ or NRMSE ≤ {t['nrmse_max_pct']} %.

{_fmt_table(table)}

![Raw vs calibrated](figures/scatter.png)
{'![Error vs humidity](figures/error_vs_rh.png)' if has_rh else ''}

## 3. Limitations

- A calibration is only valid for conditions seen during co-location
  (season, concentration range, humidity, aerosol type). Re-check periodically.
- The US EPA fixed correction was derived for PurpleAir sensors (cf_1 channel);
  it is shown as a benchmark, not a recommendation for other sensors.
- Meeting the EPA targets at one site does not make a sensor a regulatory
  (reference-equivalent) instrument.
"""
    (out / "report.md").write_text(md, encoding="utf-8")
    table.to_csv(out / "model_metrics.csv")
    qa.summary.to_csv(out / "qa_summary.csv")
    preds.to_csv(out / "out_of_fold_predictions.csv", index=False)
    return out / "report.md"

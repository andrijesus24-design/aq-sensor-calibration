# aqcal — QA and calibration of low-cost PM2.5 sensors

A small, reproducible Python pipeline that takes a low-cost PM2.5 sensor
co-located with a reference monitor and produces:

1. **Data quality checks** per channel: missing data, out-of-range values,
   stuck output, spikes (Hampel filter), dual-channel disagreement and very
   high humidity.
2. **Calibration models** compared with **time-blocked cross-validation**
   (folds are whole weeks, so scores are measured on weeks the model never saw):
   raw, linear, linear + RH, linear + RH + temperature, a **hygroscopic-growth
   model** (humidity scales the error, following the shape of κ-Köhler growth),
   the US EPA fixed PurpleAir correction as a benchmark, and a random forest.
3. **A report** (Markdown + figures + CSV) that scores every model against the
   US EPA (2021) performance targets for PM2.5 sensors, and a **drift check**
   on the two sensor channels.

👉 See the example report: [`examples/demo_report/report.md`](examples/demo_report/report.md)
(synthetic data with known, injected faults).

## Quick start

```bash
git clone <this repo>
cd aq-sensor-calibration
python -m venv .venv && source .venv/bin/activate
pip install -e ".[test]"

pytest                      # 11 tests
aqcal demo --out results/demo
```

## Run on your own data

Any CSV with one row per timestamp works. Tell the tool which column is which:

```bash
aqcal run --input colocation.csv \
  --time datetime --ref ref_pm25 \
  --a pm25_cf1_a --b pm25_cf1_b \
  --rh humidity --temp temperature \
  --hourly \
  --out results/site1 --title "Site 1 co-location"
```

`--b`, `--rh` and `--temp` are optional; models that need a missing column are
skipped. `--hourly` averages sub-hourly data to hourly means and keeps only hours
with at least 75 % of the expected records.

A suitable public dataset to try: US EPA, *Collocated PurpleAir sensors and T640
reference data located at Durango Complex in Phoenix*
([catalog.data.gov](https://catalog.data.gov/dataset/collocated-purpleair-sensors-and-t640-reference-data-located-at-durango-complex-in-phoenix)).
Check its column names and units before running.

## Method notes

- **Why blocked CV.** Hourly air-quality data are strongly autocorrelated. A
  random train/test split puts neighbouring hours in both sets and makes any
  model look better than it will be in the field.
- **Model choice.** The tool picks the lowest out-of-fold RMSE, but prefers a
  linear or physically motivated model when it is within 5 % of the best: it is
  easier to audit, explain to a client and transfer to another site.
- **Thresholds.** QA thresholds are parameters (`aqcal.qa.QAConfig`). They depend
  on the sensor, the site and the client's QA plan and should be agreed per project.
  The spike filter can also flag genuine humidity-driven peaks; review the flags
  rather than deleting data blindly.
- **EPA targets** used for the ✅/❌ columns: R² ≥ 0.70, slope 1 ± 0.35,
  intercept between −5 and +5 µg/m³, RMSE ≤ 7 µg/m³ or NRMSE ≤ 30 %
  (US EPA, 2021, *Performance Testing Protocols, Metrics, and Target Values for
  Fine Particulate Matter Air Sensors*, EPA/600/R-20/280).
- **EPA fixed correction** (Barkjohn et al., 2021): `0.524 × PA_cf1 − 0.0862 × RH + 5.75`.
  Derived for PurpleAir cf_1 data in the US; shown only as a benchmark.

## Limitations

- A calibration holds only for the conditions seen during co-location
  (season, concentration range, humidity, aerosol type).
- Passing the EPA targets at one site does not make a sensor a reference or
  equivalent method.
- The demo data are simulated. Results on real data will differ.

## Project layout

```
src/aqcal/qa.py          quality checks and hourly averaging
src/aqcal/calibrate.py   models, blocked cross-validation, metrics, EPA targets
src/aqcal/report.py      figures and Markdown report
src/aqcal/synthetic.py   simulated co-location data with injected faults
src/aqcal/cli.py         `aqcal demo` and `aqcal run`
tests/                   pytest suite
```

## Author

Maintained by **Andri Binet, PhD (c)**, environmental scientist (aerosol physics and
chemistry), with lab experience in environmental microbiology and
bioinformatics. Sensor-network QA, calibration and monthly data reports are
available as a service: **modbinet@gmail.com**.

License: MIT.

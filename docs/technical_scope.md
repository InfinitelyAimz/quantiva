# Quantiva technical scope and verification contract

Quantiva is a reproducible analysis of one retailer's historical transactions, not
a live sales feed or a deployed business intelligence service. The Streamlit dashboard
explores prepared, verified artifacts; it does not retrieve current trading activity.

## Dataset and processing boundaries

The source is UCI Online Retail, Chen (2015), DOI 10.24432/C5BW33, CC BY 4.0:
541,909 original lines from 1 December 2010 to 9 December 2011. Preserve source bytes,
their checksum and provenance. The documented cleaning policy yields 536,639 ledger
lines and 524,878 eligible completed-sales lines. Record duplicate exclusions,
negative-price quarantines, transaction types and missingness separately.

SQLite is rebuilt from verified ledger artifacts with foreign-key and integrity
checks. Fourteen packaged SQL analyses reconcile against independent pandas results.
Gross sales include anonymous eligible purchases and charges/postage. They do not
represent profit, settled payments or accounting net revenue. Customer analysis
uses identifiable purchasers and the documented RFM reference date and scoring.

## Measured reference results

These are fixed historical measurements under the eligibility policy, not forecasts
of current retail activity or claims of commercial impact.

| Metric | Verified result |
| --- | ---: |
| Gross eligible completed-sales revenue | £10,642,110.80 |
| Completed orders | 19,960 |
| Average order value | £533.17 |
| Units sold | 5,572,420 |
| Identifiable purchasers | 4,338 |
| Within-period repeat purchasers | 2,845 |
| Within-period repeat rate | 65.58% |

## Forecasting and evaluation boundaries

Preserve chronological training, validation and held-out test windows. Features use
available history only, seven-day predictions are recursive, and model selection
uses validation results before the test is evaluated. Compare naive, weekly seasonal
naive, Linear Regression and Random Forest. Preserve the frozen selected model and
recorded parameters; the held-out result is not a new model-selection opportunity.

| Model | Validation MAE (GBP/day) | Held-out MAE (GBP/day) |
| --- | ---: | ---: |
| Naive | 24,181.77 | 20,978.67 |
| Weekly Seasonal Naive | 15,580.52 | 11,250.17 |
| Linear Regression | 12,792.97 | Not evaluated |
| Random Forest | 11,431.53 | 12,344.71 |

Random Forest wins validation; Weekly Seasonal Naive performs better on the held-out
test. Do not claim general machine learning superiority. Saved-model inference for
9–15 December 2011 is a historical demonstration from the 8 December cutoff. Missing
recorded sales do not establish zero demand. Prediction intervals are not calibrated.
Historical manual tuning is documented, not independently reconstructed.

## Dashboard boundaries

Overview, Sales Analytics, Customer Intelligence, Predictive Analytics and Data Quality
use the same verified analytical artifacts. Date/country filters scope the first three
pages; forecasting and quality evidence retain their stated full-data scope. Preserve
dark/light presentation and session-wide GBP/ZAR selection. GBP is authoritative for
source values, SQL, RFM scoring, forecasts, evaluation and stored artifacts.

ZAR is an illustrative display conversion at the fixed 8 December 2011 ECB cross-rate,
1 GBP = 12.708021 ZAR. It is not actual historical ZAR transaction revenue or a live
exchange-rate feed. Convert monetary presentation and exports consistently.

## Reproduction and integrity requirements

Use Python 3.11 and the committed [dependency lock](../requirements-lock.txt).
Follow [installation and reproduction](reproducibility.md) for official-source
download, deterministic preparation, SQLite rebuild, analytics, training, artifact
loading and historical inference. Source data, databases, environments and binary
models remain excluded from Git and must be regenerated or independently verified.

Run the complete 105-test suite with warnings as errors, Ruff lint/format and dependency
checks. Full-data checks must pass seven lineage conditions, all 3,982 SQL comparisons,
all 30 forecasting conditions and all 63 dashboard conditions. Portfolio checks require
this public scope document, verify measured headline facts and model comparisons,
validate documentation/CLI references and check the six published dashboard screenshots.
They also reject internal instruction files and private preparation files.

```powershell
.\.venv\Scripts\python.exe -m pytest -W error
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/verify_data.py
.\.venv\Scripts\python.exe scripts/verify_analytics.py
.\.venv\Scripts\python.exe scripts/verify_forecasting.py
.\.venv\Scripts\python.exe scripts/verify_dashboard.py
.\.venv\Scripts\python.exe scripts/verify_portfolio.py
```

CI checks fixtures, style and public documentation without downloading the workbook.
It does not replace full-data reconciliation or browser inspection. Report uncertainties,
partial calendar coverage, anonymous purchases and baseline failures explicitly.

## Public technical documentation

- [Architecture](architecture.md): actual modules, storage and service boundaries.
- [Reproduction](reproducibility.md): installation, commands and artifact recovery.
- [Methodology index](methodology.md): eligibility, SQL, statistics, RFM and forecasting.
- [Case study](../reports/portfolio_case_study.md): measured findings and limitations.
- [KPI definitions](../reports/kpi_specification.md): analytical meanings and exclusions.
- [Model evaluation](../reports/model_evaluation.md): splits, baselines and qualifications.
- [Dashboard gallery](dashboard_gallery.md): six actual historical-data application views.

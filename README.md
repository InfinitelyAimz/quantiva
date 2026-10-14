# Quantiva — Retail Intelligence & Predictive Analytics

This snapshot uses a fixed historical retail dataset, not a live sales feed.
Analytics and forecast outputs describe their documented historical windows.

Quantiva is a local, reproducible retail data science project using real UCI Online
Retail transactions. It examines sales, products, customers, geography, and the
quality of the observations underlying business decisions.

Verified ingestion, SQL analytics and chronological seven-day forecasting are implemented in this snapshot. The dashboard is outside this milestone.
See [data methodology](reports/methodology.md) and the technical evidence linked below.

## Actual results

| Metric | Result |
| --- | ---: |
| Gross completed-sales revenue | £10,642,110.80 |
| Completed orders (distinct eligible invoices) | 19,960 |
| Average order value | £533.17 |
| Eligible source units sold | 5,572,420 |
| Identifiable purchasers | 4,338 |
| Within-period repeat purchase rate | 65.58% |

Sales include anonymous purchases and eligible service/charge codes. These are
observed gross transaction amounts, not profit or accounting net revenue. See
[KPI definitions](reports/kpi_specification.md) and [findings](reports/findings.md).

![Monthly revenue with partial coverage marked](reports/figures/monthly_revenue.png)

November 2011 has the largest complete-month revenue. December 2011 ends on
9 December and is not compared with full months. Mean order value exceeds the
£303.30 median because of a long right tail. All major charts have interpretations.

## Architecture

```text
Official UCI ZIP → immutable raw XLSX → inspect → auditable Phase 1 cleaning
                                                       ↓
                                  Parquet ledger + exclusions + checksums
                                                       ↓
                                  atomic SQLite rebuild (SQLAlchemy)
                                                       ↓
                       packaged SQL ⇄ independent pandas reconciliation
                                                       ↓
                        executable notebooks → figures + measured reports
```

`src/quantiva` contains reusable logic. Tables represent transaction lines,
invoices, products, customers, and countries. Each line retains its Excel row,
timestamp, description, nullable customer, and classification. Invoices are counted
distinctly; stock codes identify products while names are labels. Foreign keys,
monetary/eligibility constraints, and six indexes support integrity and efficient
queries. Currency is stored in integer £0.0001 units before aggregation. See
[Phase 2 methodology](reports/phase_2_methodology.md) for the schema and decisions.

Stack: Python 3.11, pandas/NumPy, requests, openpyxl, PyArrow, SQLite/SQLAlchemy,
Matplotlib, Plotly, scikit-learn, SciPy, joblib, nbformat/nbclient/ipykernel,
pytest, and Ruff. All functionality
runs locally without credentials, paid APIs, or cloud services. Descriptive
statistics use pandas; no gratuitous significance tests or clustering are added.

## Install — Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
```

No activation or execution-policy changes are needed. On macOS/Linux use Python
3.11 and `.venv/bin/python` / `.venv/bin/quantiva`. The lock pins the tested Windows
Python 3.11 environment. Use this source checkout for notebooks/reports; SQL files
are included as package resources.

## Download, inspect, clean, and rebuild

```powershell
.\.venv\Scripts\quantiva.exe download
.\.venv\Scripts\quantiva.exe inspect
.\.venv\Scripts\quantiva.exe prepare
.\.venv\Scripts\python.exe scripts/verify_data.py
.\.venv\Scripts\quantiva.exe database
```

Download uses the [official UCI archive](https://archive.ics.uci.edu/static/public/352/online+retail.zip),
records source/checksum provenance, and preserves existing raw workbooks. If it
fails, visit the [dataset page](https://archive.ics.uci.edu/dataset/352/online+retail),
download/extract `Online Retail.xlsx` to `data/raw/Online Retail.xlsx`, then inspect
and prepare. Never substitute generated business records.

`prepare` replaces derived Parquet/audit outputs. `database` verifies the manifest
and raw hash, builds a temporary sibling database, validates it, then atomically
replaces `data/processed/quantiva.db`. Failed rebuilds preserve the previous
database. Close consumers on Windows before rebuilding. Do not run concurrent
preparation/rebuild commands. Set `$env:QUANTIVA_DATA_DIR = '.\data'` to relocate
data; configuration is centralized. `.env` is not loaded automatically.

Raw workbooks, Parquet, databases, environments, and generated Plotly HTML are
ignored by Git. Small report tables, PNG figures, and executed notebooks are tracked.

## Execute SQL

```powershell
.\.venv\Scripts\quantiva.exe query
.\.venv\Scripts\quantiva.exe query kpis
.\.venv\Scripts\quantiva.exe query monthly_growth
.\.venv\Scripts\quantiva.exe query top_products
.\.venv\Scripts\quantiva.exe query customer_frequency
```

The 14 files under `src/quantiva/sql` cover daily/monthly revenue, country contribution,
product revenue/units rankings, invoice values/AOV, customer frequency/spending,
repeat purchasing, monthly growth, running revenue, and signed adjustments. They
show INNER/LEFT JOIN, GROUP BY, HAVING, CTEs, window functions, ranking, running
totals, and percentage contributions.

```sql
SELECT invoice_no, SUM(revenue_units) / 10000.0 AS order_value_gbp
FROM completed_sales
GROUP BY invoice_no;
```

```python
from quantiva.config import Settings
from quantiva.reconciliation import run_query

orders = run_query(Settings.from_environment().database_file, "order_values")
```

## Analyze and reconcile

```powershell
.\.venv\Scripts\quantiva.exe analyze
.\.venv\Scripts\python.exe scripts/verify_analytics.py
```

`analyze` executes every query, independently calculates pandas KPIs from Parquet,
and refuses publication if reconciliation fails or provenance is stale. It produces
findings, JSON metrics, duplicate sensitivity, monthly totals, eight PNG charts,
and `reports/figures/daily_revenue.html`. The interactive HTML embeds Plotly locally
and requires no CDN. Generated reports overwrite prior derived reports.

[Reconciliation](reports/reconciliation.csv) records SQL/pandas values, absolute and
relative differences, and pass/fail for 3,982 comparisons. Counts match exactly;
monetary tolerance is absolute £0.000001 with no relative tolerance. Every monthly,
country, and selling-product revenue key is compared, and absent keys fail even at
zero revenue. SQL sums stored fixed-point values; pandas separately sums the original
cleaned float amounts.

## Execute notebooks

```powershell
.\.venv\Scripts\python.exe scripts/execute_notebooks.py
```

The runner clears outputs, starts an isolated kernel using the exact calling Python,
validates execution, and saves successful results. No global kernel is registered.

- [Exploration](notebooks/01_data_exploration.ipynb): revenue, products, customers,
  geography, calendar coverage, adjustments, and duplicate sensitivity.
- [Statistics](notebooks/02_statistical_analysis.ipynb): mean, median, variance/std,
  quartiles, percentiles, IQR, skewness, outlier influence, and correlations.
- [Forecasting](notebooks/03_forecasting_experiments.ipynb): calendar policy,
  leakage checks, recursive forecasts, chronological validation, held-out errors,
  sensitivities, and trusted artifact inference. Run `forecast-train` first;
  `scripts/execute_notebooks.py --phase 3` executes only this notebook.

Open them in a notebook-capable editor using `.venv` as the kernel, or execute with
the command above. Prepare/import actual data first.

## Seven-day forecasting

After preparing the ledger and database, run:

```powershell
.\.venv\Scripts\quantiva.exe forecast-prepare
.\.venv\Scripts\quantiva.exe forecast-train
.\.venv\Scripts\quantiva.exe forecast-compare
.\.venv\Scripts\quantiva.exe forecast
.\.venv\Scripts\quantiva.exe forecast-verify
.\.venv\Scripts\python.exe scripts/verify_forecasting.py
.\.venv\Scripts\python.exe scripts/execute_notebooks.py --phase 3
```

The unchanged gross-sales target includes eligible charges. Missing dates mean zero
observed revenue; they do not prove zero demand. Both source boundary dates are
excluded, leaving 2 December 2010–8 December 2011. Each origin forecasts seven
calendar days recursively, using earlier predictions for unavailable future lags.
Eight expanding validation origins select the model by MAE before opening a separate
56-day test period. Test weights remain fixed while observed context advances between
weekly origins. Full-history deployment refitting occurs only after evaluation.

| Model | Validation MAE (GBP/day) | Test MAE (GBP/day) | Test WAPE |
| --- | ---: | ---: | ---: |
| Naive | 24,181.77 | 20,978.67 | 45.33% |
| Weekly seasonal naive | 15,580.52 | 11,250.17 | 24.31% |
| Linear Regression | 12,792.97 | Not evaluated | Not evaluated |
| Random Forest | 11,431.53 | 12,344.71 | 26.68% |

Random Forest is the validation-selected candidate. The weekly baseline is better
on the held-out test; these results do not support general machine learning superiority.
The selection remains frozen. Inference produces a **retrospective demonstration for
9–15 December 2011**, rather than current business predictions.

Training regenerates ignored `data/models` (model, context, metadata, checksums) and
`data/processed/forecasting`. Only load locally generated trusted artifacts; checksums
detect changes but do not authenticate serialized models. Models need the recorded
dependency versions. Reports, CSV evidence, PNGs and the notebook are tracked;
model binaries and interactive HTML are ignored. Do not run concurrent training or
inference while artifacts are being replaced. Training reruns reproduce the frozen
experiment and must not become test-guided tuning.

See [model evaluation](reports/model_evaluation.md),
[Phase 3 methodology](reports/phase_3_methodology.md), and
[Phase 3 progress](reports/phase_3_progress.md).

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest -W error
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/verify_data.py
.\.venv\Scripts\python.exe scripts/verify_analytics.py
.\.venv\Scripts\python.exe scripts/verify_forecasting.py
```

Tests cover Phase 1 plus schema constraints, atomic/repeatable imports, unknown
customers/countries, invoice grain, eligibility, monetary precision, tampered inputs,
SQL/pandas discrepancies, calendar gaps/partial months, duplicates, and empty inputs.
Synthetic fixtures test code only; published results use UCI records. CI checks
fixtures/lint/format without downloading data. Full-data/notebook verification is
performed locally and documented separately.

For the final completion audit, `python scripts/audit_phase2.py` independently
recalculates source-workbook KPIs, grouped revenue, duplicate sensitivity, NumPy
descriptive statistics, and Pearson/rank correlations. It compares them with the
published results and writes `reports/phase_2_audit_results.json`. This check does
not call the project cleaner or analytics functions. `.venv-audit` and `.audit-data`
contain the separate audit environment and data outputs and are ignored by Git.

## Source, limitations, and next phases

Chen, D. (2015). *Online Retail*. UCI Machine Learning Repository.
[DOI: 10.24432/C5BW33](https://doi.org/10.24432/C5BW33),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

The workbook has 541,909 lines; the ledger has 536,639 after 5,268 duplicate exclusions
and two negative-price quarantines. Cancellations and stock-adjustment candidates
remain classified. Missing IDs may bias customer findings. Exact duplicates are
ambiguous without a unique line key; restoring eligible repeats adds £24,573.74
(0.23%) in revenue but no distinct invoices. Charges/postage remain in KPI scope.
Cancellations are unmatched signed movements, not proven physical returns. Extreme
bulk orders affect averages. Missing dates, including every Saturday, are not verified
zero demand. The final day/month is partial; one retailer over about one year cannot
establish annual seasonality or represent all retail. Timestamps remain source wall time.

See [Phase 1 progress](reports/phase_1_progress.md),
[Phase 1 methodology](reports/methodology.md),
[Phase 2 progress](reports/phase_2_progress.md),
[Phase 2 methodology](reports/phase_2_methodology.md), and [findings](reports/findings.md).

Verified ingestion, SQL analytics and chronological seven-day forecasting are implemented in this snapshot. The dashboard is outside this milestone.
# Reproduce Quantiva locally

[README](../README.md) · [Architecture](architecture.md) · [Verification evidence](../reports/phase_5_progress.md)

## Environment and scope

Use **Python 3.11** (`>=3.11,<3.12`), Git and the committed
[dependency lock](../requirements-lock.txt). Windows PowerShell is the tested path.
Run commands from the checkout root. Initial downloads require internet access;
analysis and dashboard operation are local after installation and artifact preparation.
Allow several minutes and disk space for the workbook, Parquet, database, models
and installed scientific packages. No paid services or credentials are needed by the app.

Generation commands replace derived files, including tracked analytical reports.
For reproduction or an audit, use a **separate checkout**, not a workspace containing
evidence you need to preserve. Do not run preparation, database rebuild or training
concurrently with dashboard reads/inference. Stop Streamlit with Ctrl+C first.

## 1. Install from the lock

```powershell
git clone https://github.com/InfinitelyAimz/quantiva.git
cd quantiva
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\quantiva.exe --help
```

No activation or execution-policy change is necessary. If reusing an environment,
install the current lock again: an older Phase 1 environment can lack scikit-learn
or Streamlit. The editable install makes package code and SQL resources available;
keep the checkout in place. Do not upgrade individual dependencies when comparing
saved model artifacts with their recorded environment.

## 2. Obtain and verify the source workbook

```powershell
.\.venv\Scripts\quantiva.exe download
.\.venv\Scripts\quantiva.exe inspect
Get-FileHash -Algorithm SHA256 -LiteralPath 'data/raw/Online Retail.xlsx'
```

The downloader fetches the [official UCI ZIP](https://archive.ics.uci.edu/static/public/352/online+retail.zip),
extracts the workbook, validates its XLSX container and records URLs, retrieval time,
size and checksum. Existing raw bytes are reused, not replaced.

The workbook used for the published results has SHA-256:

```text
43465a06f2ccf7c8b5bd2892bc7defb52f97487934fe93b16ae4c3936424676d
```

This reference is recorded in [Phase 1 quality evidence](../reports/phase_1_quality.json).
A checksum records which bytes were analyzed; it does not prove every source record
is correct. Investigate a changed source hash rather than silently attributing old
findings to a new workbook.

Manual fallback: open the [UCI dataset page](https://archive.ics.uci.edu/dataset/352/online+retail),
download/extract **Online Retail.xlsx**, and place it at `data/raw/Online Retail.xlsx`
with the exact filename. Run `inspect`, compare the checksum, then continue.
Do not substitute fabricated records. Attribution: Chen (2015),
[DOI 10.24432/C5BW33](https://doi.org/10.24432/C5BW33), CC BY 4.0.

## 3. Prepare the ledger and SQLite

```powershell
.\.venv\Scripts\quantiva.exe prepare
.\.venv\Scripts\python.exe scripts/verify_data.py
.\.venv\Scripts\quantiva.exe database
```

Expected outputs under `data/processed/`: `transactions.parquet`, `exclusions.parquet`,
`initial_inspection.json`, `cleaning_report.json`, `manifest.json` and `quantiva.db`.
The unchanged UCI source produces 536,639 ledger lines and 524,878 eligible-sales
lines from 541,909 original lines; 5,268 duplicates and two negative-price lines
are excluded. Counts for overlapping quality conditions must not be summed.

`prepare` preserves raw bytes and replaces derived outputs, writing the manifest
last. The output set is not a single transaction. `database` verifies raw/derived
checksums, builds and validates a sibling SQLite file, then atomically replaces the
database. Logical rows can reproduce even if SQLite's physical file bytes differ.

## 4. Generate analytics and inspect SQL

```powershell
.\.venv\Scripts\quantiva.exe analyze
.\.venv\Scripts\python.exe scripts/verify_analytics.py
.\.venv\Scripts\quantiva.exe query
.\.venv\Scripts\quantiva.exe query kpis
.\.venv\Scripts\quantiva.exe query monthly_growth
.\.venv\Scripts\quantiva.exe query customer_frequency
```

`query` lists the 14 available packaged SQL names. `analyze` verifies lineage and
reconciliation before regenerating findings, metrics, CSVs and figures in `reports/`.
Expected reconciliation: **3,982 comparisons**, with exact counts and absolute
monetary tolerance £0.000001. Gross eligible revenue is £10,642,110.804 before display
rounding. No cancellation netting or charge-code redefinition is performed.

## 5. Train, evaluate and load the historical forecast

```powershell
.\.venv\Scripts\quantiva.exe forecast-prepare
.\.venv\Scripts\quantiva.exe forecast-train
.\.venv\Scripts\quantiva.exe forecast-compare
.\.venv\Scripts\quantiva.exe forecast
.\.venv\Scripts\quantiva.exe forecast-verify
.\.venv\Scripts\python.exe scripts/verify_forecasting.py
```

`forecast-train` also prepares the daily target; the explicit preparation command
lets you inspect it first. It regenerates the fixed experiment and reports, not a
new tuning search. Expect validation-selected `random_forest`, held-out Weekly
Seasonal Naive superiority, and **30 forecasting checks**. Inference covers
**9–15 December 2011**, from origin/cutoff **8 December 2011**, model version **3.0.0**.
The second prediction is zero; this does not establish zero demand.

Expected artifacts: `data/processed/forecasting/daily_series.parquet`, series metadata,
`selection_before_test.json`, and `latest_forecast.csv`; model/preprocessing, context,
metadata and checksums in `data/models/`; prediction/comparison/horizon CSVs,
`forecast_results.json`, model evaluation and PNGs in `reports/`.

Model binaries are intentionally absent from Git. **Regenerate with `forecast-train`**
to restore them. There is no hosted artifact download. If restoring your own backup,
keep its full model/context/metadata/checksum set and matching dependency versions;
then run `forecast-verify`. Load only artifacts you generated or otherwise trust.
Checksums detect changes but do not authenticate a malicious serialized model.

## 6. Execute notebooks in fresh kernels

```powershell
.\.venv\Scripts\python.exe scripts/execute_notebooks.py
```

This runs all three notebooks with the calling environment's Python, clears prior
outputs, verifies execution and saves successful results. No global kernel is
registered. Run training first. To execute only forecasting:

```powershell
.\.venv\Scripts\python.exe scripts/execute_notebooks.py --phase 3
```

Notebooks may regenerate figures and their own tracked outputs. Their historical
phase-specific conclusions remain explanatory records; current project status is
in the README and latest progress report.

## 7. Launch and verify the dashboard

```powershell
.\.venv\Scripts\python.exe scripts/verify_dashboard.py
.\.venv\Scripts\python.exe -m streamlit run app/Home.py
```

Open the localhost URL printed by Streamlit (normally port 8501). The committed
configuration binds to loopback. Required data: SQLite plus current quality/analytics
reports; the Predictive page additionally needs forecasting evidence and trusted local
models for inference. Missing artifacts produce setup guidance, not invented data.
Dashboard verification expects **63 checks**.

Use all five pages; switch Light/Dark and GBP/ZAR, navigate and confirm choices persist.
Dates/countries affect Overview, Sales and Customers; Sales also exposes product codes.
RFM selection does not change the customer KPI cohort. Predictive/Quality pages
explain their full-data scope. GBP is authoritative; default ZAR is an explicitly
illustrative fixed-rate conversion. See [methodology](methodology.md).

## 8. Automated checks

```powershell
.\.venv\Scripts\python.exe -m pytest -W error
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/verify_portfolio.py
```

The 105 tests use fixtures and do not require a downloaded workbook. Full-data
verification requires the stages above. `verify_portfolio.py` checks the published
documentation, local links/anchors, PNGs, headline evidence and actual CLI choices;
it does not regenerate analytical files or replace visual review.

| Command group | Writes |
| --- | --- |
| `download`, `inspect`, `prepare`, `database` | Raw provenance or regenerated processed artifacts |
| `analyze`, `forecast-prepare`, `forecast-train`, `forecast` | Derived data/models and/or analytical reports |
| `verify_data.py`, `verify_analytics.py`, `forecast-verify`, `forecast-compare`, `query`, `verify_portfolio.py` | Read-only results to the terminal |
| `verify_forecasting.py`, `verify_dashboard.py` | Tracked verification JSON; dashboard report includes local timings |
| `execute_notebooks.py` | Notebook outputs and potentially figures |

For a read-only acceptance audit, inspect report writers first or run them in a
separate checkout. Do not accidentally overwrite historical evidence merely to
check it. [Phase 5 progress](../reports/phase_5_progress.md) distinguishes fresh
regeneration from non-writing primary-workspace verification.

## Cross-platform guidance and troubleshooting

On macOS/Linux replace `py -3.11` with `python3.11`, `.venv\Scripts\python.exe` with
`.venv/bin/python`, and `.venv\Scripts\quantiva.exe` with `.venv/bin/quantiva`.
Use `sha256sum 'data/raw/Online Retail.xlsx'` or `shasum -a 256` for the source hash.
The lock/CI and Phase 5 reproduction were tested on Windows Python 3.11; other
platforms may require compatible wheels and are not independently verified here.

| Symptom | Action |
| --- | --- |
| Python version rejected | Install Python 3.11 and recreate the environment |
| Module missing or `quantiva` unavailable | Install the current lock, then the editable package using that same environment's Python |
| Source download fails | Use the official manual fallback and compare SHA-256 |
| Missing manifest or stale provenance | Finish `prepare`, then rebuild `database` and regenerate dependent reports |
| Database locked/replacement fails | Close Streamlit/SQLite readers; run one rebuild process at a time |
| Forecast metadata/checksum/dependency mismatch | Rebuild trusted artifacts with the locked environment; do not bypass integrity validation |
| Dashboard missing an artifact | Complete analytics and forecasting generation; inspect the displayed setup guidance |
| Port already occupied | Add `--server.port 8502` to the Streamlit startup command |
| First page slow | Cold SQL aggregation can take seconds; matching scopes are cached, not an SLA |

Optional relocation: set `$env:QUANTIVA_DATA_DIR = '.\local-data'` before running
commands. The override relocates data/model paths, not reports or notebooks, which
remain tied to the source checkout. `.env` files are not loaded automatically.
Keep raw data, databases, model binaries, environments and private configuration
out of Git. Review `git status` after any regeneration rather than discarding changes.

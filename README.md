# Quantiva — Retail Intelligence & Predictive Analytics

Quantiva is a local, reproducible data science portfolio project using real UCI
Online Retail transactions. Its business goal is to explain retail performance,
customer purchasing patterns, and the reliability of short-horizon revenue forecasts.

**Current scope: Phase 1 — foundation, ingestion, inspection, and cleaning.**
SQL analytics, notebooks, models, and Streamlit are later phases requiring explicit
approval. There is no dashboard or forecasting result yet.

The complete requirements are in [PROJECT_SPECIFICATION.md](PROJECT_SPECIFICATION.md).

## Architecture and stack

```text
Official UCI ZIP → immutable raw XLSX → quality inspection
                                      ↓
                              deterministic cleaning
                                      ↓
                       processed Parquet + audit records
                                      ↓ (Phase 2)
                         SQLite / SQLAlchemy → analytics
                                      ↓ (later phases)
                             forecasting → Streamlit
```

- Python 3.11; pandas and NumPy for data processing.
- requests for HTTPS download; openpyxl for the original Excel workbook.
- PyArrow for typed, compressed Parquet files; pytest and Ruff for verification.
- Planned: SQLAlchemy (Phase 2), Jupyter/Plotly/Matplotlib (Phase 2),
  scikit-learn/joblib (Phase 3), Streamlit (Phase 4).

`src/quantiva` contains reusable logic; `scripts` contains convenience entry points.
Configuration lives in `config.py`. Data defaults to the repository's `data` folder;
set `QUANTIVA_DATA_DIR` to relocate it. No credentials or cloud subscription are needed.
The `.env.example` documents settings; `.env` files are not loaded automatically.
Empty app, notebook, and model folders reserve space without pretending those features exist.

## Installation (Windows PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
```

Use the virtual environment executables directly; activation is optional and no
PowerShell execution policy changes are required. The lock file pins the tested
Python 3.11 environment, including build tooling. On macOS/Linux use Python 3.11
and `.venv/bin/python` / `.venv/bin/quantiva` instead.

## Download and inspect

```powershell
.\.venv\Scripts\quantiva.exe download
.\.venv\Scripts\quantiva.exe inspect
```

Download uses [UCI's official archive](https://archive.ics.uci.edu/static/public/352/online+retail.zip).
It records the source, retrieval time, size, and SHA-256 next to the workbook.
An existing workbook is preserved, never downloaded over. Inspection always hashes
the workbook actually read, including a manually imported file.

If downloading fails, open the [UCI dataset page](https://archive.ics.uci.edu/dataset/352/online+retail),
click Download, extract **Online Retail.xlsx** to `data/raw/Online Retail.xlsx`, and
run `inspect`. Preserve the original workbook. Do not substitute generated records.

Citation: Chen, D. (2015). *Online Retail*. UCI Machine Learning Repository.
[DOI: 10.24432/C5BW33](https://doi.org/10.24432/C5BW33). Licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Invoice codes beginning with C indicate cancellations according to UCI.
Prices are in pounds sterling. Invoice timestamps have no timezone; preserve their
source wall time rather than converting them to the developer's timezone.

## Prepare and verify

```powershell
.\.venv\Scripts\quantiva.exe prepare
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts/verify_data.py
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
```

See [the methodology](reports/methodology.md) for definitions and treatment of returns,
duplicates, missing identifiers, and invalid records, and [the Phase 1 report](reports/phase_1_progress.md)
for measured quality results and verification. Generated datasets are ignored by Git.
Preparation replaces derived files rather than appending, making repeated imports idempotent.

## Limitations and remaining phases

The source covers approximately one year of one UK retailer, with many wholesale
customers. It is neither representative of all retail nor adequate to establish
stable annual seasonality. A cancellation record does not prove a physical return.
Exact repeated rows may be ingestion duplicates or legitimate repeated line items;
deduplication is a documented assumption, not verified ground truth.

Phase 2 will implement SQLite tables, indexes, constraints, SQL examples, reconciled
KPIs, and executable EDA/statistical notebooks. Phase 3 will compare naive and seasonal
naive baselines with linear regression and random forest using chronological evaluation
and leakage-safe features. Phase 4 will deliver the five-page navy Streamlit dashboard.
Phase 5 will add screenshots, a portfolio case study, and results-based CV bullets.
Model evaluation, analytical business findings, dashboard launch instructions, and
screenshots will be published when those phases have actually run.

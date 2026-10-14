# Phase 1 progress — 14 October 2026

## Implemented

Inspected the existing repository before changes: clean `main`, initial commit
`a48c30a`, remote `https://github.com/InfinitelyAimz/quantiva.git`. Preserved the
existing Git history and configuration, and worked on `codex/phase-1-foundation`.
Saved the complete user specification verbatim as `PROJECT_SPECIFICATION.md`.

Created a Python 3.11 virtual environment, installable `src` package, dependency
lock file, configuration, ignored data/artifact paths, command-line interface,
convenience scripts, pytest suite, and a Windows CI workflow. The CI workflow is
configured but has not run remotely; no push has been made.

Implemented official download with workbook integrity checks and checksum provenance,
raw inspection, deterministic cleaning, line-revenue calculation, typed Parquet
outputs, an exclusion audit, versioned cleaning rules, and output hash manifest.
Published setup instructions and a technical methodology explaining the data decisions.

## Observed initial quality

Source: Chen, D. (2015), UCI Online Retail, DOI 10.24432/C5BW33, CC BY 4.0.
Downloaded the official workbook successfully; size **23,715,344 bytes**.
SHA-256: `43465a06f2ccf7c8b5bd2892bc7defb52f97487934fe93b16ae4c3936424676d`.
The dataset covers **1 December 2010 08:26 through 9 December 2011 12:50**, with
timestamps preserved as source wall time.

| Raw quality measure | Measured count |
| --- | ---: |
| Original transaction lines | 541,909 |
| Missing customer IDs | 135,080 (24.93%) |
| Missing descriptions | 1,454 |
| Exact repeated rows beyond first occurrences | 5,268 |
| Rows belonging to duplicate groups (including first occurrences) | 10,147 |
| C-prefixed cancellation rows | 9,288 |
| Negative quantity rows | 10,624 |
| Negative quantity without C prefix | 1,336 |
| Zero-price rows | 2,515 |
| Negative-price rows | 2 |
| Zero quantities / invalid timestamps | 0 / 0 |
| Distinct positive customer IDs in raw data | 4,372 |

All raw cancellation rows have negative quantities. Noncancelled negative rows
include descriptions such as “check”, “damages”, and “thrown away”; these suggest
inventory corrections rather than documented customer returns. After classification,
all 1,336 noncancelled negative rows have zero price. They remain in the ledger as
stock-adjustment candidates, excluded from completed-sales revenue.

Quantity median is 3, with quartiles 1 and 10; the 99th percentile is 100. The maximum
absolute quantity is 80,995. Unit-price median is £2.08 and the 99th percentile is
£18.00, while extreme prices reach £38,970. These tails warrant investigation in
Phase 2, not automatic trimming. This phase reports data quality, not business KPIs.

## Cleaning outcome

| Disjoint row partition | Count |
| --- | ---: |
| Cleaned ledger | 536,639 |
| Exact duplicate exclusions | 5,268 |
| Quarantined negative-price rows | 2 |
| Total reconciled to raw | 541,909 |

| Ledger classification | Count |
| --- | ---: |
| Eligible completed-sale lines | 524,878 |
| Cancellation lines | 9,251 |
| Stock-adjustment candidates | 1,336 |
| Positive-quantity zero-value lines | 1,174 |
| Unlinked positive-price negative lines | 0 |

Cancellation counts decrease after exact deduplication; cancellations themselves
were retained. The ledger still contains 1,454 missing descriptions and 135,035 rows
without valid customer IDs, including **132,186 completed-sale lines**. Those sales
remain available to aggregate revenue analyses, while later customer analyses must
exclude unidentified customers. A line count is not an order count.

Generated local outputs are `transactions.parquet`, `exclusions.parquet`,
`initial_inspection.json`, `cleaning_report.json`, and `manifest.json` under
`data/processed`. They are deliberately ignored by Git. A small committed JSON
summary records measured quality findings without exposing transaction rows.

## Verification

- **23 pytest tests pass with warnings treated as errors.** Tests cover source
  preservation, official archive extraction, download errors, required schemas,
  cancellation classification, invalid prices/quantities/dates, anonymous customers,
  exact duplicate auditing, empty input, and repeatable output artifacts.
- Ruff lint and format checks pass; dependency consistency check passes.
- Full-data verification passes: raw/report hash agreement, all output checksums,
  complete unique source-row coverage, disjoint row accounting, completed-sales
  eligibility, signed line amounts, and classification totals.
- The full dataset is prepared twice and compared via the manifest, which includes
  every output hash. Repeated preparation produces identical derived artifacts.
- The raw workbook hash remains unchanged throughout processing.
- Setup was exercised locally: virtual environment creation, dependency installation,
  editable package installation, download, inspect, prepare, and verification.

Run the same checks:

```powershell
.\.venv\Scripts\python.exe -m pytest -W error
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\python.exe scripts/verify_data.py
.\.venv\Scripts\python.exe -m pip check
```

## Outstanding limitations and recommended next steps

No blocking Phase 1 defects remain. The cleaning assumption about exact duplicates
cannot be proven from the available schema. Cancellation records do not establish
physical returns or connect every adjustment to an original invoice. Missing IDs
may bias customer insights. Extreme quantities and product codes for charges or
adjustments require EDA. The final day is partial, both December months have unequal
coverage, and the short history limits forecasting conclusions. Derived monetary
values use float64 rounded to four decimal places; they are analytical values, not
accounting settlement amounts. The multi-file output set is not transactionally
atomic, so preparation must run alone and finish before consumers read it.

The next approved phase should implement SQLite/SQLAlchemy with transaction,
invoice, product, and customer relationships; rebuild-safe imports; SQL joins,
CTEs, window functions, and calendar aggregations; revenue/KPI reconciliation; and
executable EDA/statistics notebooks with written chart interpretations. Begin with
revenue definitions and duplicate-sensitivity checks before publishing KPIs.

**Phase 2 has not started and requires the user's explicit approval.** No models,
forecast scores, dashboard screenshots, or CV achievements have been invented.

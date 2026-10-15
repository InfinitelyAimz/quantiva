# Phase 4 completion report

## A. Git status

Verified baseline main/origin main: `7eb1d20d044f17dc8061630419823a0e6fb36c82`.
The original working tree was clean and 66 tests passed before `phase-4` was created.
Phase 1–3 commits and branches are preserved. Complete user requirements are saved in
`PHASE_4_SPECIFICATION.md`. Only `phase-4` is authorized for implementation commits
and pushes. Implementation commit: `924ae2cad8a7ed6bc55d1e36cdc262980be24864`,
published on `origin/phase-4`. Draft [PR #2](https://github.com/InfinitelyAimz/quantiva/pull/2)
targets `main` and remains unmerged. A following documentation commit records this
publication; its final SHA is supplied in the delivery message to avoid a self-referential
hash here. The branch exists on GitHub. No main modification,
merge, force push, branch deletion or Phase 5 work is part of this delivery.

## B. Implementation

- `app/Home.py`: application frame, supported five-page navigation and persistent
  appearance control; page failures retain navigation and provide setup guidance.
- `dashboard/data.py`: parameterized SQLite scope and aggregate reads, packaged KPI
  reuse, file/WAL signature cache invalidation and source/filter month completeness.
- `dashboard/components.py` and `theme.py`: shared cards, escaped bounded tables/CSV
  exports and consistent Plotly charts, dark/light tokens and responsive CSS.
- `dashboard/pages.py`: Overview, Sales Analytics, Customer Intelligence, Predictive
  Analytics and Data Quality with the required charts, scope notes and source caveats.
- `segmentation.py`: identifiable-customer RFM, deterministic tie-safe/sparse scoring
  and six mutually exclusive exhaustive descriptive segments.
- `dashboard/evidence.py`: verify saved prediction/metric agreement separately from
  optional binary-model availability. Existing trusted Phase 3 inference is reused.
- Streamlit 1.66.0 and its dependencies are locked; local configuration binds loopback
  and disables usage statistics. No credentials/cloud/paid service is required.
- README setup/launch instructions, Phase 4 methodology, UI verification, screenshots,
  machine-readable browser/data verification and 39 dashboard/RFM/presentation cases added.

Streamlit reruns the page after widget interaction; session state preserves theme and
the shared commercial scope. Cached SQL aggregates avoid repeated transaction scans.
RFM is new descriptive analytics, not a clustering algorithm. The predictive page
does not train or redefine the Phase 3 experiment. These choices prioritize consistent
business definitions and traceable evidence over presenting every table as a new model.

## C. Verification

Windows Python 3.11.9 was used in `.venv-phase4`; a second fresh environment under
ignored `.audit-data/phase4-fresh` installed the final committed dependency lock and
editable package with `--no-deps --no-build-isolation`. No runtime dependency conflicts.

| Executed command | Result |
| --- | --- |
| `python -m pytest -W error` | 105 passed, including the previous 96 and nine presentation cases |
| Fresh locked environment: `python -m pytest -W error` | 96 passed during the earlier currency follow-up; not reinstalled for styling |
| `ruff check .` | Passed |
| `ruff format --check .` | Passed |
| `python -m pip check` | No broken requirements |
| `python scripts/verify_data.py` | All seven Phase 1 checks passed |
| `python scripts/verify_analytics.py` | Five integrity/coverage/lineage checks, 14 queries and 3,982 reconciliations passed |
| `python scripts/verify_forecasting.py` | 30 forecasting checks passed, including saved inference |
| `python scripts/verify_dashboard.py` | 63 full-data/filtered/RFM checks passed; zero failed |
| `python -m streamlit run app/Home.py --server.port 8501` | Real local app launched and browser-tested |

New tests cover cache invalidation on atomic rebuild, parameter binding/injection
strings, date gaps/empty scopes, product and country grouping, monthly completeness,
RFM recency/distinct frequency/value and tie/segment rules, theme state/figure colors,
widget/filter reruns, missing prerequisites, and evaluation separation/tampering.
Initial tests found an empty-scope pandas dtype warning; explicit numeric conversion
fixed it. A UI fixture initially selected an unavailable cancelled-only country;
the corrected test selects a real eligible option and verifies actual changed values.
No current project test failure remains.

Real browser verification covers all five pages and both themes at 1440×950,
country/product/segment/evaluation controls and navigation persistence, plus responsive
behavior at 600×900. See `phase_4_ui_verification.md` for the precise scope and manual
repeat steps; formal accessibility/device certification is not claimed. Error states
are covered by AppTest/service fixtures without deleting the user's real artifacts.

Cold full-scope aggregate time was 5.59s; matching cached read 0.008s on this run.
Cold loads can be noticeable. Cached entry counts, aggregate-only reads, bounded
tables and no retraining/raw workbook reads keep repeated exploration practical.
These timings are observations, not universal performance guarantees.

## D. Analytical integrity

Full-data dashboard results reproduce Phase 2: £10,642,110.804 gross eligible sales,
19,960 completed orders, £533.1718839679359 AOV, 5,572,420 units, 4,338 identifiable
purchasers and 65.583218% within-period repeat rate. Displayed cards round for reading;
calculation uses the existing fixed-point monetary aggregation and invoice definitions.
Filtered scopes are independently compared against eligible Parquet observations.
Product-filter AOV is selected-line revenue per affected invoice, explicitly labeled.
Monthly growth excludes incomplete source or filter periods.

Full-data RFM reference is 2011-12-10. Counts: Champions 911, At Risk 513, Hibernating
1,214, Loyal Customers 381, New Customers 515, Potential Loyalists 804. They account
for all 4,338 identifiable purchasers. Recency, distinct invoice frequency and monetary
values match independent eligible-source groupings. Scores are relative to the current
scope, tie-safe and sparse-sample aware; segment labels are not validated churn, first
acquisition or lifetime value. IDs are pseudonymous source identifiers.

Forecast results remain unchanged from Phase 3. Random Forest remains validation-selected,
while weekly seasonal naive has better held-out MAE (£11,250.17 vs £12,344.71).
Linear Regression has no invented test score. The December 2011 demonstration displays
model/version/cutoff/horizon and no fabricated intervals. Current code selection and
historical manual decision provenance remain distinct. Model checksums, dependency
versions and metadata hash are validated; evaluation stays accessible without a model.

Data Quality preserves duplicate ambiguity, anonymous customer coverage, cancellations,
stock-adjustment candidates, zero-value lines, negative-price quarantine, calendar gaps,
partial boundaries and eligibility of charges. Stored verification does not assert
the current test suite passed; an explicit action separately checks current artifacts.

## E. Readiness, limitations and next steps

Phase 4 is ready for user review, with no known blocking defect. The draft PR remains
unmerged; this report does not approve the phase or authorize Phase 5.

Known limitations: controlled CSS depends on Streamlit 1.66.0 and needs retesting on
upgrades; initial reported theme may lag; session state is not cross-session storage;
cold reads take seconds; signatures invalidate caches but do not authenticate files;
simultaneous data rebuilds are unsupported; no formal accessibility certification or
all-device testing. Business limitations and weaker forest held-out performance remain
visible. No production deployment, calibrated intervals, new model tuning or K-Means
was introduced.

After explicit approval, Phase 5 can refine the portfolio case study, selected
screenshots, concise accurate CV bullets and final presentation. No Phase 5 work has
started. Review the dashboard, definitions, visual evidence and draft PR first.

## Follow-up: KPI layout and currency — 15 October 2026

Recovery audit found a clean, intact branch but a truncated revenue value at 1280px.
The shared metric CSS now uses bounded container-relative type and wrapping fallback,
preserving the existing layout, themes and other KPI values. Browser measurements
cover 600/1024/1280/1440px × GBP/ZAR × dark/light: 16 passing Overview states.
Full revenue is £10,642,110.80 or illustrative R 135,240,167.58, with unchanged counts.

`dashboard/currency.py` adds immutable presentation conversion, labels and export
provenance. ZAR is the session default; the sidebar selector persists on all pages.
Use a fixed 2011-12-08 ECB cross-rate, 1 GBP = 12.708021 ZAR, explicitly illustrative.
All monetary cards/charts/hover labels/tables/narratives and dashboard exports follow
the selection. RFM scores, counts, WAPE and model ranking remain unchanged; only
monetary displays scale. Source GBP aggregates, SQL, model code and artifacts are
untouched. See methodology for primary source, derivation, precision and limitations.

Eight new tests cover formatting, conversion, row units, unchanged source frames,
model ranking, RFM values, export metadata, charts/tables/CSV consistency and widget
persistence. The complete suite now has 96 tests. Full-data regressions again pass
(7 Phase 1, 3,982 Phase 2, 30 forecasting, 63 dashboard checks). Report-writing
statements were omitted in memory during verification so historical stored evidence
was not overwritten; the verification logic and repository scripts were unchanged.
The browser-downloaded ZAR CSV reconciles all 4,338 customers and unchanged RFM scores.
Original screenshots remain historical; new currency captures and the extended browser
record document the correction. Draft PR #2 remains the review vehicle; final follow-up
commit/synchronization details are reported in the delivery message. No main change,
merge, dependency change, dataset rebuild, model retraining or Phase 5 work is included.

## Follow-up: professional UI refinement — 15 October 2026

Completed on the existing clean `phase-4` branch from `811abdf`. Requirements are
saved in `PHASE_4_UI_REFINEMENT_SPECIFICATION.md`. `app/Home.py` and shared theme,
components and page modules retain the five-page architecture. New
`dashboard/presentation.py` handles human labels, safe table markup and log-axis
eligibility separately from analytical data and export definitions. The sole existing
currency-test adjustment expects the improved `Revenue (ZAR)` display header; CSV
checks and monetary expectations are preserved. Nine presentation cases are added in
`tests/test_dashboard_presentation.py`.

Changes: consistent headings/spacing/cards; stronger active navigation, icon contrast,
multiselect surfaces and focus; explicit month coverage and ranked countries;
semantic segment/model colors; more readable customer bars and optional log spending
axes without dropping outliers; correct RFM labels; readable forecast comparisons and
Lowest MAE markers; progressive methodology disclosure; grouped quality information;
and aligned, escaped, focusable tables with readable counts/percentages/units.

Verification: 105 tests passed in 22.74s on the final code, Ruff lint/format and pip
check passed. Read-only Phase 1–4 verification again passed 7 integrity checks,
3,982 SQL/pandas comparisons, 30 forecasting checks and 63 dashboard checks. Only
the report-write statements were omitted in memory, preserving existing reports.
Hashes confirm 42 protected data, RFM, SQL-access/evaluation and forecasting files
unchanged. Full-data segment counts and forecasting results remain as reported above.
GBP/ZAR behavior and the fixed rate are unchanged. The new browser CSV is identical
to the prior verified export, including all 4,338 customers.

Browser: 40 page/theme/width states at 600/1024/1280/1440px pass, plus real filter,
currency/navigation, log/linear, held-out selection and keyboard-focus interactions.
Representative `dashboard_polish_*.png` images and
`phase_4_polish_browser_checks.json` record this review; precise scope, comparison and
remaining limitations are in `phase_4_ui_verification.md`. No formal accessibility
or universal device/performance certification is claimed.

Performance: no additional SQL calls, model loads or dependencies. Isolated cold
aggregate read 5.96s; cached read 0.010s. A concurrent verification run took 10.95s
while tests/server work overlapped, so timing is load-dependent. The unchanged data
layer and caching still dominate initial load time; this is not an optimization claim.

Draft PR #2 remains unmerged for user review. Final commit SHA, remote synchronization
and CI status are reported in the delivery message. Main and Phase 5 are untouched.

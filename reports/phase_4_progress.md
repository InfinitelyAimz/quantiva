# Phase 4 completion report

## A. Git status

Verified baseline main/origin main: `7eb1d20d044f17dc8061630419823a0e6fb36c82`.
The original working tree was clean and 66 tests passed before `phase-4` was created.
Phase 1–3 commits and branches are preserved. Complete user requirements are saved in
`PHASE_4_SPECIFICATION.md`. Only `phase-4` is authorized for implementation commits
and pushes; the resulting draft PR URL and final commit SHA are reported after
publication, avoiding a self-referential hash in this report. No main modification,
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
  machine-readable browser/data verification and 22 dashboard/RFM test cases added.

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
| `python -m pytest -W error` | 88 passed, including all 66 Phase 1–3 cases and 22 new cases |
| Fresh locked environment: `python -m pytest -W error` | 88 passed |
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

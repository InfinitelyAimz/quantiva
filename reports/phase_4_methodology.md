# Phase 4 dashboard methodology

## Architecture and data flow

`app/Home.py` is the Streamlit application frame. Supported `st.navigation`, `st.Page`
and `st.page_link` APIs route five page functions in `dashboard/pages.py`. Streamlit
reruns Python when widgets change; the frame owns the persistent appearance control
and the page owns its scoped filters. Shared components render headings, KPI cards,
bounded accessible tables and Plotly figures. Business calculations live in
`dashboard/data.py`, `dashboard/evidence.py` and `segmentation.py`, separate from UI.

The dashboard reads SQLite aggregates through existing SQLAlchemy connections and the
existing `completed_sales` view. The authoritative packaged KPI SQL is reused inside
a filtered CTE. Source eligibility, integer £0.0001 aggregation, invoice grain and
anonymous-sale treatment remain unchanged. No raw workbook is read on reruns.
Daily/weekly/monthly counts use distinct invoices within that period, not sums of
daily counts. Product descriptions are labels, stock codes identifiers. Null countries
have an explicit Unknown label. Orders can appear in more than one product group;
group counts must not be added to obtain total distinct orders.

## Filters and coverage

Overview and Customer Intelligence share inclusive dates and country selections.
Sales adds stock-code filtering. SQL binds all values, including list entries;
column/period expressions are allowlisted. End dates become an exclusive next-day
timestamp. Out-of-coverage and reversed dates are rejected; stale category selections
are reset to available choices. An empty category selection means all categories.
No hidden product filter applies on the other pages.

Every commercial KPI/chart follows the visible scope. A product filter selects lines,
so AOV becomes selected eligible GBP divided by affected distinct invoices, not full
basket value. RFM segment choices affect its charts/tables only; customer KPI cards
retain their labeled date/country scope. Predictive Analytics and Data Quality use
fixed full-data evidence and explicitly disable commercial-filter semantics.

Monthly completeness follows Phase 2, additionally requiring selected dates to cover
the whole month. Growth exists only between adjacent complete months with a positive
previous total. December 2011 is partial. Weekly periods start Monday and boundary
weeks can be partial. Zero-filled daily gaps represent observed activity, not proven
zero demand. Commercial/RFM analysis retains Phase 2 source coverage through the final
partial day; the independent Phase 3 forecasting policy excludes both boundary days.

## RFM definitions and scoring

Use only identifiable eligible purchasers in the current date/country scope. Anonymous
sales remain in commercial revenue but not RFM. Recency is calendar days between the
latest eligible purchase and the day AFTER the selected end date (full-data reference:
10 December 2011). Frequency is distinct eligible invoices, not transaction lines.
Monetary is gross eligible GBP, with no cancellation netting.

Higher F/M scores mean higher observed frequency/value. Lower recency gets a higher
R score. For at least five distinct values, empirical 20/40/60/80 percentile thresholds
define scores 1–5; equality belongs to the lower base bin before recency inversion.
Tied values always get the same score; no ID-based tie breaking or jitter occurs.
Fewer than five distinct values use evenly spaced dense-value ranks over 1–5, leaving
unsupported score bins empty. A constant value gets neutral score 3. Sparse groups
are therefore not forced into arbitrary five equally sized bins. Scores recalibrate
within each scope, so they are relative group descriptions rather than absolute
cross-scope classifications. RFM code is three-digit R/F/M, not a continuous risk score.

First matching segment rule wins:

| Segment | Exact ordered rule |
| --- | --- |
| Champions | R≥4 and F≥4 and M≥4 |
| At Risk | Remaining R≤2 and (F≥3 or M≥4) |
| Hibernating | Remaining R≤2 |
| Loyal Customers | Remaining F≥4 |
| New Customers | Remaining R≥4 and F≤2 |
| Potential Loyalists | All remaining eligible customers |

This partitions every eligible customer once. These labels are descriptive, not
validated churn, first-ever acquisition, lifetime value or machine learning clustering.
IDs are pseudonymous source identifiers, not verified identities. The full-data
segment counts and independent recency/frequency/monetary checks are in
`phase_4_verification.json`.

## Themes, state and charting

`dashboard/theme.py` centralizes dark/light tokens, a restrained palette, chart canvas,
axes, legend and tooltip styling. Plotly uses explicit colors with Streamlit's automatic
chart theme disabled, so the session control governs the real chart appearance.
Tables are escaped HTML with bounded rows, scrolling and CSV export; no unthemeable
canvas data grid is used. Chart headings wrap outside the figure at smaller widths.
CSS stacks columns below 1,100px; Streamlit handles the mobile sidebar drawer.

The visible Light/Dark control updates `quantiva_theme` in session state and persists
across navigation/reruns. Initial appearance uses Streamlit's reported theme type where
available; it may lag on first load. Direct operating-system theme detection is not
claimed. Native widgets have no supported per-session runtime theme setter, so
controlled CSS overrides cover application/sidebar/controls/date fields/popovers/
tables/messages. Selectors use stable semantic roles and a small set of Streamlit
test IDs, avoiding generated Emotion class names. This is version-specific styling,
tested with locked Streamlit 1.66.0; widget/date-popup/contrast tests must be repeated
before a Streamlit upgrade. Browser Settings theme changes after initial load do not
override the app's visible session choice.

The design uses text Quantiva branding, navy/white surfaces, blue accents and the
same components on every page. Local configuration disables usage statistics and
binds the app to loopback. No cloud services or credentials are required.

Official API references: [navigation](https://docs.streamlit.io/develop/api-reference/navigation/st.navigation),
[session context](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.context),
[theme configuration](https://docs.streamlit.io/develop/concepts/configuration/theming).

## Display currency

Added 15 October 2026 following the recovery audit and additional user requirements.
The sidebar defaults to ZAR and offers GBP; its separate session-state value persists
across pages and reruns. GBP remains the dataset and authoritative analytical unit.
Conversion happens on copies in `dashboard/currency.py`, called by the shared KPI,
chart, table and CSV components. SQL, cached GBP aggregates, RFM scoring, model
selection, evaluation calculations and saved artifacts are unchanged.

Use one fixed illustrative rate for the entire dashboard, including forecasts:

- Reference date: **8 December 2011**, within the source observation period.
- ECB series `EXR.D.GBP.EUR.SP00.A`: **0.8528 GBP per EUR**.
- ECB series `EXR.D.ZAR.EUR.SP00.A`: **10.8374 ZAR per EUR**.
- Cross-rate: `10.8374 / 0.8528`, rounded once to six decimal places:
  **1 GBP = 12.708021 ZAR**.
- [Official ECB observations, date and series identifiers](https://data-api.ecb.europa.eu/service/data/EXR/D.GBP+ZAR.EUR.SP00.A?startPeriod=2011-12-08&endPeriod=2011-12-08&format=csvdata),
  retrieved and inspected on 15 October 2026. No runtime network lookup is made.

Every page labels ZAR as illustrative and displays the rate/date. This is not a
transaction-date FX conversion, a period average, an accounting restatement, an
inflation adjustment or a current quote. It cannot establish historical South African
revenue. GBP mode restores the original units. Initial ZAR preference is a display
choice, not an inferred customer location.

Monetary columns use explicit `_gbp` source names. Presentation copies scale these
values, relabel displayed headers/axes/hover text, and leave dates, counts, percentages,
RFM scores/segments and metadata identifiers unchanged. Mixed duplicate-sensitivity
tables scale only monetary rows, retain count rows and percentages, and label row units.
Narrative amounts use the same currency formatter. KPI values use decimal half-up
rounding to cents; table/chart formatting is for presentation and CSV exports retain
numeric precision. Monetary exports identify source/display currency, reference rate,
date and illustrative-conversion status. Source report files are never converted.

A fixed positive multiplier scales MAE, RMSE and bias for display; WAPE and model
rankings remain unchanged. Selection still uses the frozen GBP results. RFM monetary
plots/tables convert after GBP scoring, so ties, segment membership and scores remain
unchanged. No currency selector feeds training, validation or model inference.

The KPI fix uses bounded CSS container-relative type with normal wrapping as a
fallback, scoped to the existing metric value. It removes ellipsis without reducing
all cards to one fixed small font. The existing small-screen column stacking remains.
Current browser checks cover both currencies/themes at 600, 1024, 1280 and 1440px;
see UI verification for observations and capture scope.

## Forecasting and evidence integrity

The predictive view reads Phase 3 predictions and independently recomputes their
reported metrics using the tested metric function. It checks validation/test separation
and chronology. Model loading uses existing explicit local trust, checksums, dependency
versions and context/metadata checks, plus a metadata hash comparison with the saved
evaluation. No model is cached without validation, downloaded or silently retrained.
Missing/invalid models leave saved evaluation evidence accessible with setup messages.

Display the 9–15 December 2011 demonstration, model/version, training cutoff, horizon
and GBP. It is retrospective, not live revenue. Validation selection and held-out
evaluation are separate; Linear Regression has no invented test result. Weekly seasonal
naive's better test MAE remains explicit. There are no fabricated uncertainty bands.
Current code selection is validation-only; historical manual decision independence
remains unverified. The post-evaluation deployment refit is distinct from pretest scores.

Data Quality reads original Phase 1 summaries, coverage, duplicate sensitivity and
stored Phase 2/3 verification evidence. It labels stored evidence as historical rather
than implying a test suite ran during the session. A separate button explicitly runs
current model integrity/inference verification. Cancellation, missing IDs, ambiguous
duplicates/nonstandard codes, quarantine and observation boundaries remain explained.

## UI refinement — 15 October 2026

The user-approved refinement requirements are preserved in
`PHASE_4_UI_REFINEMENT_SPECIFICATION.md`. This extends the existing Streamlit shell;
it does not introduce a new framework, dependency, analytical pipeline or data source.

`dashboard/presentation.py` separates readable UI labels and escaped tables from
technical export fields. Models use business-readable names in charts, controls and
tables; CSVs retain model identifiers. Counts have grouping without false decimal
precision, percentages have explicit percent signs, and monetary headers retain the
selected unit. Numeric cells align right, headers have column scope, and bounded table
regions support keyboard focus and internal scrolling. Currency conversion is unchanged.

Theme tokens now cover selection, hover, focus, spacing and radius alongside existing
colors. Sidebar links use the observed Streamlit page-link test IDs and the supported
current page URL path; no generated Emotion class names are targeted. Inactive icons,
multiselect surfaces and focus outlines have explicit theme colors. Native sidebar
navigation and the persistent theme/currency widgets remain unchanged.

The Overview names complete/partial months explicitly and ranks countries largest-first.
Source calendar policy, filtered scope and the distinction between recorded sales and
underlying demand remain visible. Date axes show month/year for longer histories and
day/month for short windows; hovers retain the appropriate full date or month.

Customer bar charts sort by customer count or recorded revenue and use one semantic
segment palette, shared with both scatterplots. The new monetary-axis control defaults
to a **logarithmic axis**, rather than transforming source data. Equal distances on this
axis indicate multiplicative differences. Plotly still receives original positive
display-currency values, and hover values remain unlogged. All observations and outliers
are retained. If any monetary value is non-positive or missing, a requested log view
falls back to a linear axis with an explicit message; rows are not silently discarded.
The linear option remains available. Axis ticks use whole powers of ten for readability.
RFM scores, thresholds, reference dates, segment membership and source monetary values
remain unchanged; the score distribution is labeled RFM Score and scope relativity is
explicit. The spending histogram retains original monetary units and its full range.

Forecast comparisons sort presentation copies by the selected period's MAE and label
its lowest MAE explicitly. This highlights an observed result, not a new selection
decision. Random Forest remains validation-selected; Weekly Seasonal Naive's stronger
held-out result remains visible. Model colors are stable across plots and periods.
Retrospective labeling, zero-prediction caveats and absent calibrated intervals remain
visible. Detailed metric definitions and chronology move into a labeled expander, while
the weaker held-out forest result remains outside it. No scores or model weights change.

Data Quality groups source/eligibility, exclusions and customer/transaction conditions,
then calendar coverage and provenance. Source metadata has an expander, but material
quality caveats and the historical/current verification distinction remain visible.
The explicit current-artifact action reports its successful checks separately from
the test suite. These changes add no SQL calls or model loads to the existing paths.

## Caching, performance and failures

`st.cache_data` stores read-only catalog/aggregate results with bounded entry counts;
presentation state and figure instances are separate. Keys include resolved path,
nanosecond mtime/size and SQLite WAL signature. After atomic database replacement or
WAL activity, reads are invalidated; a change detected during aggregate reading fails
with a retry message rather than publishing a mixed snapshot. Avoid simultaneous
rebuilds and dashboard reads. Signatures are invalidation, not cryptographic authentication.

Only aggregate tables are loaded: roughly 4,000 products/customers and 20,000 order
values for the full UCI scope, not 536,639 transaction rows. RFM scatter plots use the
aggregate customer rows. HTML tables display at most 50 rows and provide CSV exports.
Cold full-scope reads were 5.59 seconds on this Windows run; cached reads were 0.008
seconds. These are observations, not cross-machine guarantees or an SLA. There is no
distributed infrastructure, model retraining, or raw Excel load on reruns.

The application frame handles expected file, metadata, filter and SQL failures with
setup guidance while retaining navigation. It never substitutes synthetic business
records. Pure services, synthetic SQLite fixtures, Streamlit AppTest and browser QA
cover logic/widgets separately. The full-data verifier compares displayed calculations
with independent verified Parquet aggregates; published findings use UCI data only.

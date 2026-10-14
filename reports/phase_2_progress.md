# Quantiva Phase 2 progress — 14 October 2026

## A. Git state and scope

Development branch: **phase/02-analytics**. Phase 1's local branch was safely renamed
from `codex/phase-1-foundation` to **phase/01-foundation**. Both initially pointed to
the verified Phase 1 milestone `17755ee`, following `a48c30a` (initial commit).
The 23 baseline tests and full-data checks were re-executed before implementation.
Phase 1 files, raw data, commits, and history were preserved; cleaning rules did not change.

`main` and the locally recorded `origin/main` remain at `a48c30a`. Neither phase has
been merged into main. No branches or commits were pushed, and no remote fetch was
needed; the remote's live state has not been rechecked. Phase 2's verified changes
are saved as a local milestone; use `git log -1 --oneline` for its hash. The final
working tree is checked after committing. Future merge/push decisions need explicit
approval; the Phase 1 branch rename is local and does not rename any remote branch.

The submitted Phase 2 requirements are saved in `PHASE_2_SPECIFICATION.md`.
No Phase 3, RFM/clustering, dashboard, or Phase 5 implementation was undertaken.

## B. Implementation

New package modules:

- `database.py`: relational schema, manifest verification, fixed-point money,
  atomic rebuilding, constraints/indexes, integrity checks, canonical content digest.
- `analytics.py`: independent pandas KPIs, calendar aggregates, descriptive statistics,
  and duplicate sensitivity.
- `reconciliation.py`: packaged SQL execution, scalar/group reconciliation, tolerances,
  and failures on absent keys or disagreements.
- `analysis_report.py`: actual full-data calculations and generated reports.
- `visualization.py`: eight Matplotlib PNG figures and self-contained Plotly daily HTML.

Modified `config.py` adds the database path; `cli.py` adds database, query, and analyze
commands. Phase 1 modules and outputs remain unchanged. `pyproject.toml` adds Phase 2
dependencies and packaged SQL resources; the dependency lock is updated. `.gitignore`
excludes the fresh verification environment and generated large interactive HTML.
README now documents setup, rebuilding, SQL, analysis, reconciliation, notebooks, and limitations.

The six tables are transactions, invoices, products, customers, countries, and metadata.
Transactions retain Excel source-row traceability and nullable customer/country FKs.
Invoice timestamps remain on lines because 43 invoices have multiple timestamps.
There are 647 stock codes with multiple descriptions; product codes are keys, while
latest known names are display labels. Original names remain on transaction lines.
Money is stored in integer units of £0.0001; observed prices fit that precision.
Six indexes support date/invoice/customer/product/country/type-date queries.

Fourteen SQL files demonstrate all requested techniques: INNER/LEFT JOIN, GROUP BY,
HAVING, CTEs, window functions, dates, ranking, running totals, and percentage
contributions. Queries cover daily/monthly revenue, geography, product revenue/units,
invoice values/AOV, customer frequency/spending, repeat purchasing, safe monthly
growth, running revenue, and signed adjustments. SQL files are package resources.

Two executed notebooks:

- `01_data_exploration.ipynb`: 11 code cells covering sales/products/customers/geography,
  coverage, names, nonstandard codes, extreme records, and quality sensitivity.
- `02_statistical_analysis.ipynb`: 6 code cells covering location/spread/shape, outlier
  influence, calendar variability, and correlations at matched grains.

New scripts execute notebooks in isolated kernels and verify full-data analytics.
Tests add shared fixtures plus database and analytics suites. Reports include
`kpi_specification.md`, `phase_2_methodology.md`, generated `findings.md`,
`phase_2_metrics.json`, `monthly_revenue.csv`, `duplicate_sensitivity.csv`,
`reconciliation.csv`, and eight PNGs. Notebook sources are maintained directly,
avoiding a second duplicate set of cell templates.

## C. Actual business findings

| Metric | Measured value |
| --- | ---: |
| Gross eligible completed-sales revenue | £10,642,110.804 |
| Completed distinct invoices | 19,960 |
| AOV | £533.171884 |
| Eligible source units | 5,572,420 |
| Identifiable purchasers | 4,338 |
| Known-customer eligible revenue | £8,887,208.894 |
| Revenue per identifiable purchaser | £2,048.688081 |
| Identifiable repeat purchasers | 2,845 |
| Within-period repeat purchase rate | 65.58% |

Anonymous sales contribute 16.49% of gross revenue. Gross KPIs include eligible
postage/manual/service records; they are not settled payments, merchandise-only
sales, profit, or accounting net revenue. Cancellation movements are separate.

Top revenue codes are DOT (DOTCOM POSTAGE, £206,248.77), 22423 (REGENCY CAKESTAND 3 TIER,
£174,156.54), and 23843 (PAPER CRAFT, LITTLE BIRDIE, £168,469.60). Code 23843 is also
the highest-volume code at 80,995 units. Extreme cancellation counterpart candidates
are shown without asserting verified return matches. Top ten codes contribute
10.82% of revenue; top 100 contribute 34.46%. Nonstandard-code candidates contribute
£395,289.934; a syntax heuristic is an investigation aid, not a merchandise taxonomy.
Slow-moving codes have only one eligible unit in this window, which does not prove
poor performance without availability/introduction information.

Top countries: United Kingdom £9,001,744.09 (84.59%), Netherlands £285,446.34,
EIRE £283,140.52, Germany £228,678.40, and France £209,625.37. The source retailer's
country mix cannot establish national demand or causal geographic differences.
The top ten identified customers contribute 17.30% of known-customer revenue.

November 2011 has the highest full-month revenue, £1,503,866.78, up 30.63% from
October. Among adjacent complete months, growth ranges from −25.03% in April to
+43.27% in May. December 2011 is truncated and its monthly growth is not published.

Invoice mean £533.17 exceeds median £303.30; sample standard deviation is £1,780.41,
IQR £341.77, and skewness 51.08. Above-p99 invoices contribute 19.37% of gross
revenue; the mean at/below p99 is £434.24. Those are influence diagnostics, not reasons
to delete valid bulk orders. Known-customer spending median is £668.57 versus mean
£2,048.69. Calendar daily revenue std is £23,376.42; interior observed-day std is
£18,829.44, illustrating denominator sensitivity. Standard deviation is not a forecast interval.
Invoice units/value Pearson correlation is 0.883 versus rank correlation 0.839;
customer frequency/spending values are 0.553 and 0.807. These are partly mechanical
relationships, not causal effects. No unnecessary significance tests were added.

## D. Validation and data sensitivity

| Database table | Rows |
| --- | ---: |
| transactions | 536,639 |
| invoices | 25,898 |
| products | 4,070 |
| customers | 4,372 |
| countries | 38 |

Ledger customer count exceeds eligible purchaser count because customers can appear
only on ineligible lines. All classifications are retained: 524,878 completed-sale
lines, 9,251 cancellations, 1,336 stock-adjustment candidates, and 1,174 zero-value
positive lines. Line count is not order count.

All **3,982 SQL/pandas comparisons pass**, including scalar KPIs and all monthly,
country, and selling-product revenue groups. Maximum absolute difference is
1.862645149230957e−09, below the 0.000001 monetary tolerance. Counts match exactly.
Foreign-key checks, SQLite integrity, provenance, counts, and independent monthly
coverage/growth checks pass. Every one of the 14 query files executes.

Retaining eligible duplicate lines changes revenue from £10,642,110.804 to
£10,666,684.544: **+£24,573.74 (+0.2309%)**. Units increase by **15,956 (+0.2863%)**.
Distinct invoices stay at 19,960, while AOV rises by £1.231149 to £534.403033.
No unique source line key resolves whether identical rows are legitimate repetitions.

Signed cancellation movements total **−£893,979.73**. Gross plus cancellation
movements is £9,748,131.074, labelled an unmatched signed-movement sensitivity,
not accounting net revenue. The two quarantined negative-price rows total
−£22,124.12 and describe bad debt. Noncancelled negative zero-price lines remain
inventory-adjustment candidates; none is reinterpreted as a confirmed customer return.

There are 374 calendar dates and 305 dates with ledger activity. Of 69 no-record
dates, 53 are Saturdays (all Saturdays in the span). The source does not prove
closure or missing capture. Christmas 2010 has an extended gap. December 2011 and
its final midday observation are partial; the first day is also flagged as a boundary.
Calendar zeros mean no observed activity, not verified zero demand.

## E. Executed verification

- Baseline: all 23 Phase 1 tests pass before Phase 2.
- Final suite: **37 passed, 0 failed**, with warnings treated as errors, including
  all 23 unchanged baseline tests and 14 Phase 2 tests.
- Ruff lint and formatting checks pass; dependency consistency checks pass.
- Full Phase 1 integrity and independent database/analytics verification pass.
- Both notebooks execute successfully with empty starting outputs and fresh isolated
  kernels; 17 code cells complete without execution errors.
- Installation, tests, analysis, and notebook execution are repeated in a fresh
  Python 3.11 environment built from `requirements-lock.txt`.
- Full database rebuilding is checked for identical canonical schema and every-row
  contents across separate processes. Raw/processed Phase 1 artifacts stay unchanged.
- Eight plots are generated from actual data and inspected; each has a written
  interpretation. Plotly's self-contained HTML is regenerated locally and ignored by Git.

An initial database file-byte comparison failed because physical SQLite page layout
can vary with index creation order; it was replaced by a canonical structural-schema
and ordered-row comparison. No analytical discrepancy was found. Earlier long-line
lint failures in notebook prose were corrected; final checks pass. The notebook
runtime emits an informational localhost TCP encryption warning; it does not cause
execution failure. Remote CI has not run because nothing was pushed.

No blocking defects remain. See README for exact reproducible verification commands.
No test, notebook, remote CI run, or model evaluation is claimed without execution.

The full-data canonical schema/row digest before and after rebuilding is
`92d6104f8eae89cb9c6ca78a9b8f2f3508a2ce8ed24abe0b0e9ef164b3002345`.
Final review also added an invalid-positive-duplicate regression: the sensitivity
comparison reuses every Phase 1 validity rule instead of testing only sign/price.
The actual measured results are unchanged.

## F. Recommendations and remaining decisions

Technical debt: the local snapshot/rebuild model does not implement concurrent
incremental ingestion. Product labels are not a curated catalogue. Clarify service/
charge taxonomy before introducing merchandise-only metrics. Preserve the existing
audits and report the effect of any later eligibility change. Customer missingness
may create selection bias; consider identified/anonymous subgroup comparisons.

Before Phase 3 approval, decide the forecasting target's treatment of charges,
exceptional bulk-sale/cancellation pairs, missing-record calendar dates, and the
last partial day. Begin with naive and weekly seasonal-naive baselines; use expanding
chronological validation with 7-day horizons and a final held-out test. Persist
target/calendar policy alongside model metadata. Features should use shifted lags
and rolling summaries available at prediction time. Multi-step evaluation must
simulate inference rather than borrow future actuals. Compare linear regression
and random forest only after meaningful baselines; 30-day forecasts require separate
reliability evidence. One year is insufficient to establish robust annual seasonality.

These are recommendations, not Phase 3 code. Further phase work, merges, and GitHub
pushes all require the user's explicit approval.

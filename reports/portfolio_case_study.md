# Quantiva: making retail analytics traceable

[Project landing page](../README.md) · [Dashboard gallery](../docs/dashboard_gallery.md)

## Executive summary

Quantiva connects source validation, SQL reporting, exploratory statistics, customer
segmentation and evaluated forecasting in one local retail analytics workflow.
Its central result is a defensible account of observed transactions, including
where the data and models do not support stronger conclusions. A five-page
Streamlit dashboard makes those results available without requiring SQL or Python.

The project processes 541,909 real UCI source lines. It demonstrates practical
engineering and analysis for a portfolio; it has not measured commercial adoption,
cost savings or the effect of an intervention on revenue.

## Business problem

A retailer reviewing sales needs consistent answers to operational questions:
Which products and countries contribute most? How skewed are order values? Which
identifiable customers buy frequently or have not purchased recently? Can a model
forecast the next week more accurately than simply repeating last week?

Those questions depend on transaction eligibility, observation coverage and customer
identity. Quantiva exposes these assumptions rather than hiding them behind totals.

## Data source and quality

The [UCI Online Retail dataset](https://archive.ics.uci.edu/dataset/352/online+retail)
contains transactions from a UK-based non-store retailer, including wholesale customers,
between 1 December 2010 and 9 December 2011. Prices are in GBP. Attribution:
Chen, D. (2015), [DOI 10.24432/C5BW33](https://doi.org/10.24432/C5BW33), CC BY 4.0.

The actual workbook contains missing customer IDs on 135,080 lines and missing
descriptions on 1,454 lines. The final day ends at 12:50. Source documentation
does not replace empirical quality inspection or establish complete capture.

| Metric | Verified result |
| --- | ---: |
| Original source records | 541,909 |
| Cleaned ledger records | 536,639 |
| Eligible completed-sales lines | 524,878 |
| Gross eligible completed-sales revenue | £10,642,110.80 |
| Completed orders | 19,960 |
| Average order value | £533.17 |
| Units sold | 5,572,420 |
| Identifiable purchasers | 4,338 |
| Within-period repeat purchasers | 2,845 |
| Within-period repeat rate | 65.58% |

Unrounded gross eligible revenue is **GBP 10,642,110.804**; display values use cents.
Counts have different grains: lines, distinct eligible invoices and distinct
identifiable purchasers. The six segment counts below use only those 4,338 purchasers.

## Data engineering

The downloader preserves original workbook bytes and records provenance/checksums.
Cleaning retains Excel source-row identity, nullable customer IDs, original line
descriptions and transaction classifications. Missing descriptions do not invalidate
otherwise eligible amounts; anonymous purchases remain in aggregate sales.

Keep-first exact deduplication excludes 5,268 lines; two negative-price records are
quarantined. Valid negative quantities are investigated and classified, not all
discarded: cancellation, stock-adjustment candidate and zero-value categories remain
in the ledger. Completed-sales eligibility requires noncancelled positive quantities
and prices. Eligible charge/postage codes remain included; valid bulk orders are retained.

Parquet outputs and a checksum manifest precede an atomic SQLite rebuild. Foreign
keys, classification/monetary constraints and indexes constrain imports. Rebuilds
replace data rather than append duplicate imports. The [architecture](../docs/architecture.md)
and [cleaning methodology](methodology.md) explain the failure and concurrency boundaries.

## SQL analytics and exploratory analysis

Fourteen packaged SQL queries use joins, grouped aggregates, CTEs, window functions,
rankings and running totals. SQL computes amounts from integer £0.0001 units;
independent pandas aggregates use the verified Parquet line values. Reconciliation
checks scalars and every monthly/country/selling-product revenue group, including
missing-key detection: **3,982 comparisons pass**.

Exploration separates line, invoice, customer and daily-calendar grains. Means,
medians, quartiles, percentiles, variance, skewness and correlations provide context:

- AOV is £533.17 versus a £303.30 median invoice value. Large bulk orders influence
  the mean, so a “typical order” should not be described using the mean alone.
- The UK contributes 84.59% of this retailer's recorded gross revenue. This is
  concentration within the sample, not a causal geography effect or market-size estimate.
- Keeping eligible duplicate repeats adds £24,573.74, about 0.23%, without changing
  the distinct order count. This quantifies the deduplication assumption.
- November 2011 is the highest complete month. Partial December 2011 must not be
  interpreted as a full-month decline. Absent dates mean zero observed sales,
  not independently established zero demand.

[Measured findings](findings.md) contain the distributions, sensitivities and their
interpretations. [The notebooks](../notebooks) show executable exploration and diagnostics;
correlations describe associations rather than causes.

## Customer intelligence

RFM summarizes identifiable eligible purchasers. Recency is days since the last
eligible purchase relative to the day after the selected end date; frequency is
distinct eligible invoices; monetary value is gross eligible GBP spend. Quintile
thresholds respect ties, sparse distinct values use spaced ranks, and constant values
receive neutral score 3. First-match rules create six exclusive descriptive segments.

| Segment | Customers |
| --- | ---: |
| Champions | 911 |
| At Risk | 513 |
| Hibernating | 1,214 |
| Loyal Customers | 381 |
| New Customers | 515 |
| Potential Loyalists | 804 |

Full-scope reference date: **10 December 2011**. Scores and counts can change when
the date/country cohort changes. These labels identify groups to investigate;
“At Risk” is not a validated churn probability, and “New Customers” does not prove
the customer's first-ever purchase. Anonymous customers cannot be segmented.

![Customer purchasing patterns colored by descriptive RFM segment](figures/dashboard_polish_customer_patterns_light.png)

Log monetary axes reveal dense lower-spending groups while retaining outliers.
Hover values stay in the selected display currency; source scoring remains GBP.

## Forecasting: testing complexity against simple baselines

The target is daily gross eligible completed-sales GBP, including eligible charges.
Both source boundary dates are excluded conservatively; 372 modeled dates span
2 December 2010–8 December 2011. Calendar gaps remain zero recorded revenue.

| Window | Inclusive dates | Procedure |
| --- | --- | --- |
| Initial training | 2010-12-02 to 2011-08-18 | Historical context and initial fitting |
| Validation | 2011-08-19 to 2011-10-13 | Eight expanding weekly origins |
| Held-out test | 2011-10-14 to 2011-12-08 | Eight weekly origins; fixed learned weights |

Known calendar predictors combine with lagged revenue and shifted rolling statistics.
Preprocessing is fitted within each training window. Seven-day recursive inference
appends earlier predictions to context for later steps; future actuals from the
same forecast window are never supplied as features. During test, context advances
between completed weeks while model weights remain fixed.

Naive and weekly seasonal naive provide essential benchmarks. Linear Regression
offers a linear comparison; Random Forest captures nonlinear interactions with
120 trees, depth 6, minimum leaf size 5 and seed 42. These settings remain unchanged.

| Model | Validation MAE (GBP/day) | Held-out MAE (GBP/day) |
| --- | ---: | ---: |
| Naive | 24,181.77 | 20,978.67 |
| Weekly Seasonal Naive | 15,580.52 | 11,250.17 |
| Linear Regression | 12,792.97 | Not evaluated |
| Random Forest | 11,431.53 | 12,344.71 |

Random Forest is selected by lowest validation MAE before the held-out evaluation.
Weekly Seasonal Naive wins held-out MAE; the selection is not revised after seeing
test results. No held-out Linear Regression result is invented. RMSE and WAPE
complement MAE in the [evaluation report](model_evaluation.md).

The forest's held-out underprediction is consistent with large late-period spikes
and trees' limited extrapolation, while last-week values adapt to recent levels.
This is a plausible explanation supported by diagnostics, not an isolated causal
experiment proving why one model won. Eight origins provide limited stability evidence.

Current code behavior and reproduction verify validation-only execution. They do
not independently prove that earlier manual decisions were uninfluenced by previously
seen test outcomes. The overwritten selection file is not an immutable experiment record.

![Held-out comparison showing the weekly baseline has the lowest MAE](figures/dashboard_polish_evaluation_dark.png)

This actual dashboard capture displays illustrative ZAR; the table above uses
authoritative GBP. A fixed positive multiplier changes monetary error units but
preserves WAPE and ranking. After evaluation, a separate final refit through
8 December 2011 supplies a **9–15 December 2011 historical demonstration**. It is
not a live forecast and has no calibrated prediction intervals.

## Dashboard and business communication

Overview summarizes performance; Sales Analytics investigates time/products/geography;
Customer Intelligence explains known-customer behavior and RFM; Predictive Analytics
exposes baseline comparisons and errors; Data Quality explains provenance and exclusions.
Filters identify scope, and full-data pages state when commercial filters do not apply.

Dark/light themes and GBP/ZAR preferences persist within the session. ZAR defaults
to a fixed illustrative ECB cross-rate, £1 = R12.708021 dated 8 December 2011.
It is neither actual historical ZAR transactions nor a transaction-date conversion.
All underlying calculations, model evaluation and artifacts remain GBP.

## Engineering quality and reproducibility

The 105-test suite covers fixtures, regressions, provenance, chronological inference,
artifact failures, dashboard controls and presentation consistency. Ruff checks lint
and formatting. GitHub Actions exercises fixtures on Windows without downloading data.
Separate actual-data checks cover seven source/ledger conditions, 3,982 SQL/pandas
comparisons, 30 forecast conditions and 63 dashboard conditions. Browser evidence
checks actual pages, themes, currencies, filters and responsive layouts.

The [reproduction guide](../docs/reproducibility.md) supplies locked installation,
official source download, checksum, regeneration, notebook and startup commands.
[Phase 5 progress](phase_5_progress.md) records which steps were rerun in a fresh
environment and how historical evidence was protected.

## Challenges, trade-offs and limitations

SQLite and local artifacts keep the project inspectable and free, while imposing
single-process rebuild and finite-dataset assumptions. Gross eligible sales provide
a reproducible operational measure; matched returns, profit and settled revenue
would require additional source information. Fixed-point SQL and floating-point
pandas require explicit reconciliation tolerances.

Approximately one year from one retailer cannot establish durable annual seasonality
or population-wide retail patterns. Missing identifiers can bias customer findings.
Large orders, service codes and unknown gap causes complicate forecasting. RFM is
descriptive; prediction intervals, 30-day forecasting, production authentication
and monitoring are future work. No tested commercial intervention or causal uplift
is claimed.

## Lessons demonstrated and portfolio value

Quantiva demonstrates that reliable reporting starts with grain, eligibility and
lineage; that independent calculations strengthen trust; and that a simple baseline
can generalize better than a more complex candidate. It connects Python/SQL data
engineering, statistical interpretation, forecasting evaluation and stakeholder-facing
presentation without hiding unfavorable results. The contribution is a reproducible,
reviewable analytical system and a credible explanation of its limits.

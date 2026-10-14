# Phase 3 — forecasting milestone and verification evidence

> Historical technical evidence: measurements, test counts and verification scope
> describe the implementation milestone recorded here, not a new execution.
> Later technical corrections are identified in the follow-up evidence.

## A. Technical scope

This milestone extends the verified ingestion and SQL analytics pipeline with
chronological seven-day forecasting. Raw/processed datasets, model binaries,
database files and virtual environments are regenerated locally and excluded
from versioned source; small measured reports and the executed notebook provide evidence.

## B. Implementation

Created modules: `forecast_series.py` (verified target/calendar), `features.py`
(historical predictors), `forecasting.py` (baselines and recursive regressors),
`forecast_evaluation.py` (chronological folds and metrics), `forecast_experiment.py`
(validation-only selection, test evaluation, sensitivities and final refit),
`model_artifacts.py` (trusted persistence), and `forecast_report.py` (measured reports).
Existing ingestion, cleaning, SQLite schema, packaged SQL and KPI policies are reused.

Modified configuration exposes forecasting/model directories; the CLI adds
`forecast-prepare`, `forecast-train`, `forecast-compare`, `forecast`, and
`forecast-verify`. `scripts/verify_forecasting.py` checks report lineage, chronology,
metric accounting and saved inference. The notebook runner accepts `--phase 3`.
Added sklearn/SciPy/joblib dependencies and a tested Python 3.11 lock. Ignore rules
exclude derived forecasting data, binary models and the fresh verification environment.

Created this technical report, methodology,
model evaluation, JSON results/verification, nine forecast CSV evidence tables,
seven PNG figures and `03_forecasting_experiments.ipynb`. README documents reproduction
and actual results. Three test modules add 22 cases to the 42-test baseline.
No Phase 4 dashboard, Phase 5 portfolio work, deep learning or 30-day model is added.

## C. Measured forecasting results

Each model has 56 scored calendar dates in validation; only the selected candidate
and required baselines are evaluated on the final 56 test dates.

| Model | Validation MAE GBP | Validation RMSE GBP | Validation WAPE | Test MAE GBP | Test RMSE GBP | Test WAPE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Naive | 24,181.77 | 30,305.71 | 74.80% | 20,978.67 | 28,049.45 | 45.33% |
| Weekly seasonal naive | 15,580.52 | 21,661.32 | 48.19% | 11,250.17 | 16,218.79 | 24.31% |
| Linear Regression | 12,792.97 | 18,258.31 | 39.57% | Not evaluated | Not evaluated | Not evaluated |
| Random Forest | 11,431.53 | 17,764.13 | 35.36% | 12,344.71 | 17,396.90 | 26.68% |

Random Forest wins validation MAE and remains the frozen candidate. Weekly seasonal
naive beats it on all three held-out metrics. No general machine learning superiority
claim is supported, and the candidate is not switched after seeing test outcomes.

Selected test MAE by horizon, with eight observations each:

| Lead (calendar days) | MAE GBP |
| --- | ---: |
| 1 | 8,249.99 |
| 2 | 0.00 |
| 3 | 14,091.54 |
| 4 | 20,367.62 |
| 5 | 13,504.20 |
| 6 | 16,941.09 |
| 7 | 13,258.50 |

Origins are Thursdays, so lead two is always Saturday; the zero error reflects
the observed schedule. These leads do not isolate an independent horizon effect.
Validation fold MAE spans £6,772.46–£20,042.77, showing instability across weeks.
Held-out bias is −£6,379.57/day, indicating underprediction. The largest miss is
14 November (actual £114,237.40, predicted £50,286.40). See `model_evaluation.md`
and prediction/fold/horizon CSVs for complete accounting.

## D. Data and statistical findings

The full £10,642,110.804 gross target reconciles with Phase 2 daily SQL. Excluding
the uncertain first boundary and partial last day leaves 372 dates, 2 December 2010
through 8 December 2011, and £10,382,433.034. Source coverage has 305 eligible-sales
days, zero other-ledger-only days, and 69 gaps including 53 Saturdays. Gaps carry
zero observed revenue, not proof of zero demand. Holiday gaps and boundary policies
are explicit; the final month is not treated as complete.

Development autocorrelation at lag seven is 0.598, supporting a weekly comparator.
Only about one annual cycle limits recurring-seasonality claims. Initial-training
p99 is £71,392.92; three validation days above it contribute 51.71% of forest squared
error. Its below-threshold MAE is £9,040.34 on 53 dates, an influence diagnostic;
no valid orders or training targets are deleted.

The calendar sensitivity learns Saturday inactivity from initial training only,
excludes it from regression fitting and schedules zeros without future activity flags.
Forest validation MAE becomes £11,716.15, so it does not improve the primary candidate.
Excluding DOT, POST, AMAZONFEE and BANK CHARGES gives forest MAE £11,346.99 on a
different target. M remains ambiguous and included. Different target denominators
prevent interpreting those errors as an improvement in primary gross forecasting.

All lag/rolling features stop at t−1 or earlier. Within each seven-day window,
unavailable future observations are replaced by earlier predictions. Each validation
fit uses only preceding dates; test weights remain fixed through 13 October, with
past observed context advancing between completed weeks. Selection, features, seed,
policies and hyperparameters are fixed in the committed execution path. This audit
does not independently establish whether earlier manual decisions were influenced
by already viewed test results; the overwritten selection file is not an immutable
historical experiment record. The final
deployment refit through 8 December is separately labeled and has no new unbiased
performance estimate. Its 9–15 December 2011 output is a retrospective demonstration.

## E. Verification evidence

Fresh Windows Python 3.11.9 environment `.venv-phase3` was installed from the lock
and the package installed editable without dependency resolution or build isolation.
The original 64 tests passed with warnings treated as errors, including all 42 existing
regression tests. Ruff lint and formatting pass; pip reports no broken requirements.
The initial feature test exposed only a DatetimeIndex frequency-metadata difference;
its assertion now checks equivalent dates/values without demanding identical optional
frequency metadata. No outstanding test failure remains.

Full-data verification passes all seven Phase 1 checks. Phase 2 executes all 14 SQL
queries and passes 3,982 SQL/pandas comparisons, integrity, foreign keys and lineage.
Forecast verification passes 30 checks with zero failures: provenance and policy,
224 validation rows, 168 held-out rows, all metrics/horizons, frozen test weights,
pretest selection, metadata hash, trusted reload and deterministic future inference.
Unchanged held-out prediction CSV bytes were reproduced from the fresh environment.
Separate CLI/Python processes load the persisted model and produce the same seven
finite forecasts, without new training or future transactions.

The Phase 3 notebook clears outputs and executes successfully in an isolated fresh
kernel. It reproduces validation, audits fixed held-out evidence, checks leakage,
analyzes sensitivities and reloads inference. Existing Phase 1/2 notebook sources are
preserved; they were verified previously and are not re-executed in this phase.
All seven PNGs were visually inspected; demonstration date labels were corrected
for readability. Self-contained Plotly HTML is regenerated locally and ignored.

| Phase 3 requirement | Verified evidence |
| --- | --- |
| Traceable daily target and unchanged eligibility | Source/ledger hashes and daily SQL comparison |
| Explicit calendar, gaps and boundaries | Series metadata, methodology and coverage tests |
| Seven-day naive and weekly baselines | Full-horizon fixtures and measured comparisons |
| Leakage-safe features and recursive inference | Adversarial future perturbation and spy-estimator tests |
| OLS and seeded Random Forest | Shared fitted pipeline and deterministic test fixtures |
| Chronological validation and validation-only code selection | Eight expanding origins; current execution selects before test; earlier manual decisions not independently verified |
| Final held-out candidate plus baselines | Fixed-weight 56-day test and complete horizon accounting |
| MAE, RMSE, WAPE and zero handling | Hand-calculated metrics tests, recomputed report checks |
| Statistical diagnostics and sensitivities | Development diagnostics, three labeled validation experiments |
| Trusted persistence, metadata and fresh inference | Checksums, dependency checks, tampering/trust tests and separate processes |
| Executable notebook, seven charts, documentation | Fresh-kernel execution, visual QA, README and reports |
| Preserved Phase 1/2 functionality | Full 64-test suite and full-data reconciliation |

The completion audit reproduced the full workflow in a fresh GitHub checkout and
executed all three notebooks. It confirmed a constant-history diagnostic defect;
the follow-up corrects undefined autocorrelations to JSON null and adds two regression
cases. See `phase_3_audit_followup.md` for current verification evidence and remaining
limitations; the 64-test counts above describe the original implementation baseline.

Verification results describe the tested implementation and its documented limits.

## F. Recommendations and limits

Weekly seasonal naive provides an essential comparator. Keep validation
selection, held-out metrics and full-history deployment cutoff visibly separate.
Consume the reusable inference frame with model/version, origin, horizon, GBP,
training cutoff and retrospective label; do not infer current business conditions.

Remaining limitations: one retailer, short history, unknown gap causes, charge scope,
wholesale spikes, correlated predictors, limited origins and weekday/lead confounding.
There are no calibrated prediction intervals, production monitoring or concurrent
artifact updates. Direct multi-horizon models, stronger business-calendar evidence
and a new independent test period could be future investigations, requiring separate
scope and honest evaluation. This milestone contains forecasting rather than a dashboard.

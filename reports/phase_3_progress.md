# Phase 3 progress and completion evidence

## A. Git status and approved workflow

Baseline: `6f8985d9d93bebe0ba0953f992efd23b9c5bbb61`, following Phase 1 commit
`17755ee` and Phase 2 implementation `d18e571`. Local and remote main were synchronized
at the baseline on inspection. No Phase 3 commits were on local or remote main.
All existing uncommitted Phase 3 implementation was preserved when creating `phase-3`
from the active `phase/03-machine-learning` branch. That older branch remains intact.

The user's subsequent workflow explicitly authorizes committing, pushing `phase-3`,
and opening a draft PR targeting main. It replaces the original Phase 3 specification's
branch name and no-commit/no-push restriction. Root `AGENTS.md` records this change;
no prior root instructions existed to overwrite. Future branches are `phase-4`,
`phase-5`, etc. Main is not modified, merged, force-pushed, or rewritten.

This report is part of the proposed implementation commit. Its final SHA, remote
verification and draft PR link are reported after publication in the task's final
message, avoiding a self-referential commit hash. Only source, tests, requirements,
documentation, executed notebook and small measured report evidence are proposed.
Raw/processed datasets, model binaries, database files, virtual environments,
personal paths and credentials are excluded. The working tree is checked after commit.

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

Created `PHASE_3_SPECIFICATION.md`, root `AGENTS.md`, this report, methodology,
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

## E. Verification and acceptance criteria

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

No known blocking implementation defect remains. This is completion evidence for
review, not user approval of Phase 3 or authorization to begin Phase 4.

## F. Recommendations and limits

Phase 3 is ready for review as a defensible portfolio experiment. Weekly seasonal
naive deserves prominent comparison in any eventual dashboard. Keep validation
selection, held-out metrics and full-history deployment cutoff visibly separate.
Consume the reusable inference frame with model/version, origin, horizon, GBP,
training cutoff and retrospective label; do not infer current business conditions.

Remaining limitations: one retailer, short history, unknown gap causes, charge scope,
wholesale spikes, correlated predictors, limited origins and weekday/lead confounding.
There are no calibrated prediction intervals, production monitoring or concurrent
artifact updates. Direct multi-horizon models, stronger business-calendar evidence
and a new independent test period could be future investigations, requiring separate
scope and honest evaluation. Phase 4 and Phase 5 remain unstarted.

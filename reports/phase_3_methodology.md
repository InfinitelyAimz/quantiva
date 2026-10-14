# Phase 3 methodology

## Target, traceability, and calendar

Predict seven calendar days of daily gross eligible completed-sales revenue in GBP.
Reuse Phase 1 eligibility and the verified ledger; aggregate quantity times unit
price in integer £0.0001 units before conversion to GBP. Cancellation movements
remain outside this gross target. Every daily value reconciles with packaged Phase 2
SQL, and raw/ledger/series hashes link model evidence to its source. The source total
remains £10,642,110.804; forecasting does not redefine business KPIs.

The 374 source calendar dates contain 305 eligible-sales dates, zero dates with only
other ledger activity, and 69 dates without records, including 53 Saturdays.
The baseline fills absent records with zero **observed revenue**, not zero demand.
The Christmas/New Year gap from 24 December 2010 through 3 January 2011 and spring
gaps may reflect closures or recording coverage. Holiday demand is not identifiable
from those records, so no externally guessed holiday indicator is used.

Source timestamps begin at 08:26 on 1 December 2010 and end at 12:50 on 9 December
2011. The last day is partial; the first day's completeness is uncertain rather than
proven incomplete. Exclude both boundary days conservatively, retain flags in the
series, and model 372 daily dates from 2 December 2010 through 8 December 2011.
Excluded revenue is £259,677.77, leaving £10,382,433.034 for modeling. No partial
December total is presented as a complete month.

## Available features and multi-step inference

For a target date t, feature construction uses these availability rules:

| Predictor | Definition and availability |
| --- | --- |
| weekday | Date t; known in advance; six one-hot indicators with Monday reference |
| month_sin, month_cos | sin/cos of 2π × month(t)/12; known in advance |
| day_of_month | Date t; known in advance |
| lag_1, lag_7, lag_14, lag_28 | Revenue at t minus the indicated calendar days |
| mean_7, mean_14, mean_28 | Means of the indicated windows ending at t−1 |
| std_7 | Sample standard deviation of seven dates ending at t−1 |
| trend_7_28 | mean_7 minus mean_28; historical level difference, not a causal trend |

The first 28 dates provide feature context; the first fitted regression target is
30 December 2010. Scale numeric inputs using only the current training window.
No target-day activity flags, transaction/customer counts, or future invoices enter
the pipeline. Tests perturb future targets and future activity flags to detect leakage.

Recursive forecasting fits one next-day regressor and invokes it seven times.
After each step, append the prediction to context. Thus step two's lag_1 is step one's
prediction, and its rolling windows also include that prediction. Unknown future
actuals never enter the same seven-day window. This matches deployment exactly.
Errors can accumulate recursively; a direct approach would fit separate models for
each horizon and needs a separate evaluation. The limited sample favors this compact
initial experiment. Predictions clip at zero under one declared policy everywhere;
no 30-day performance or confidence interval is claimed.

The naive baseline repeats the last calendar observation, including a zero gap.
Weekly seasonal naive copies the corresponding date seven days earlier. Both predict
the entire horizon deterministically. Regression training requires 56 calendar days;
inference requires 28, while the baselines need one and seven respectively.

## Models and chronological evaluation

Linear Regression minimizes squared residuals with an intercept. Its additive
relationship is an approximation: correlated lag/rolling features make individual
coefficients unstable, spikes have high influence, and time dependence weakens
independence assumptions. Numeric coefficients represent GBP change per training
standard deviation holding other predictors fixed; weekday coefficients compare with
Monday. They describe associations, not causal effects. No inferential p-values or
independent-normal-error claim is made. See the [official OLS documentation](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html).

Random Forest averages 120 bootstrap trees, each with maximum depth 6 and minimum
leaf size 5. It uses all features at each split, squared-error criterion, seed 42,
and one worker for repeatability. Trees partition feature space and capture nonlinear
interactions; averaged leaves can smooth noise but do not reliably extrapolate a new
revenue regime. Depth/leaf restrictions reduce overfitting without making it
impossible. Scaling is retained in the shared pipeline, though trees do not require
it. Impurity importance is a model diagnostic affected by correlated predictors,
not evidence of causation. See the [official forest documentation](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html).

Reserve the last 56 dates for test and the preceding 56 for validation, leaving
260 initial-training dates. Splits use dates and length, not revenue outcomes:

| Segment | Inclusive dates | Procedure |
| --- | --- | --- |
| Initial training | 2010-12-02–2011-08-18 | Historical context and fitting |
| Validation | 2011-08-19–2011-10-13 | Eight expanding origins, seven dates each |
| Held-out test | 2011-10-14–2011-12-08 | Eight origins, seven dates each; fixed weights |

At each validation origin, refit preprocessing and the estimator on earlier history.
Already completed validation weeks are observable history at later origins; their
targets are never used to predict their own window. Selection minimizes pooled
primary validation MAE across 56 dates, with alphabetical model-name tie breaking.
No search or test-based calendar/outlier/feature optimization occurs in the committed
execution path. Code review and reproduction do not independently establish whether
earlier manual choices were influenced by already viewed test outcomes. The selection
file is overwritten on reruns and is not an immutable historical experiment record.

Write the frozen selection before computing test results. Refit the selected model
through 13 October for test, then freeze learned weights across all test origins.
Lag context advances after each completed week using observed past test dates,
matching weekly operation. Those values are never used within their own predicted
week or to refit weights. Evaluate only the selected candidate and both required
baselines. Subsequent deterministic reproductions use unchanged choices; they are
verification, not new tuning cycles. After evaluation, refit the selected configuration
through 8 December for demonstration inference. Metadata separates this deployment
cutoff from the pretest evaluation cutoff; deployment has no separate unbiased score.

## Metrics, diagnostics, and controlled sensitivities

MAE is mean absolute daily error in GBP. RMSE is the square root of mean squared
daily error in GBP and emphasizes large misses. WAPE is 100 × sum absolute errors /
sum absolute actual GBP across the scored dates. It is undefined when that entire
denominator is zero; such results are null. Daily zero values remain valid. Bias is
mean prediction minus actual GBP; negative bias means underprediction. Do not use
MAPE with these zero dates. Compare models on identical targets and dates.

Development-only daily mean is £24,655.08, median £24,708.73, standard deviation
£18,988.99, and maximum £109,553.90. Lag-7 autocorrelation is 0.598 versus 0.350 at
lag 1, suggesting useful weekly structure without proving a causal calendar effect.
Trend and weekday activity confound correlations. Approximately one year is too
short to establish recurring annual seasonality from month features.

Undefined autocorrelations are represented as JSON `null`. Correlation needs varying
paired observations: constant-zero and constant-positive histories have zero variance,
so their autocorrelations cannot be estimated. Null is not a zero correlation estimate
or evidence of no temporal dependence. Too few varying paired observations can also
make an autocorrelation undefined.

Run three validation-only sensitivity analyses and preserve the primary selection:

1. Learn inactive weekdays once from initial training: require at least eight dates
   and no ledger activity on every occurrence. Only Saturday qualifies. Exclude
   those dates from regression fitting and schedule zero predictions for them;
   the naive model uses its most recent active observation. Score the same seven
   calendar dates and never inspect future activity to decide a day's status.
2. Set an extreme threshold using initial-training p99 (£71,392.92). Three validation
   days exceed it and account for 51.71% of forest squared error. Score the other
   53 dates separately to quantify influence. Delete no training targets or valid
   orders, and never optimize a threshold on test.
3. Exclude exactly DOT, POST, AMAZONFEE and BANK CHARGES in a separate target.
   M (Manual) stays because its meaning is ambiguous. Forest validation MAE is
   £11,346.99 on this alternative target, versus £11,431.53 on the primary target;
   different target totals/denominators prevent calling this a primary improvement.

The calendar alternative gives forest MAE £11,716.15, providing no improvement for
that candidate. Below-threshold forest MAE is £9,040.34, illustrating spike influence
rather than an alternative operational accuracy claim.

Forest validation fold MAE ranges from £6,772.46 to £20,042.77. Its held-out bias is
−£6,379.57/day, with the largest miss on 14 November: £114,237.40 actual against
£50,286.40 predicted. Horizon errors are nonmonotonic: all eight origins are Thursdays,
so horizon 2 always lands on Saturday and has zero error. Lead and weekday are
confounded. Eight observations per horizon cannot establish a stable degradation
curve, normal residuals, or general performance superiority.

## Persistence, reproducibility, and interfaces

`forecast_series` verifies source lineage and SQL agreement; `features` creates
historical-only predictors; `forecasting` fits and predicts; `forecast_evaluation`
owns splits and metrics; `forecast_experiment` coordinates frozen experiments;
`model_artifacts` saves/loads trusted artifacts; `forecast_report` publishes evidence.
The CLI exposes preparation, training, comparison, inference and artifact checks;
`scripts/verify_forecasting.py` audits all 30 evidence checks independently of the
training orchestration, though it reuses the tested metric function.

Ignored `data/models` stores joblib model/preprocessing, CSV historical context,
metadata JSON and checksum manifest. Metadata records model version 3.0.0, both
cutoffs, feature availability, policies, splits, hyperparameters, seed, validation/test
metrics, dependencies and source hashes. Require explicit trust in the Python API,
validate checksums before deserialization, and enforce dependency compatibility.
Only the CLI's own configured local artifact directory is loaded as trusted.
Checksums detect alteration but do not authenticate a malicious pickle. See the
[official persistence guidance](https://scikit-learn.org/stable/model_persistence.html).

The Python 3.11 lock supports rebuilding an isolated Windows environment. Models are
regenerated rather than committed. Fresh-process inference reloads and checks identical
finite seven-date output, ending 15 December 2011. These are historical demonstrations,
not live forecasts. Concurrent artifact replacement is unsupported. Dashboard
integration should consume the reusable inference frame and display policies, origin,
cutoff and baseline results; no dashboard is implemented in this phase.

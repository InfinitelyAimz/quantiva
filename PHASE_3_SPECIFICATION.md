# QUANTIVA — PHASE 3 IMPLEMENTATION SPECIFICATION
## Machine Learning, Time-Series Forecasting & Model Evaluation

### 1. Role and Project Context

Act as a senior data scientist, machine learning engineer, Python developer, data engineer, and technical mentor.

We are continuing development of **Quantiva — Retail Intelligence & Predictive Analytics**, an end-to-end data science portfolio project.

The objective is to demonstrate professional data science, machine learning, statistical analysis, SQL, and data engineering skills relevant to Junior Data Scientist, Data Analyst, and Junior Data Engineer positions.

The project is being developed locally on Windows using Python 3.11, SQLite, SQLAlchemy, pandas, NumPy, scikit-learn, SciPy, Matplotlib, Plotly, pytest, and Git.

GitHub repository:

https://github.com/InfinitelyAimz/quantiva

The authoritative requirements document is:

`PROJECT_SPECIFICATION.md`

Phase 1 and Phase 2 are complete, verified, committed, merged into `main`, and pushed to GitHub.

The current verified `main` commit is:

`6f8985d9d93bebe0ba0953f992efd23b9c5bbb61`

Treat this as the baseline, subject to verification against the actual repository.

We are beginning:

**Phase 3 — Machine Learning & Sales Forecasting**

Do not begin Phase 4 or Phase 5.

---

### 2. Git and Repository Management

Before implementation:

1. Inspect the existing repository.
2. Verify the current branch and Git status.
3. Confirm the Phase 1 and Phase 2 commits are present.
4. Confirm local `main` and `origin/main` are synchronized.
5. Run the existing automated tests.
6. Preserve all existing code, data-processing rules, documentation, and Git history.

Create a new development branch:

`phase/03-machine-learning`

Branch from the verified `main` branch.

Follow the existing naming convention:

- `main`
- `phase/01-foundation`
- `phase/02-analytics`
- `phase/03-machine-learning`
- `phase/04-dashboard`
- `phase/05-portfolio`

If the execution environment requires another naming convention, explain the restriction.

Do not overwrite existing branches.

Do not merge, push, delete branches, force-push, or rewrite history without my approval.

Do not commit changes without my explicit approval.

Save this complete specification as:

`PHASE_3_SPECIFICATION.md`

---

### 3. Existing Data and Analytical Foundation

Quantiva currently processes the UCI Online Retail dataset.

The dataset contains approximately 541,909 raw transaction lines from December 2010 through December 2011.

Phase 1 established reproducible ingestion, cleaning, transaction classification, data provenance, and Parquet outputs.

Phase 2 established a relational SQLite database, SQL analytics, statistical analysis, independent reconciliation, and reproducible visualizations.

Previously verified results include:

| Metric | Result |
|---|---:|
| Gross completed-sales revenue | £10,642,110.804 |
| Completed orders | 19,960 |
| Eligible completed-sale lines | 524,878 |
| Identifiable customers | 4,338 |
| SQL/pandas reconciliations | 3,982 passed |
| Final automated tests | 42 passed |

These values are historical Phase 2 findings, not forecasting results.

Inspect the actual repository and reports before using them.

Do not hardcode historical results into the forecasting pipeline.

---

### 4. Primary Phase 3 Objective

Develop a scientifically defensible machine learning pipeline that predicts future daily retail revenue.

The primary forecast horizon is:

**7 calendar days**

The system must:

1. Build a reproducible daily revenue time series.
2. Define and document the forecasting target.
3. Handle calendar gaps and incomplete observations.
4. Establish simple forecasting baselines.
5. Engineer valid time-dependent features.
6. Train regression-based forecasting models.
7. Evaluate models using chronological validation.
8. Prevent data leakage.
9. Compare machine learning models against baselines.
10. Produce reproducible model evaluation reports.
11. Save suitable model artifacts.
12. Support genuine future inference.
13. Provide outputs suitable for integration into the Phase 4 dashboard.

Do not claim that machine learning improves forecasting unless empirical results demonstrate an improvement.

---

### 5. Forecasting Target and Revenue Policy

The initial target is:

**Daily gross eligible completed-sales revenue, expressed in GBP.**

Use the existing Phase 1 and Phase 2 completed-sales eligibility rules.

Do not silently change business KPI definitions.

#### Target requirements

- Aggregate eligible completed-sale transactions by calendar date.
- Preserve monetary precision appropriately.
- Document the aggregation process.
- Distinguish gross sales from cancellation-related movements.
- Do not label the target as accounting net revenue.
- Preserve source-data traceability.
- Ensure target calculations reconcile with existing Phase 2 analytics.

#### Non-merchandise codes

The dataset includes charges and nonstandard stock codes such as:

- DOT
- POST
- M
- AMAZONFEE
- BANK CHARGES

For the primary experiment, preserve the existing completed-sales eligibility policy, including eligible charges, to maintain consistency with Phase 2.

However, investigate how these records affect forecasting.

If useful, create a separate documented sensitivity experiment excluding clearly identifiable service or charge codes.

Do not redefine the primary target without approval.

#### Extreme transactions

The dataset includes unusually large orders and possible reversal-related activity.

Investigate extreme daily revenue values and their influence on model performance.

Do not automatically delete valid large orders.

Any outlier adjustment must be treated as a separate experiment and documented.

---

### 6. Calendar Coverage and Missing Dates

Phase 2 identified:

- 374 calendar dates.
- 305 dates with recorded ledger activity.
- 69 dates without recorded transactions.
- 53 missing Saturdays.
- A partial final observation day.
- A truncated December 2011.

These issues must be handled explicitly.

#### Required calendar investigation

Determine:

1. Which dates contain completed-sales activity.
2. Which dates contain other ledger activity but no eligible sales.
3. Which dates have no records at all.
4. Whether missing dates follow recurring weekday patterns.
5. Whether holidays or unusual observation gaps affect the series.
6. Whether the first and final observation dates are complete.

#### Calendar policy

Do not assume that every missing date represents genuine zero customer demand.

For the initial baseline, a zero-observed-revenue calendar series may be used if clearly labeled as an observed-activity assumption.

Also evaluate an alternative calendar policy where appropriate, such as excluding structurally unobserved days from the modeled observation schedule.

Avoid using future knowledge to identify whether an individual prediction date should be considered active.

Any business-calendar rule used at prediction time must be based on information available at that time.

#### Boundary dates

Exclude or explicitly flag the final partial observation day from model training and evaluation.

Investigate whether the first observation day should also be excluded.

Document the exact date range used for forecasting.

Do not treat the partial final month as a complete month.

---

### 7. Forecasting Strategy

Implement a genuine multi-step forecasting strategy.

The model must predict the next seven calendar days using only information available at the forecast origin.

A model that predicts tomorrow using yesterday's actual revenue is not automatically capable of predicting seven days ahead.

#### Acceptable approaches

Investigate and select an appropriate strategy, such as:

- Recursive forecasting.
- Direct multi-horizon forecasting.
- Another clearly justified multi-step approach.

Explain the selected approach.

For recursive forecasting, future lagged features must use prior predictions rather than unavailable future actual revenue.

For direct forecasting, each horizon must use features available at the forecast origin.

Do not use actual revenue from the validation or test forecast window as an input to subsequent predictions within that same window.

Ensure the inference procedure matches the procedure used during evaluation.

---

### 8. Baseline Forecasting Models

Implement simple forecasting baselines before machine learning.

#### Required baselines

**Baseline A — Naive Forecast**

Use an appropriate most-recent-observation approach.

Document how missing calendar dates affect the baseline.

**Baseline B — Weekly Seasonal Naive**

Use the corresponding day from the previous week, where appropriate.

Document any handling of missing observations and calendar gaps.

Consider an additional simple rolling-average baseline if useful.

#### Baseline requirements

- Forecast all seven days.
- Use only historical information.
- Support repeated rolling-origin evaluation.
- Produce deterministic predictions.
- Handle insufficient history safely.
- Record baseline assumptions.

These baselines establish the performance that machine learning must beat to justify its complexity.

---

### 9. Feature Engineering

Create a dedicated, reusable forecasting feature pipeline.

#### Calendar features

Consider:

- Day of week.
- Month.
- Day of month.
- Week of year.
- Weekend indicator.
- Known calendar or holiday indicators where justified.

#### Historical revenue features

Consider:

- Lag 1.
- Lag 7.
- Lag 14.
- Lag 28.
- Rolling 7-day mean.
- Rolling 14-day mean.
- Rolling 28-day mean.
- Rolling standard deviation.
- Historical revenue trend indicators.

#### Leakage prevention

All historical revenue features must use information available at prediction time.

Use shifted historical observations before calculating rolling features.

Do not calculate rolling statistics that include the target day's actual revenue.

Do not use future transaction counts, future invoice values, future customer counts, or future observed-sales indicators.

Document the feature availability of every predictor.

Avoid unnecessarily large feature sets given the limited dataset.

Implement tests specifically designed to detect temporal leakage.

---

### 10. Machine Learning Models

Implement and compare:

1. Linear Regression.
2. Random Forest Regressor.

Use scikit-learn.

#### Linear Regression

Use this as an interpretable statistical learning baseline.

Explain:

- The model's assumptions.
- How coefficients should be interpreted.
- Limitations caused by correlated lag features.
- Sensitivity to extreme observations.

#### Random Forest Regression

Use this to investigate nonlinear relationships.

Explain:

- Ensemble learning.
- Decision-tree behavior.
- Nonlinear feature interactions.
- Overfitting risks.
- Why more complex models do not necessarily forecast better.

#### Training requirements

- Use deterministic random seeds.
- Document model hyperparameters.
- Keep preprocessing within the reproducible pipeline.
- Avoid training on validation or test targets.
- Do not tune against the final held-out test set.
- Avoid excessive hyperparameter searches.

Prioritize correct evaluation over model complexity.

Do not introduce neural networks, LSTMs, transformers, or deep learning during Phase 3 unless explicitly approved.

---

### 11. Chronological Training and Validation

Do not use random train/test splitting.

Use chronological evaluation.

#### Required approach

Implement expanding-window or rolling-origin validation.

Each validation origin must:

1. Have a clearly defined historical training window.
2. Forecast the next seven calendar days.
3. Use only information available at that origin.
4. Compare predictions with the corresponding actual observed values under the documented calendar policy.
5. Record results for every horizon.

#### Final test period

Reserve a final contiguous, untouched period for evaluation.

Prefer a period containing multiple seven-day forecast origins, while preserving enough historical data for training.

Choose exact dates based on the dataset and document the reasoning.

Do not use the held-out test period for:

- Feature selection.
- Hyperparameter tuning.
- Calendar-policy optimization.
- Outlier-policy optimization.
- Model selection.

Select the final candidate using validation performance.

Evaluate the selected candidate and required baselines once on the untouched test period.

Explain any limitations caused by the short historical window.

---

### 12. Forecasting Evaluation Metrics

Calculate:

- Mean Absolute Error (MAE).
- Root Mean Squared Error (RMSE).
- Weighted Absolute Percentage Error (WAPE), where appropriate.

#### Evaluation requirements

Report:

- Overall seven-day forecast performance.
- Performance by forecast horizon, where feasible.
- Validation results.
- Final held-out test results.
- Baseline comparison.
- Error distributions.
- Significant forecast misses.
- Effects of unusual revenue spikes.

Do not use MAPE blindly when actual daily revenue can be zero.

Clearly explain metric units and denominators.

Compare models under the same evaluation dates and calendar policy.

Do not claim an improvement based solely on training performance.

If a naive or seasonal-naive baseline performs best, report that result honestly.

---

### 13. Statistical and Diagnostic Analysis

Investigate the forecasting series before final model selection.

#### Required diagnostics

- Revenue distribution.
- Daily revenue volatility.
- Weekday patterns.
- Autocorrelation at relevant lags.
- Trend behavior.
- Extreme observations.
- Missing-date sensitivity.
- Prediction residuals.

Use appropriate statistical techniques without unnecessary complexity.

#### Interpretation

Explain:

- Whether weekly structure appears useful.
- Whether the short history limits seasonality estimates.
- Whether extreme transactions dominate errors.
- Whether the model systematically overpredicts or underpredicts.
- Whether errors increase with forecast horizon.
- Whether the model is stable across validation periods.

Do not make unsupported causal claims.

---

### 14. Forecasting Sensitivity Experiments

Perform a small, controlled set of sensitivity experiments.

At minimum, investigate:

**Experiment A — Calendar policy**

Compare reasonable treatments of missing-record dates.

**Experiment B — Extreme observations**

Quantify the influence of exceptional revenue days on forecast evaluation.

**Experiment C — Non-merchandise charges**

Assess the impact of clearly identifiable charge/service codes where the classification is defensible.

Keep the primary target definition unchanged.

Treat alternative target definitions as separate experiments with separate labels and metrics.

Do not compare models across different targets as though the metrics are directly interchangeable.

Do not select the final approach based on final held-out test performance.

Document the effect of each sensitivity choice.

---

### 15. Future Forecast Inference

Implement a reusable inference interface.

It must be possible to generate a genuine seven-day forecast from the latest eligible historical observation.

#### Required functionality

- Load the selected model.
- Load the required preprocessing configuration.
- Load or reconstruct the required historical context.
- Determine the forecast origin.
- Generate seven future calendar dates.
- Produce one prediction per date.
- Record the forecast horizon.
- Return forecast values in GBP.
- Clearly identify the forecasting model and version.
- Report the training cutoff date.
- Validate required input history.

Do not use future actual sales in the inference pipeline.

#### Forecast interpretation

The dataset ends in December 2011.

Forecasts generated from this dataset are **historical demonstrations**, not predictions of current retail revenue in 2026.

Clearly label them as retrospective demonstrations.

Do not describe historical-data forecasts as live business predictions.

---

### 16. Model Persistence and Metadata

Save the selected model and necessary preprocessing artifacts.

Use an appropriate format such as joblib.

#### Required metadata

Record:

- Model name.
- Model version.
- Training start and end dates.
- Validation period.
- Held-out test period.
- Forecast horizon.
- Forecasting strategy.
- Feature list.
- Feature availability assumptions.
- Calendar policy.
- Revenue eligibility policy.
- Hyperparameters.
- Random seed.
- MAE.
- RMSE.
- WAPE where appropriate.
- Dataset provenance.
- Relevant dependency versions.

Ensure the model can be loaded in a fresh Python process.

Do not load untrusted serialized model files.

Avoid committing unnecessarily large model artifacts.

---

### 17. Project Architecture

Build on the existing Quantiva architecture.

Expected modules include:

- Time-series preparation.
- Calendar policy.
- Forecasting features.
- Baseline models.
- Regression model training.
- Chronological validation.
- Forecast evaluation.
- Model persistence.
- Future inference.
- Forecast reporting.

Use modular, maintainable Python code.

Prefer reusing existing package configuration and logging.

Avoid duplicating existing data ingestion, cleaning, SQL, or analytics logic.

Use type hints and docstrings for important interfaces.

Keep forecasting logic separate from eventual dashboard presentation code.

Do not unnecessarily restructure working Phase 1 and Phase 2 components.

---

### 18. Command-Line Interface

Extend the existing Quantiva CLI.

Provide practical commands for:

- Preparing the forecasting series.
- Training and evaluating forecasting models.
- Comparing model performance.
- Generating a seven-day forecast.
- Verifying forecasting artifacts.

Exact command names may follow the existing CLI conventions.

Commands should:

- Use centralized configuration.
- Provide clear errors.
- Support reproducible execution.
- Avoid hardcoded personal paths.
- Document required prerequisites.
- Print useful progress and summary information.

---

### 19. Notebooks and Visualizations

Create a dedicated forecasting notebook:

`notebooks/03_forecasting_experiments.ipynb`

#### Required notebook content

1. Forecasting problem definition.
2. Target construction.
3. Calendar coverage investigation.
4. Descriptive time-series analysis.
5. Baseline forecasting.
6. Feature engineering.
7. Model training.
8. Chronological validation.
9. Model comparison.
10. Final test evaluation.
11. Forecast error analysis.
12. Sensitivity experiments.
13. Future forecast demonstration.
14. Limitations and conclusions.

#### Required charts

- Historical daily revenue.
- Forecast validation windows.
- Actual versus predicted revenue.
- Model comparison.
- Forecast error by horizon.
- Residual distribution.
- Forecast demonstration for the next seven days.

Use Matplotlib and Plotly where appropriate.

Include written interpretations for major charts.

Ensure all notebook cells execute successfully from a clean environment.

---

### 20. Automated Testing

Extend the existing pytest suite.

#### Required tests

Test:

1. Daily revenue aggregation.
2. Calendar gap handling.
3. Partial boundary-date handling.
4. Forecasting target eligibility.
5. Lag feature calculations.
6. Rolling feature calculations.
7. Temporal leakage prevention.
8. Chronological split boundaries.
9. Seven-day horizon construction.
10. Naive baseline behavior.
11. Seasonal-naive baseline behavior.
12. Recursive or direct multi-step forecasting.
13. Correct use of historical predictions during inference.
14. Metric calculations.
15. Zero-revenue metric edge cases.
16. Model serialization and reloading.
17. Forecast reproducibility.
18. Missing input handling.
19. Inference output schema.
20. Separation of validation and held-out test data.

Use small deterministic synthetic fixtures for unit tests.

Synthetic data may be used for tests but not fabricated as actual retail findings.

Run all Phase 1 and Phase 2 regression tests.

---

### 21. Verification and Reproducibility

Run:

- The full pytest suite.
- Ruff lint checks.
- Ruff formatting checks.
- Dependency consistency checks.
- Phase 1 data verification.
- Phase 2 database verification.
- SQL/pandas reconciliation.
- Phase 3 forecasting verification.
- Notebook execution in a clean kernel.

Where practical, verify the entire workflow in a fresh local environment.

Ensure training and evaluation can be reproduced from the documented dataset and configuration.

Do not claim any check passed unless it was executed.

Report failures accurately.

---

### 22. Documentation

Update the README and create or update:

- `reports/model_evaluation.md`
- `reports/phase_3_methodology.md`
- `reports/phase_3_progress.md`
- Appropriate machine-readable metrics and configuration files.

#### Model evaluation report

Include:

- Forecasting target definition.
- Calendar policy.
- Feature engineering.
- Forecasting strategy.
- Baseline performance.
- Linear Regression performance.
- Random Forest performance.
- Chronological validation results.
- Held-out test results.
- Error diagnostics.
- Sensitivity experiments.
- Selected model and justification.
- Limitations.
- Reproduction commands.

Use actual calculated metrics only.

#### Technical methodology

Explain the statistical and machine learning concepts used.

Document leakage-prevention measures and validation decisions.

---

### 23. Learning and Mentorship

I want to understand the data science behind the implementation.

For each major area, explain:

1. What was built.
2. Why it matters.
3. How it works.
4. Which machine learning concepts are involved.
5. How correctness was verified.
6. What limitations remain.

Provide accessible but technically accurate explanations.

Explain the difference between:

- Regression and time-series forecasting.
- Training, validation, and testing.
- Overfitting and generalization.
- Baseline models and machine learning models.
- Recursive and direct multi-step forecasting.
- MAE, RMSE, and WAPE.
- Data leakage and legitimate historical features.

Do not simply generate code without helping me understand the methods.

---

### 24. Engineering Constraints

The project must remain:

- Completely free.
- Locally executable.
- Compatible with Windows.
- Reproducible.
- Modular.
- Well-tested.
- Properly documented.
- Suitable for a professional GitHub portfolio.

Do not introduce:

- Paid APIs.
- Mandatory cloud services.
- Proprietary forecasting platforms.
- Unnecessary deep learning frameworks.
- Fabricated business data.
- Fabricated forecasting results.
- Unsupported accuracy claims.
- Unnecessary architectural complexity.

Maintain compatibility with the existing Python 3.11 environment unless a change is justified.

---

### 25. Phase 3 Definition of Done

Phase 3 is complete only when:

- The forecasting target is documented and reconciled with Phase 2.
- Calendar gaps and boundary dates are handled explicitly.
- The seven-day forecasting horizon is correctly implemented.
- Naive and weekly seasonal-naive baselines work.
- Linear Regression and Random Forest models are implemented.
- Historical features are leakage-safe.
- Chronological validation works.
- The final test period remains untouched during model selection.
- Models are compared under equivalent evaluation conditions.
- MAE, RMSE, and appropriate percentage errors are reported.
- Forecast diagnostics are documented.
- Sensitivity experiments are completed.
- The selected model can be saved and reloaded.
- Genuine seven-day inference works without future actuals.
- The forecasting notebook executes successfully.
- All automated tests pass.
- Phase 1 and Phase 2 remain functional.
- Documentation contains actual results and limitations.
- No unsupported predictive-performance claims are made.

Do not declare Phase 3 complete until these requirements are verified.

---

### 26. Implementation Stages

Implement Phase 3 incrementally.

**Stage 1 — Repository Verification**
- Inspect Git status.
- Confirm synchronized main.
- Run baseline tests.
- Create Phase 3 branch.

**Stage 2 — Forecasting Data Foundation**
- Define target and calendar policy.
- Build daily time series.
- Validate aggregation and date coverage.

**Stage 3 — Baselines and Validation**
- Implement naive and seasonal-naive baselines.
- Establish chronological validation.
- Reserve untouched final test data.

**Stage 4 — Machine Learning**
- Implement leakage-safe features.
- Train Linear Regression and Random Forest.
- Compare models on validation folds.

**Stage 5 — Evaluation and Sensitivity**
- Evaluate selected model and baselines on held-out data.
- Analyze errors.
- Run controlled sensitivity experiments without using the held-out test set for decisions.

**Stage 6 — Inference and Persistence**
- Save model and configuration.
- Implement seven-day inference.
- Verify loading and reproducibility.

**Stage 7 — Documentation and Verification**
- Execute all tests.
- Execute forecasting notebook.
- Generate model evaluation reports.
- Review completion criteria.

You may proceed between stages without asking permission.

However, do not begin Phase 4 without explicit approval.

---

### 27. Final Progress Report

When Phase 3 implementation is complete, create:

`reports/phase_3_progress.md`

Include:

#### A. Git Status
- Current branch.
- Commit history.
- Uncommitted changes.
- GitHub synchronization status.

#### B. Implementation
- Files created.
- Files modified.
- Forecasting architecture.
- Model implementations.
- CLI commands.
- Notebooks.
- Tests.

#### C. Forecasting Results
- Actual baseline metrics.
- Actual machine learning metrics.
- Validation results.
- Held-out test results.
- Selected model.
- Forecast horizon performance.
- Important error patterns.

#### D. Data and Statistical Findings
- Calendar policy.
- Outlier sensitivity.
- Non-merchandise sensitivity.
- Leakage prevention.
- Limitations.

#### E. Verification
- Tests passed and failed.
- Regression test results.
- Notebook execution.
- Reproducibility checks.
- Outstanding defects.

#### F. Recommendations
- Whether Phase 3 is ready for approval.
- Remaining technical debt.
- Model reliability limitations.
- Recommended Phase 4 dashboard integration approach.

Do not fabricate results.

---

### 28. Final Execution Instructions

Treat this document as the authoritative Phase 3 implementation specification alongside `PROJECT_SPECIFICATION.md`.

Begin by inspecting the existing repository.

Preserve the verified Phase 1 and Phase 2 implementations.

Create `phase/03-machine-learning` from synchronized `main`.

Implement the forecasting pipeline incrementally.

Run tests throughout development.

Explain important machine learning and statistical concepts.

Do not merge into `main`.

Do not push anything to GitHub.

Do not begin Phase 4.

Do not commit changes without my explicit approval.

At completion, provide the final Phase 3 progress report and wait for my review.

**Begin Phase 3 implementation now.**
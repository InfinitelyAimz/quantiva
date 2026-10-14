# Phase 3 audit follow-up

Baseline audited commit: `bba3b8b259bba2d331ed7ef4fa878e2469a4556c`.
This follow-up is proposed on `phase-3`; PR #1 remains a draft targeting `main`.
The final fix commit SHA is reported in the PR and task after committing this report.

## Confirmed defect and correction

Constant revenue histories have zero variance, so autocorrelation is undefined.
The original diagnostics returned NaN, which strict JSON serialization rejected.
`series_diagnostics` now checks that each lag has enough varying paired observations
and represents undefined/nonfinite correlations as Python None, serialized as JSON
null. It avoids the constant-series numerical warning and preserves valid UCI
correlations. Null means correlation cannot be estimated, rather than an estimate
of zero correlation or proof of no temporal dependence.

Two focused regression cases use 140 dates of constant-zero and constant-positive
revenue. Both require all four lag correlations to be null after strict JSON
serialization and verify the unchanged revenue level and zero volatility.
The fix addresses diagnostic serialization; it is not a claim that every stage of
the UCI experiment now supports arbitrary degenerate datasets.

## Audit findings and documentation

The completion audit reproduced the committed workflow in a fresh GitHub checkout
using the dependency lock, regenerated all excluded UCI data/model artifacts, executed
all three notebooks, passed 64 original tests, seven Phase 1 checks, 3,982 Phase 2
reconciliations, 93 independent Phase 2 checks, 30 forecasting checks and 98 additional
forecasting/sensitivity checks. It found no UCI Phase 3 merge blocker, with the
constant-history diagnostics defect as an optional robustness correction.

README, methodology, progress report, generated model evaluation and forecasting
notebook now distinguish current code behavior from historical manual decisions.
The code selects using validation before computing test metrics. Reproduction cannot
independently establish whether earlier manual choices were influenced by already
viewed test outcomes. The overwritten selection file is not an immutable historical
record. No claims of independently verified historical manual tuning remain in these
implementation reports. The saved specification retains the user's original requirements.

## Verification of this follow-up

Executed with the existing locked Windows Python 3.11.9 `.venv-phase3` environment:

| Exact command (PowerShell) | Result |
| --- | --- |
| `.\.venv-phase3\Scripts\python.exe -m pytest tests/test_forecast_diagnostics.py -W error` | 2 passed |
| `.\.venv-phase3\Scripts\python.exe -m pytest -W error` | 66 passed in 10.23 seconds, including all 42 Phase 1/2 regression cases |
| `.\.venv-phase3\Scripts\ruff.exe check .` | Passed |
| `.\.venv-phase3\Scripts\ruff.exe format --check .` | Passed |
| `.\.venv-phase3\Scripts\python.exe -m pip check` | No broken requirements |
| `.\.venv-phase3\Scripts\python.exe scripts/verify_data.py` | All 7 checks passed |
| `.\.venv-phase3\Scripts\python.exe scripts/verify_analytics.py` | All 5 checks and 3,982 reconciliations passed; 14 SQL queries executed |
| `.\.venv-phase3\Scripts\quantiva.exe forecast-train` | Training/evaluation, model persistence, reports and demonstration regenerated |
| `.\.venv-phase3\Scripts\python.exe scripts/verify_forecasting.py` | 30 checks passed, zero failed |
| `.\.venv-phase3\Scripts\quantiva.exe forecast-verify` | Checksums and deterministic seven-day saved-model inference passed |
| `.\.venv-phase3\Scripts\python.exe scripts/execute_notebooks.py --phase 3` | Fresh-kernel forecasting notebook passed |
| `git diff --check` | Passed |

The final report wording was regenerated from the same saved prediction tables after
a heading change; no additional model selection or parameter tuning was performed.
The machine-readable `phase_3_fix_verification.json` compares 18 regenerated evidence
files with the baseline Git blobs: all nine forecast CSVs and both forecasting JSONs
are identical after LF/CRLF normalization; all seven PNGs are byte-identical. This
covers predictions, metrics, sensitivities, diagnostics, selection, split configuration,
seed, features, lineage and the model metadata hash. The comparison preserves exact
numerical strings, rather than merely accepting a numerical tolerance.

Random Forest remains validation-selected with MAE £11,431.53/day. Its held-out MAE
remains £12,344.71/day, versus £11,250.17/day for weekly seasonal naive. The baseline's
better test result is reported without changing the frozen selection. No model
parameters, splits, target/calendar policies or measured forecasting results changed.

## Remaining limitations and blockers

No known blocker remains for the scoped UCI Phase 3 experiment. Historical manual
decision provenance remains unverified; future experiments should archive immutable
pretest configurations and predictions. The short history, unknown gap causes,
extreme orders, correlated predictors, limited origins and weekday/horizon confounding
remain. No calibrated intervals or concurrent artifact replacement are supported.
The forest is not justified as a production improvement over the better held-out
weekly baseline. Optional future techniques require new independent evaluation.

Main is unchanged; no merge or PR-readiness change is authorized. Phase 4 and Phase 5
remain unstarted. The audit and this follow-up are review evidence, not phase approval.

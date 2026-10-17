# Methodology and limitations

[README](../README.md) · [Case study](../reports/portfolio_case_study.md)

This is the current entry point to the preserved Phase 1–4 technical reports.
Statements such as “the next phase has not started” inside earlier progress reports
describe their historical milestone, not the current project state. Phases 1–4 are
merged; Phase 5 packages the existing system for review.

| Question | Authoritative detail and measured evidence |
| --- | --- |
| What happened to every source line? | [Phase 1 methodology](../reports/methodology.md), [quality counts](../reports/phase_1_quality.json) |
| What does revenue mean? | [KPI specification](../reports/kpi_specification.md), [Phase 2 methodology](../reports/phase_2_methodology.md) |
| Do SQL and pandas agree? | [Reconciliation](../reports/reconciliation.csv), [metrics](../reports/phase_2_metrics.json), [independent workbook audit](../reports/phase_2_audit_results.json) |
| What patterns were measured? | [Findings](../reports/findings.md), [exploration notebook](../notebooks/01_data_exploration.ipynb), [statistics notebook](../notebooks/02_statistical_analysis.ipynb) |
| How were forecasts evaluated? | [Phase 3 methodology](../reports/phase_3_methodology.md), [model evaluation](../reports/model_evaluation.md), [forecast notebook](../notebooks/03_forecasting_experiments.ipynb) |
| What was corrected or unverified? | [Phase 3 audit follow-up](../reports/phase_3_audit_followup.md) |
| What do RFM, filters and currency mean? | [Phase 4 methodology](../reports/phase_4_methodology.md), [UI verification](../reports/phase_4_ui_verification.md) |
| How was this portfolio package checked? | [Phase 5 progress](../reports/phase_5_progress.md) |
| What is implemented and independently checked? | [Technical scope and verification contract](technical_scope.md) |

## Interpretive boundaries

- **Gross eligible sales:** positive-price, positive-quantity, noncancelled eligible
  lines, including charges and anonymous purchases. Not profit, settled payments
  or accounting net revenue. Cancellations are separate signed movements without
  verified matching to original purchases; adjustment candidates are not confirmed returns.
- **Missing identifiers:** raw missing customer IDs occur on 135,080 lines. Aggregate
  sales retain anonymous records; customer metrics/RFM describe identifiable purchasers
  only. Missingness can bias conclusions; it is not established as random.
- **Duplicates and extremes:** identical lines lack a unique source-line identifier.
  Keep-first deduplication is an assumption with a documented sensitivity, not proof
  that every repeated item was an error. Large valid orders remain in primary metrics.
- **Calendar:** absent dates mean zero recorded activity, not proven zero demand.
  December 2011 is partial. Forecasting conservatively excludes both source boundary
  dates; the first day's completeness is uncertain and the last ends at midday.
- **RFM:** reference date is the day after the selected end date. Distinct eligible
  invoices define frequency; GBP spend defines monetary value. Scores are relative
  to the selected cohort, with ties respected. Segment names do not verify churn,
  lifetime value, acquisition date or response to an intervention.
- **Forecasting:** current code selects on validation before test. Reproduction
  cannot independently establish that earlier manual decisions were uninfluenced
  by previously seen test results; the selection file is overwritten on reruns.
  Weekly Seasonal Naive has better held-out MAE than Random Forest. One short
  history, spikes, gaps and weekday/horizon confounding limit generalization.
- **Inference:** 9–15 December 2011 is a retrospective demonstration from a separate
  final refit, not a current prediction. Its weights do not inherit the pretest
  model's held-out score as an independent evaluation. No calibrated intervals exist.
- **Currency:** GBP remains authoritative. ZAR uses a fixed 8 December 2011 ECB
  cross-rate, £1 = R12.708021, only for display/export. It is not transaction-date
  conversion, a period average, inflation adjustment or actual historical ZAR sales.
- **Inference versus explanation:** correlations, RFM groups and feature importance
  describe associations. No causal effects, business uplift or population-wide
  retail results have been measured.

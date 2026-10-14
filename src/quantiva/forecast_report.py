"""Measured forecasting reports and reproducible diagnostic plots."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
from matplotlib.dates import AutoDateLocator, ConciseDateFormatter

from quantiva.analysis_report import markdown_table
from quantiva.forecast_evaluation import summarize_predictions


def write_forecast_report(
    summary: dict,
    history: pd.Series,
    validation: pd.DataFrame,
    test: pd.DataFrame,
    demo: pd.DataFrame,
    folder: Path,
) -> None:
    """Render measured comparisons and seven interpreted charts without invented scores."""
    figures = folder / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "figure.facecolor": "#101b2d",
            "axes.facecolor": "#101b2d",
            "text.color": "#e8edf5",
            "axes.labelcolor": "#e8edf5",
            "xtick.color": "#b9c7da",
            "ytick.color": "#b9c7da",
            "axes.edgecolor": "#62728a",
            "font.size": 10,
            "savefig.facecolor": "#101b2d",
        }
    )

    def save(name, title, draw, xlabel, ylabel):
        fig, ax = plt.subplots(figsize=(10, 5), layout="constrained")
        draw(ax)
        if name in {"history", "windows", "actual_prediction", "demonstration"}:
            locator = AutoDateLocator(minticks=4, maxticks=7)
            ax.xaxis.set_major_locator(locator)
            ax.xaxis.set_major_formatter(ConciseDateFormatter(locator))
        ax.set(title=title, xlabel=xlabel, ylabel=ylabel)
        ax.grid(axis="y", alpha=0.15)
        fig.savefig(figures / f"forecast_{name}.png", dpi=130)
        plt.close(fig)

    selected = summary["selected_model"]
    v = validation.loc[validation["model"].eq(selected)]
    t = test.loc[test["model"].eq(selected)]

    def historical(ax):
        ax.plot(history.index, history, color="#59a5f5", linewidth=0.8)
        split = summary["split"]
        ax.axvspan(
            pd.Timestamp(split["validation_start_date"]),
            pd.Timestamp(split["validation_end_date"]),
            color="#59a5f5",
            alpha=0.2,
            label="Validation",
        )
        ax.axvspan(
            pd.Timestamp(split["test_start_date"]),
            history.index[-1],
            color="#efa65d",
            alpha=0.2,
            label="Untouched test",
        )
        ax.legend()

    save(
        "history",
        "Observed daily gross revenue — both source boundaries excluded",
        historical,
        "Source calendar date",
        "Observed gross revenue (GBP)",
    )

    def windows(ax):
        for fold, frame in v.groupby("fold"):
            ax.plot(frame["date"], [fold] * len(frame), color="#59a5f5", linewidth=6)
            ax.scatter(frame["forecast_origin"].iloc[0], fold, color="#efa65d")

    save(
        "windows",
        "Expanding-origin validation — each bar is a full 7-calendar-day forecast",
        windows,
        "Prediction dates (orange point = forecast origin)",
        "Validation fold",
    )

    def actual_predicted(ax):
        ax.plot(t["date"], t["actual_gbp"], label="Actual observed", color="#e8edf5")
        ax.plot(t["date"], t["prediction_gbp"], label=f"Predicted: {selected}", color="#59a5f5")
        ax.legend()

    save(
        "actual_prediction",
        "Held-out results — selected model only, frozen learned weights",
        actual_predicted,
        "Test calendar date",
        "Gross observed revenue (GBP)",
    )
    comparison = pd.DataFrame(summary["validation"]).sort_values("mae_gbp")
    save(
        "comparison",
        "Primary validation MAE — equal dates and target for all candidates",
        lambda ax: ax.bar(comparison["model"], comparison["mae_gbp"], color="#59a5f5"),
        "Candidate",
        "Mean absolute error (GBP/day)",
    )
    horizons = summarize_predictions(test, by="horizon")

    def horizon_plot(ax):
        for name, frame in horizons.groupby("model"):
            ax.plot(frame["horizon"], frame["mae_gbp"], marker="o", label=name)
        ax.legend()

    save(
        "horizons",
        "Held-out MAE by forecast horizon — eight origins per horizon",
        horizon_plot,
        "Calendar days ahead",
        "MAE (GBP/day)",
    )
    save(
        "residuals",
        "Selected held-out residuals — positive = overprediction",
        lambda ax: ax.hist(
            t["prediction_gbp"] - t["actual_gbp"], bins=20, color="#59a5f5", edgecolor="#101b2d"
        ),
        "Prediction minus actual (GBP)",
        "Forecast-day count",
    )

    def demonstration(ax):
        ax.plot(
            history.iloc[-28:].index,
            history.iloc[-28:],
            label="Historical observed",
            color="#e8edf5",
        )
        ax.plot(
            demo["date"],
            demo["prediction_gbp"],
            marker="o",
            color="#59a5f5",
            label="Retrospective 2011 demonstration",
        )
        ax.axvline(history.index[-1], color="#efa65d", linestyle="--")
        ax.legend()

    save(
        "demonstration",
        "Next seven days after December 2011 history — not live 2026 predictions",
        demonstration,
        "Historical/demonstration date",
        "Gross revenue (GBP)",
    )
    interactive = px.line(
        test,
        x="date",
        y="prediction_gbp",
        color="model",
        template="plotly_dark",
        title="Held-out historical forecast comparison (GBP)",
        hover_data=["actual_gbp", "horizon", "forecast_origin"],
    )
    interactive.write_html(figures / "forecast_interactive.html", include_plotlyjs=True)
    validated = pd.DataFrame(summary["validation"])
    tested = pd.DataFrame(summary["heldout_test"])
    sensitivities = pd.DataFrame(summary["sensitivities"])
    influence = pd.DataFrame(summary["extreme_influence"])
    chosen_validation = validated.loc[validated["model"].eq(selected)].iloc[0]
    chosen_test = tested.loc[tested["model"].eq(selected)].iloc[0]
    best_test = tested.sort_values(["mae_gbp", "model"]).iloc[0]
    test_interpretation = (
        "The validation-selected candidate is also best on this single held-out period; "
        "that is limited evidence, not broad deployment reliability."
        if best_test["model"] == selected
        else f"{best_test['model']} beats validation-selected {selected} on test. "
        "The selection is not revised after viewing test scores; "
        "no general machine-learning superiority claim is supported."
    )
    test_wape = (
        "undefined (zero total actual revenue)"
        if chosen_test["wape_pct"] is None
        else f"{chosen_test['wape_pct']:.2f}%"
    )
    fold_metrics = summarize_predictions(validation, by="fold")
    chosen_folds = fold_metrics.loc[fold_metrics["model"].eq(selected)]
    worst = (
        test.assign(absolute_error=(test["prediction_gbp"] - test["actual_gbp"]).abs())
        .loc[test["model"].eq(selected)]
        .nlargest(5, "absolute_error")
    )
    plot_notes = [
        (
            "history",
            "Missing dates are zero observed activity, not proven zero demand. "
            "Windows are chronological; both source boundary days are excluded.",
        ),
        (
            "windows",
            "Each origin fits earlier history and predicts a whole week. "
            "Actuals within the predicted week are never fed into its predictions.",
        ),
        (
            "actual_prediction",
            "Selected weights are fixed before test. Later origins may use "
            "earlier test dates as context, never their own future window.",
        ),
        (
            "comparison",
            "MAE compares the same 56 validation forecast-days. Lower means smaller "
            "absolute errors; complexity does not determine the ranking.",
        ),
        (
            "horizons",
            "Eight observations per horizon are a small sample. Errors need not "
            "increase monotonically: each lead targets a different weekday.",
        ),
        (
            "residuals",
            "Positive residuals overpredict. Large negative residuals can reflect "
            "spikes; the histogram does not establish independent/normal errors.",
        ),
        (
            "demonstration",
            "Forecasts refer to December 2011 after modeled history. No future "
            "transactions are used; no current-business prediction is claimed.",
        ),
    ]
    charts = "\n\n".join(
        f"![{name}](figures/forecast_{name}.png)\n\nInterpretation: {note}"
        for name, note in plot_notes
    )
    worst_table = markdown_table(
        worst[
            ["date", "forecast_origin", "horizon", "actual_gbp", "prediction_gbp", "absolute_error"]
        ]
    )
    report = f"""# Phase 3 measured forecasting experiment

## Target and frozen experiment

Daily gross eligible completed-sales GBP, including eligible charges, under unchanged
Phase 1/2 rules. No cancellation netting or valid-outlier deletion. Dates without
records carry zero observed revenue, not a zero-demand assertion. Both source boundary
days are excluded. Modeling range: {summary["series"]["modeling_start"]} to
{summary["series"]["modeling_end"]}. Full source total reconciles to Phase 2 daily SQL;
excluded boundary revenue is £{summary["series"]["excluded_boundary_revenue_gbp"]:,.2f}.

Initial training: {summary["split"]["training_start_date"]}–
{summary["split"]["initial_training_end_date"]}.
Validation: {summary["split"]["validation_start_date"]}–{summary["split"]["validation_end_date"]}
(eight expanding weekly origins). Held-out test:
{summary["split"]["test_start_date"]}–{summary["split"]["test_end_date"]} (eight origins).
Splits depend only on dates/length; primary policy, features, hyperparameters, seed,
and selection rule are fixed before viewing final test metrics.

The full seven-calendar-day horizon is recursive: unknown future lag/rolling inputs
use earlier predictions. Known date predictors use no transaction counts, activity
flags, future customers, or future actual revenue. Numeric scaling and weekday
encoding are fitted within each training window. Negative predictions clip to zero
under the same declared policy in evaluation and deployment.

## Primary validation comparison

{markdown_table(validated)}

Selected **{selected}** by lowest primary validation MAE
**£{chosen_validation["mae_gbp"]:,.2f}**, with deterministic model-name tie breaking.
Candidate ranking does not use sensitivity outcomes or held-out scores. A baseline
win is reported without forcing a machine learning model into deployment.

## Untouched held-out comparison

{markdown_table(tested)}

Only the selected candidate and required naive/weekly baselines are evaluated here.
Learned weights train through {summary["split"]["validation_end_date"]} and stay frozen
for test. Historical context advances between completed forecast blocks, reflecting
weekly operation. There is no weight refit on test targets. Selected test MAE is
£{chosen_test["mae_gbp"]:,.2f}; RMSE £{chosen_test["rmse_gbp"]:,.2f}; WAPE
{test_wape}. These results are descriptive evidence on one short
held-out period, not statistical proof of broad superiority.

MAE/RMSE are GBP per forecast-day. RMSE weights large misses more strongly.
WAPE = 100 × sum absolute error / sum absolute actual GBP across the scored rows;
it is undefined for all-zero actuals. Zero daily values do not cause MAPE-style divisions.
Horizon and fold results are in the accompanying CSV files.

The lowest held-out MAE belongs to **{best_test["model"]}** at
**£{best_test["mae_gbp"]:,.2f}**. This does not revise the validation selection.
{test_interpretation}

## Diagnostics

Selected validation fold MAE ranges from £{chosen_folds["mae_gbp"].min():,.2f} to
£{chosen_folds["mae_gbp"].max():,.2f}. Test mean prediction-minus-actual bias is
£{chosen_test["bias_gbp"]:,.2f}. Positive means overprediction; negative means
underprediction. Error distributions and horizons do not support claims about
normality, causal weekdays, or stable annual seasonality.

Development-only autocorrelations (no test-based feature selection):
{summary["development_diagnostics"]["autocorrelation"]}.
Lag correlations are descriptive and confounded by trend, weekday schedule and extremes;
weekly structure should be judged alongside actual seasonal-naive performance.

Largest selected held-out misses:

{worst_table}

## Controlled sensitivity experiments — validation only

{markdown_table(sensitivities)}

Calendar alternative: weekdays {summary["sensitivity_inactive_weekdays"]} (Monday=0)
have at least eight initial-training occurrences and no ledger records; those rules
are frozen before validation. Exclude those weekdays from regression training and
forecast zero on their scheduled dates, without examining each future day's activity.
Other gaps remain zero observed revenue. Same seven calendar dates are scored.

Named-charge alternative: exclude exactly DOT, POST, AMAZONFEE, BANK CHARGES.
M (Manual) remains included because its merchandise/adjustment meaning is ambiguous.
This is a distinct revenue target; its errors cannot be called improvements on the
primary gross target. Other ambiguous codes remain included. No sensitivity changes
the primary selection rule.

Extreme influence uses initial-training p99 £{summary["initial_p99_gbp"]:,.2f} to
describe validation error concentration and show below-threshold evaluation only.
No training targets are winsorized or removed, and no held-out threshold is optimized.

{markdown_table(influence)}

## Persistence and retrospective inference

The selected model is refitted through {summary["deployment_training_cutoff"]} only
AFTER held-out evaluation, for demonstration deployment. This different final refit
is not assigned the pretest model's test score as its own unbiased evaluation.
Version 3.0.0 metadata distinguishes the pretest evaluation cutoff from deployment
cutoff, and records features, seed, policies, metrics, dependencies and provenance.
Model/context/metadata live in ignored data/models with checksum manifest. Load only
trusted local artifacts; hashes do not authenticate an untrusted pickle.

{markdown_table(demo[["date", "horizon", "prediction_gbp", "model", "training_cutoff"]])}

These are **retrospective demonstrations for December 2011**, not 2026 forecasts.
The original excluded partial-day record is not used as a future predictor or as a
complete actual to judge the demonstration. No prediction intervals are claimed.

## Figures and interpretations

{charts}

## Reproduction and limitations

`quantiva forecast-prepare`, `quantiva forecast-train`, `quantiva forecast-compare`,
`quantiva forecast`, `quantiva forecast-verify`; see README and phase_3_methodology.md.
Training reruns reproduce this frozen experiment, not a new test-guided tuning loop.
The source is one retailer over about one year, including wholesale spikes, charges,
holiday gaps and missing Saturdays. Eight origins per split/horizon provide limited
stability evidence. Direct horizon models or richer calendars are future options,
not assumed improvements. A 30-day model needs separate evaluation; no claim is made.
"""
    (folder / "model_evaluation.md").write_text(report, encoding="utf-8")

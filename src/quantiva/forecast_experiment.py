"""Validation-first experiments, sealed test evaluation, and deployment refit."""

import json
import logging
import math
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from quantiva.config import Settings
from quantiva.database import load_verified_ledger
from quantiva.features import FEATURES
from quantiva.forecast_evaluation import (
    SplitPlan,
    heldout_evaluation,
    rolling_validation,
    summarize_predictions,
)
from quantiva.forecast_series import (
    CHARGE_CODES,
    TARGET_POLICY,
    construct_series,
    learn_inactive_weekdays,
    modeled_history,
    prepare_forecast_series,
)
from quantiva.forecasting import SEED, fit_forecaster, forecast
from quantiva.ingestion import sha256
from quantiva.model_artifacts import dependency_versions, save_artifact

logger = logging.getLogger(__name__)


def select_candidate(validation: pd.DataFrame) -> str:
    """Model selection consumes primary validation rows only, never held-out metrics."""
    if set(validation["experiment"]) != {"primary"}:
        raise ValueError("Selection requires primary validation only")
    comparison = summarize_predictions(validation).sort_values(["mae_gbp", "model"])
    return str(comparison.iloc[0]["model"])


def series_diagnostics(development: pd.Series) -> dict:
    """Describe development data; undefined correlations are None, not zero association."""
    autocorrelation = {}
    for lag in [1, 7, 14, 28]:
        current, previous = development.iloc[lag:], development.iloc[:-lag]
        # Correlation requires two varying samples. Avoid NumPy's zero-variance warning.
        if len(current) < 2 or current.nunique() < 2 or previous.nunique() < 2:
            autocorrelation[str(lag)] = None
        else:
            value = float(development.autocorr(lag))
            autocorrelation[str(lag)] = value if math.isfinite(value) else None
    return {
        "start": str(development.index[0].date()),
        "end": str(development.index[-1].date()),
        "mean_gbp": float(development.mean()),
        "median_gbp": float(development.median()),
        "std_gbp": float(development.std(ddof=1)),
        "max_gbp": float(development.max()),
        "autocorrelation": autocorrelation,
        "weekday_mean_gbp": {
            str(day): float(value)
            for day, value in development.groupby(development.index.dayofweek).mean().items()
        },
        "monthly_observed_revenue_gbp": development.groupby(development.index.strftime("%Y-%m"))
        .sum()
        .to_dict(),
    }


def train_experiment(settings: Settings, reports_dir: Path) -> dict:
    """Run fixed, deterministic choices; choose by validation MAE then open test once.

    Re-running reproduces the same frozen experiment; it is not a new tuning cycle.
    Keep train/config/selection logic unchanged once held-out results are opened.
    """
    series_meta = prepare_forecast_series(settings)
    table = pd.read_parquet(settings.forecast_dir / "daily_series.parquet")
    history = modeled_history(table)
    plan = SplitPlan()
    split = plan.boundaries(history)
    development = history.iloc[: split["test_start"]].copy()
    initial = history.iloc[: split["validation_start"]]
    diagnostics = series_diagnostics(development)
    logger.info("validation_start periods=%s", json.dumps(split))
    primary = rolling_validation(development, split["validation_start"])
    selected_name = select_candidate(primary)
    # Pre-declared calendar sensitivity learned once from initial training ONLY.
    inactive = learn_inactive_weekdays(table, initial.index[0], initial.index[-1])
    calendar_sensitivity = rolling_validation(
        development,
        split["validation_start"],
        inactive_weekdays=inactive,
        experiment="calendar_training_schedule",
    )
    # Distinct target: exact named-code exclusions, never adopted as primary.
    ledger = load_verified_ledger(settings)
    charges_history = modeled_history(construct_series(ledger, exclude_charges=True))
    charge_sensitivity = rolling_validation(
        charges_history.iloc[: split["test_start"]],
        split["validation_start"],
        experiment="excluding_named_charges",
    )
    # Influence-only diagnostic: threshold learned on initial training, no retraining/deletion.
    threshold = float(initial.quantile(0.99))
    extreme_rows = primary.copy()
    extreme_rows["is_extreme"] = extreme_rows["actual_gbp"].gt(threshold)
    central = primary.loc[~primary["actual_gbp"].gt(threshold)].copy()
    central["experiment"] = "evaluation_below_initial_training_p99"
    sensitivities = pd.concat(
        [calendar_sensitivity, charge_sensitivity, central], ignore_index=True
    )
    logger.info("selection_complete selected=%s validation_only=true", selected_name)
    # Persist the decision before computing test outcomes. This file has no test metric.
    settings.forecast_dir.mkdir(parents=True, exist_ok=True)
    frozen = {
        "selected_model": selected_name,
        "selection_metric": "primary validation MAE",
        "split": split,
        "split_config": asdict(plan),
        "seed": SEED,
        "features": list(FEATURES),
        "strategy": "recursive",
        "primary_policy": TARGET_POLICY,
        "calendar": "zero_observed_calendar",
        "clip_negative_predictions": True,
        "sensitivity_inactive_weekdays": list(inactive),
        "initial_p99_gbp": threshold,
    }
    (settings.forecast_dir / "selection_before_test.json").write_text(
        json.dumps(frozen, indent=2) + "\n", encoding="utf-8"
    )
    evaluation_model = fit_forecaster(development, selected_name)
    test = heldout_evaluation(history, split["test_start"], evaluation_model)
    validation_comparison = summarize_predictions(primary)
    test_comparison = summarize_predictions(test)
    fold_metrics = summarize_predictions(primary, by="fold")
    horizon_metrics = summarize_predictions(primary, by="horizon")
    test_horizons = summarize_predictions(test, by="horizon")
    sensitivity_metrics = summarize_predictions(sensitivities)
    reports_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in {
        "validation_predictions": primary,
        "test_predictions": test,
        "validation_comparison": validation_comparison,
        "test_comparison": test_comparison,
        "validation_folds": fold_metrics,
        "validation_horizons": horizon_metrics,
        "test_horizons": test_horizons,
        "sensitivity_metrics": sensitivity_metrics,
    }.items():
        frame.to_csv(reports_dir / f"forecast_{name}.csv", index=False)
    primary["residual_gbp"] = primary["prediction_gbp"] - primary["actual_gbp"]
    test["residual_gbp"] = test["prediction_gbp"] - test["actual_gbp"]
    influence = []
    for name, group in extreme_rows.groupby("model"):
        squared = (group["prediction_gbp"] - group["actual_gbp"]) ** 2
        influence.append(
            {
                "model": name,
                "threshold_gbp": threshold,
                "extreme_days": int(group["is_extreme"].sum()),
                "extreme_squared_error_share_pct": float(
                    100 * squared[group["is_extreme"]].sum() / squared.sum()
                ),
            }
        )
    metadata = {
        "forecast_horizon": 7,
        "forecast_strategy": "recursive_with_predicted_lags",
        "validation_period": [split["validation_start_date"], split["validation_end_date"]],
        "heldout_test_period": [split["test_start_date"], split["test_end_date"]],
        "evaluation_model_training_end": str(development.index[-1].date()),
        "deployment_refit_after_evaluation": True,
        "feature_list": list(FEATURES),
        "feature_availability": (
            "date known in advance; revenue features shifted to t-1 or earlier; "
            "recursive future context uses predictions"
        ),
        "calendar_policy": "zero_observed_calendar; both source boundary days excluded",
        "revenue_policy": TARGET_POLICY,
        "random_seed": SEED,
        "training_context_start": str(history.index[0].date()),
        "first_regression_target_date": str((history.index[0] + pd.Timedelta(days=28)).date()),
        "selected_validation_metrics": validation_comparison.loc[
            validation_comparison["model"].eq(selected_name)
        ]
        .iloc[0]
        .to_dict(),
        "selected_test_metrics": test_comparison.loc[test_comparison["model"].eq(selected_name)]
        .iloc[0]
        .to_dict(),
        "named_charge_exclusions_sensitivity_only": list(CHARGE_CODES),
        "preprocessing": {
            "weekday": "one-hot weekdays 0..6; drop Monday",
            "numeric": "StandardScaler fitted on historical training only",
        },
        "validation_metrics": validation_comparison.to_dict("records"),
        "test_metrics": test_comparison.to_dict("records"),
        "dataset_provenance": series_meta,
        "hyperparameters": {
            "linear_regression": "OLS with one-hot weekday, standardized numeric features",
            "random_forest": {
                "n_estimators": 120,
                "max_depth": 6,
                "min_samples_leaf": 5,
                "max_features": 1.0,
                "bootstrap": True,
                "n_jobs": 1,
            },
        },
        "interpretation": "December 2011 retrospective demonstration, not current revenue",
    }
    # Holdout now evaluated; full-history refit serves deployment only, never retroactive scores.
    deployed = fit_forecaster(history, selected_name)
    save_artifact(deployed, history, settings.model_dir, metadata)
    demonstration = forecast(deployed, history)
    demonstration.to_csv(reports_dir / "forecast_demonstration.csv", index=False)
    model_diagnostics = {}
    if deployed.estimator is not None:
        names = deployed.estimator.named_steps["preprocessing"].get_feature_names_out().tolist()
        regressor = deployed.estimator.named_steps["regressor"]
        importance = (
            regressor.coef_
            if selected_name == "linear_regression"
            else regressor.feature_importances_
        )
        model_diagnostics = dict(zip(names, [float(v) for v in importance], strict=True))
    summary = {
        **frozen,
        "series": series_meta,
        "development_diagnostics": diagnostics,
        "validation": validation_comparison.to_dict("records"),
        "heldout_test": test_comparison.to_dict("records"),
        "sensitivities": sensitivity_metrics.to_dict("records"),
        "extreme_influence": influence,
        "model_feature_diagnostics": model_diagnostics,
        "deployment_training_cutoff": str(history.index[-1].date()),
        "artifact_metadata_sha256": sha256(settings.model_dir / "metadata.json"),
        "dependencies": dependency_versions(),
    }
    (reports_dir / "forecast_results.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    from quantiva.forecast_report import write_forecast_report

    write_forecast_report(summary, history, primary, test, demonstration, reports_dir)
    logger.info("forecast_experiment_complete selected=%s", selected_name)
    return summary

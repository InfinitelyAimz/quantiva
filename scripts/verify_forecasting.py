"""Verify forecasting files, chronological accounting, metrics and artifact inference."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from quantiva.config import Settings
from quantiva.forecast_evaluation import score
from quantiva.forecast_series import TARGET_POLICY
from quantiva.ingestion import sha256
from quantiva.model_artifacts import forecast_saved, load_artifact, verify_artifact


def verify_forecasting() -> dict:
    """Verify current lineage and independently recompute all reported forecast metrics."""
    settings = Settings.from_environment()
    root = Path(__file__).resolve().parents[1]
    report = json.loads((root / "reports" / "forecast_results.json").read_text())
    split = report["split"]
    validation = pd.read_csv(
        root / "reports" / "forecast_validation_predictions.csv",
        parse_dates=["date", "forecast_origin", "training_cutoff"],
    )
    test = pd.read_csv(
        root / "reports" / "forecast_test_predictions.csv",
        parse_dates=["date", "forecast_origin", "training_cutoff"],
    )
    frozen = json.loads((settings.forecast_dir / "selection_before_test.json").read_text())
    checks = {
        "artifact_metadata_matches_report": sha256(settings.model_dir / "metadata.json")
        == report["artifact_metadata_sha256"],
        "raw_provenance_matches": sha256(settings.raw_file) == report["series"]["source_sha256"],
        "ledger_provenance_matches": sha256(settings.processed_dir / "transactions.parquet")
        == report["series"]["ledger_sha256"],
        "series_provenance_matches": sha256(settings.forecast_dir / "daily_series.parquet")
        == report["series"]["series_sha256"],
        "eligibility_policy_unchanged": report["primary_policy"] == TARGET_POLICY,
        "primary_validation_rows": len(validation) == 56 * 4,
        "test_models_selected_and_baselines_only": set(test["model"])
        == {report["selected_model"], "naive", "seasonal_naive"},
        "test_rows_accounted": len(test) == 56 * test["model"].nunique(),
        "validation_precedes_test": validation["date"].max() < test["date"].min(),
        "training_precedes_forecast_windows": bool(
            (validation["training_cutoff"] <= validation["forecast_origin"]).all()
            and (validation["forecast_origin"] < validation["date"]).all()
            and (test["training_cutoff"] < pd.Timestamp(split["test_start_date"])).all()
        ),
        "test_weights_not_refit": test.groupby("model")["training_cutoff"].nunique().eq(1).all(),
        "pretest_selection_matches": frozen["selected_model"] == report["selected_model"],
    }
    for label, frame, reported in [
        ("validation", validation, report["validation"]),
        ("test", test, report["heldout_test"]),
    ]:
        for model in reported:
            rows = frame.loc[frame["model"].eq(model["model"])]
            independently = score(rows["actual_gbp"], rows["prediction_gbp"])
            checks[f"{label}_metrics_{model['model']}"] = all(
                independently[key] is None
                and model[key] is None
                or np.isclose(independently[key], model[key], atol=1e-6, rtol=0)
                for key in ["mae_gbp", "rmse_gbp", "wape_pct", "bias_gbp", "observations"]
            )
            checks[f"{label}_horizons_{model['model']}"] = (
                rows.groupby("fold")["horizon"]
                .apply(lambda values: sorted(values) == list(range(1, 8)))
                .all()
            )
    artifact = verify_artifact(settings.model_dir)
    loaded, context, metadata = load_artifact(settings.model_dir, trusted=True)
    demo = forecast_saved(settings.model_dir, trusted=True)
    stored = pd.read_csv(root / "reports" / "forecast_demonstration.csv", parse_dates=["date"])
    checks["saved_inference_matches_report"] = np.allclose(
        stored["prediction_gbp"], demo["prediction_gbp"], rtol=0, atol=1e-8
    )
    checks["future_dates_without_actuals"] = (demo["date"] > context.index[-1]).all()
    checks["deployment_cutoff_distinguished"] = (
        metadata["evaluation_model_training_end"] < metadata["training_end"]
    )
    checks["selected_model_reload_matches"] = loaded.name == report["selected_model"]
    checks = {key: bool(value) for key, value in checks.items()}
    if not all(checks.values()):
        raise ValueError(f"Forecast verification failed: {[k for k, v in checks.items() if not v]}")
    summary = {
        "checks": checks,
        "passed": sum(checks.values()),
        "failed": 0,
        "artifact_inference": artifact,
    }
    (root / "reports" / "forecast_verification.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    verify_forecasting()

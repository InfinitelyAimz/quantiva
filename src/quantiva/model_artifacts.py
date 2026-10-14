"""Local trusted artifact persistence with checksums, context, and complete metadata."""

import json
import platform
from importlib.metadata import version
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from quantiva.forecast_series import validate_history
from quantiva.forecasting import Forecaster, forecast
from quantiva.ingestion import sha256


def dependency_versions() -> dict:
    """Capture the actual interpreter and forecasting runtime versions."""
    return {
        "python": platform.python_version(),
        **{name: version(name) for name in ["numpy", "pandas", "scikit-learn", "scipy", "joblib"]},
    }


def save_artifact(model: Forecaster, history: pd.Series, folder: Path, metadata: dict) -> dict:
    """Save local fitted model, observed context, metadata, and integrity manifest."""
    history = validate_history(history, minimum=28)
    if model.training_cutoff != history.index[-1]:
        raise ValueError("Saved deployment context must end at the final training cutoff")
    folder.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, folder / "selected.joblib", compress=3)
    history.rename("revenue_gbp").rename_axis("date").reset_index().to_csv(
        folder / "context.csv", index=False
    )
    config = {
        **metadata,
        "model_name": model.name,
        "model_version": model.version,
        "training_start": str(model.training_start.date()),
        "training_end": str(model.training_cutoff.date()),
        "inactive_weekdays": list(model.inactive_weekdays),
        "dependencies": dependency_versions(),
        "artifact_source": "locally_trained_quantiva",
    }
    (folder / "metadata.json").write_text(
        json.dumps(config, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    manifest = {
        name: sha256(folder / name) for name in ["selected.joblib", "context.csv", "metadata.json"]
    }
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return config


def load_artifact(folder: Path, *, trusted: bool = False) -> tuple[Forecaster, pd.Series, dict]:
    """Load only explicitly trusted local artifacts. Hashes are integrity, not authentication.

    Never point this at downloaded or third-party pickle/joblib files. Serialization
    may execute code; approval of trust must precede joblib.load.
    """
    if not trusted:
        raise ValueError("Serialized models require explicit trust in the local training source")
    manifest_path = folder / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError("Model artifacts missing. Run quantiva forecast-train first.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or set(manifest) != {
        "selected.joblib",
        "context.csv",
        "metadata.json",
    }:
        raise ValueError("Malformed model manifest")
    for name, digest in manifest.items():
        if sha256(folder / name) != digest:
            raise ValueError(f"Model artifact checksum mismatch: {name}")
    metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
    if metadata.get("artifact_source") != "locally_trained_quantiva":
        raise ValueError("Artifact is not marked as a locally trained Quantiva model")
    if metadata.get("dependencies") != dependency_versions():
        raise ValueError("Model dependency versions differ; use the lock file or retrain")
    model = joblib.load(folder / "selected.joblib")
    if not isinstance(model, Forecaster):
        raise ValueError("Unexpected serialized model type")
    table = pd.read_csv(folder / "context.csv", parse_dates=["date"])
    history = validate_history(table.set_index("date")["revenue_gbp"], minimum=28)
    if str(history.index[-1].date()) != metadata["training_end"]:
        raise ValueError("Context cutoff differs from metadata")
    if model.name != metadata["model_name"] or model.training_cutoff != history.index[-1]:
        raise ValueError("Model/context/metadata mismatch")
    return model, history, metadata


def forecast_saved(folder: Path, *, trusted: bool = False) -> pd.DataFrame:
    """Generate a retrospective seven-day demonstration with no future transactions."""
    model, context, _metadata = load_artifact(folder, trusted=trusted)
    return forecast(model, context)


def verify_artifact(folder: Path) -> dict:
    """Check reload/inference determinism for own locally produced artifacts."""
    first = forecast_saved(folder, trusted=True)
    second = forecast_saved(folder, trusted=True)
    pd.testing.assert_frame_equal(first, second)
    if len(first) != 7 or not np.isfinite(first["prediction_gbp"]).all():
        raise ValueError("Invalid saved-model inference output")
    return {
        "artifact_checksums": "passed",
        "inference_reproducibility": "passed",
        "horizon": 7,
        "origin": str(first["forecast_origin"].iloc[0].date()),
        "forecast_start": str(first["date"].iloc[0].date()),
        "forecast_end": str(first["date"].iloc[-1].date()),
        "model": first["model"].iloc[0],
    }

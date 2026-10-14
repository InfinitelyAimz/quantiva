"""Saved evaluation checks independent of optional binary-model availability."""

from pathlib import Path

import numpy as np
import pandas as pd

from quantiva.dashboard.data import read_json
from quantiva.forecast_evaluation import summarize_predictions


def load_evidence(folder: Path) -> dict:
    "Recompute metrics from saved predictions; do not infer trust from a stored PASS."
    summary = read_json(folder / "forecast_results.json")
    result = {"summary": summary}
    for name, key in [("validation", "validation"), ("test", "heldout_test")]:
        frame = pd.read_csv(
            folder / f"forecast_{name}_predictions.csv",
            parse_dates=["date", "forecast_origin", "training_cutoff"],
        )
        if not np.isfinite(frame[["prediction_gbp", "actual_gbp"]]).all().all():
            raise ValueError("Forecast evidence contains nonfinite values. Run forecast-train.")
        if not (frame["forecast_origin"] < frame["date"]).all():
            raise ValueError("Forecast evidence has invalid chronology")
        metrics = summarize_predictions(frame).sort_values("model").reset_index(drop=True)
        stored = pd.DataFrame(summary[key]).sort_values("model").reset_index(drop=True)
        if metrics["model"].tolist() != stored["model"].tolist() or not np.allclose(
            metrics[["mae_gbp", "rmse_gbp", "wape_pct", "bias_gbp"]],
            stored[["mae_gbp", "rmse_gbp", "wape_pct", "bias_gbp"]],
            atol=1e-6,
            rtol=0,
            equal_nan=True,
        ):
            raise ValueError("Forecast metrics disagree with predictions. Regenerate evidence.")
        result[name], result[f"{name}_metrics"] = frame, metrics
    if result["validation"]["date"].max() >= result["test"]["date"].min():
        raise ValueError("Validation overlaps test")
    return result

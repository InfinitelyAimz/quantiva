"""Command-line entry point for reproducible local runs."""

import argparse
import json
import logging
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from quantiva.analysis_report import write_analysis
from quantiva.config import Settings
from quantiva.database import rebuild_database
from quantiva.ingestion import download_dataset, load_raw, sha256
from quantiva.inspection import inspect_data
from quantiva.pipeline import prepare_data
from quantiva.reconciliation import query_names, run_query


def main() -> None:
    """Run one pipeline stage and report failures with an actionable message."""
    parser = argparse.ArgumentParser(description="Quantiva local retail analytics")
    parser.add_argument(
        "command",
        choices=[
            "download",
            "inspect",
            "prepare",
            "database",
            "query",
            "analyze",
            "forecast-prepare",
            "forecast-train",
            "forecast-compare",
            "forecast",
            "forecast-verify",
        ],
    )
    parser.add_argument("query_name", nargs="?", help="Packaged SQL query name")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s level=%(levelname)s %(message)s")
    settings = Settings.from_environment()
    try:
        if args.command == "download":
            download_dataset(settings.raw_file)
        elif args.command == "forecast-prepare":
            from quantiva.forecast_series import prepare_forecast_series

            print(json.dumps(prepare_forecast_series(settings), indent=2))
        elif args.command == "forecast-train":
            from quantiva.forecast_experiment import train_experiment

            print(
                json.dumps(
                    train_experiment(settings, Path(__file__).resolve().parents[2] / "reports"),
                    indent=2,
                )
            )
        elif args.command == "forecast-compare":
            import pandas as pd

            root = Path(__file__).resolve().parents[2] / "reports"
            for name in ["validation", "test"]:
                print(pd.read_csv(root / f"forecast_{name}_comparison.csv").to_string(index=False))
        elif args.command == "forecast":
            from quantiva.model_artifacts import forecast_saved

            output = forecast_saved(settings.model_dir, trusted=True)
            output.to_csv(settings.forecast_dir / "latest_forecast.csv", index=False)
            print(output.to_string(index=False))
        elif args.command == "forecast-verify":
            from quantiva.model_artifacts import verify_artifact

            print(json.dumps(verify_artifact(settings.model_dir), indent=2))
        elif args.command == "prepare":
            print(json.dumps(prepare_data(settings), indent=2))
        elif args.command == "database":
            print(json.dumps(rebuild_database(settings), indent=2))
        elif args.command == "analyze":
            root = Path(__file__).resolve().parents[2]
            print(json.dumps(write_analysis(settings, root / "reports"), indent=2))
        elif args.command == "query":
            if not args.query_name:
                print("Available queries: " + ", ".join(query_names()))
            else:
                print(run_query(settings.database_file, args.query_name).to_string(index=False))
        else:
            report = inspect_data(load_raw(settings.raw_file))
            report["source_sha256"] = sha256(settings.raw_file)
            settings.processed_dir.mkdir(parents=True, exist_ok=True)
            (settings.processed_dir / "initial_inspection.json").write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8"
            )
            print(json.dumps(report, indent=2))
    except (OSError, ValueError, RuntimeError, SQLAlchemyError) as exc:
        parser.exit(1, f"Pipeline failed: {exc}\n")

"""Command-line entry point for reproducible local runs."""

import argparse
import json
import logging

from quantiva.config import Settings
from quantiva.ingestion import download_dataset, load_raw, sha256
from quantiva.inspection import inspect_data
from quantiva.pipeline import prepare_data


def main() -> None:
    """Run one pipeline stage and report failures with an actionable message."""
    parser = argparse.ArgumentParser(description="Quantiva Phase 1 pipeline")
    parser.add_argument("command", choices=["download", "inspect", "prepare"])
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s level=%(levelname)s %(message)s")
    settings = Settings.from_environment()
    try:
        if args.command == "download":
            download_dataset(settings.raw_file)
        elif args.command == "prepare":
            print(json.dumps(prepare_data(settings), indent=2))
        else:
            report = inspect_data(load_raw(settings.raw_file))
            report["source_sha256"] = sha256(settings.raw_file)
            settings.processed_dir.mkdir(parents=True, exist_ok=True)
            (settings.processed_dir / "initial_inspection.json").write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8"
            )
            print(json.dumps(report, indent=2))
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, f"Pipeline failed: {exc}\n")

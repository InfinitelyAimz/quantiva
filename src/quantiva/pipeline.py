"""Run cleaning and save deterministic derived artifacts without append imports."""

import json
import logging
from pathlib import Path

from quantiva.cleaning import clean_transactions
from quantiva.config import Settings
from quantiva.ingestion import load_raw, sha256
from quantiva.inspection import inspect_data

logger = logging.getLogger(__name__)


def write_json(path: Path, payload: dict) -> None:
    """Replace a JSON report with a complete UTF-8 document."""
    temporary = path.with_suffix(path.suffix + ".part")
    try:
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def prepare_data(settings: Settings) -> dict:
    """Rebuild the ledger and audit files and write a provenance manifest last.

    Each output is replaced atomically, but the output set is not a multi-file
    transaction. Do not run concurrent prepares or read outputs during rebuilding.
    """
    before = sha256(settings.raw_file)
    raw = load_raw(settings.raw_file)
    inspection = inspect_data(raw)
    result = clean_transactions(raw)
    if before != sha256(settings.raw_file):
        raise RuntimeError("Source file changed during preparation; outputs were not saved")
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in [("transactions", result.ledger), ("exclusions", result.exclusions)]:
        target = settings.processed_dir / f"{name}.parquet"
        temporary = target.with_suffix(".parquet.part")
        try:
            frame.to_parquet(temporary, index=False, engine="pyarrow")
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    inspection["source_sha256"] = before
    result.report["source_sha256"] = before
    write_json(settings.processed_dir / "initial_inspection.json", inspection)
    write_json(settings.processed_dir / "cleaning_report.json", result.report)
    write_json(
        settings.processed_dir / "manifest.json",
        {
            "source_sha256": before,
            "policy_version": result.report["policy_version"],
            "outputs": {
                name: sha256(settings.processed_dir / name)
                for name in [
                    "transactions.parquet",
                    "exclusions.parquet",
                    "initial_inspection.json",
                    "cleaning_report.json",
                ]
            },
        },
    )
    logger.info("prepare_complete summary=%s", json.dumps(result.report))
    return result.report

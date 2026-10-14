"""Download the official workbook without modifying an existing raw file."""

import hashlib
import io
import json
import logging
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

from quantiva.config import COLUMNS, DATASET_PAGE, DOWNLOAD_URL

logger = logging.getLogger(__name__)


def sha256(path: Path) -> str:
    """Hash a file for reproducible provenance."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_dataset(destination: Path) -> Path:
    """Fetch UCI's ZIP, extract only its workbook, and record source metadata.

    Existing workbooks are reused. No ZIP member paths are extracted to disk.
    Failures leave no partially written workbook.
    """
    if destination.exists():
        logger.info("raw_file_reused path=%s sha256=%s", destination, sha256(destination))
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        response = requests.get(DOWNLOAD_URL, timeout=(15, 180))
        response.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            matches = [n for n in archive.namelist() if Path(n).name == "Online Retail.xlsx"]
            if len(matches) != 1:
                raise ValueError("The official archive must contain exactly one Online Retail.xlsx")
            workbook = archive.read(matches[0])
        # XLSX itself is a ZIP. Check integrity before saving the download.
        with zipfile.ZipFile(io.BytesIO(workbook)) as archive:
            if archive.testzip() is not None or "xl/workbook.xml" not in archive.namelist():
                raise ValueError("Downloaded workbook failed integrity validation")
    except (requests.RequestException, zipfile.BadZipFile, ValueError) as exc:
        raise RuntimeError(
            f"Download failed. Visit {DATASET_PAGE}, download and extract Online Retail.xlsx "
            f"to {destination}, then run quantiva inspect. Cause: {exc}"
        ) from exc
    temporary = destination.with_suffix(".xlsx.part")
    try:
        temporary.write_bytes(workbook)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    metadata = {
        "dataset": "UCI Online Retail (352)",
        "source_page": DATASET_PAGE,
        "download_url": DOWNLOAD_URL,
        "downloaded_at_utc": datetime.now(UTC).isoformat(),
        "sha256": sha256(destination),
        "bytes": destination.stat().st_size,
        "citation": "Chen, D. (2015). Online Retail. DOI: 10.24432/C5BW33",
        "license": "CC BY 4.0",
    }
    destination.with_suffix(".provenance.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    logger.info("download_complete bytes=%d sha256=%s", metadata["bytes"], metadata["sha256"])
    return destination


def load_raw(path: Path) -> pd.DataFrame:
    """Read original Excel values, preserving identifiers as nullable strings."""
    if not path.is_file():
        raise FileNotFoundError(f"Raw workbook missing: {path}. Run quantiva download first.")
    frame = pd.read_excel(
        path, engine="openpyxl", dtype={"InvoiceNo": "string", "StockCode": "string"}
    )
    missing = set(COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Required columns missing: {sorted(missing)}")
    return frame[COLUMNS].copy()

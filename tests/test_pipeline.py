"""Verify idempotent artifact replacement and raw file preservation."""

import json

import pandas as pd

from quantiva.config import COLUMNS, Settings
from quantiva.ingestion import sha256
from quantiva.pipeline import prepare_data


def test_preparation_is_repeatable_and_leaves_raw_untouched(tmp_path):
    settings = Settings(tmp_path)
    settings.raw_file.parent.mkdir(parents=True)
    rows = [["1", "A", "Item", 2, "2011-01-01", 3, None, "UK"]]
    pd.DataFrame(rows + rows, columns=COLUMNS).to_excel(settings.raw_file, index=False)
    original_hash = sha256(settings.raw_file)
    first = prepare_data(settings)
    manifest = json.loads((settings.processed_dir / "manifest.json").read_text())
    second = prepare_data(settings)
    assert first == second
    assert manifest == json.loads((settings.processed_dir / "manifest.json").read_text())
    assert sha256(settings.raw_file) == original_hash
    ledger = pd.read_parquet(settings.processed_dir / "transactions.parquet")
    assert len(ledger) == 1
    assert ledger["line_revenue_gbp"].sum() == 6
    assert len(pd.read_parquet(settings.processed_dir / "exclusions.parquet")) == 1

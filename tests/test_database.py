"""Database constraints, atomic rebuilds, foreign keys, and provenance validation."""

import pandas as pd
import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from quantiva.cleaning import clean_transactions
from quantiva.config import COLUMNS, Settings
from quantiva.database import (
    build_database,
    database_content_digest,
    database_engine,
    load_verified_ledger,
)
from quantiva.ingestion import sha256


def test_schema_foreign_keys_and_anonymous_sales(analytical_database):
    engine = database_engine(analytical_database)
    try:
        assert set(inspect(engine).get_table_names()) == {
            "transactions",
            "invoices",
            "products",
            "customers",
            "countries",
            "dataset_metadata",
        }
        assert len(inspect(engine).get_indexes("transactions")) == 6
        with engine.connect() as connection:
            assert not connection.execute(text("PRAGMA foreign_key_check")).fetchall()
            assert connection.execute(text("SELECT COUNT(*) FROM transactions")).scalar_one() == 8
            assert (
                connection.execute(
                    text("SELECT COUNT(*) FROM completed_sales WHERE customer_id IS NULL")
                ).scalar_one()
                == 1
            )
            assert (
                connection.execute(
                    text("SELECT display_description FROM products WHERE stock_code='A'")
                ).scalar_one()
                == "New name"
            )
        with pytest.raises(IntegrityError), engine.begin() as connection:
            connection.execute(
                text("UPDATE transactions SET customer_id='absent' WHERE source_row=2")
            )
    finally:
        engine.dispose()


def test_rebuild_is_repeatable_and_invalid_rebuild_preserves_old_database(
    analytical_database, cleaning_result
):
    initial = sha256(analytical_database)
    content = database_content_digest(analytical_database)
    build_database(cleaning_result.ledger, analytical_database)
    assert database_content_digest(analytical_database) == content
    initial = sha256(analytical_database)
    bad = cleaning_result.ledger.copy()
    bad.loc[0, "StockCode"] = None
    with pytest.raises((IntegrityError, TypeError)):
        build_database(bad, analytical_database)
    assert sha256(analytical_database) == initial


def test_primary_key_and_monetary_constraints(analytical_database):
    engine = database_engine(analytical_database)
    try:
        for query in [
            "UPDATE transactions SET source_row=3 WHERE source_row=2",
            "UPDATE transactions SET revenue_units=999 WHERE source_row=2",
            "UPDATE transactions SET quantity=0 WHERE source_row=2",
            "UPDATE transactions SET transaction_type='made_up' WHERE source_row=2",
        ]:
            with pytest.raises(IntegrityError), engine.begin() as connection:
                connection.execute(text(query))
    finally:
        engine.dispose()


def test_empty_schema_and_invalid_input(tmp_path, cleaning_result):
    path = tmp_path / "empty.db"
    empty = clean_transactions(pd.DataFrame(columns=COLUMNS)).ledger
    assert build_database(empty, path)["transaction_lines"] == 0
    with pytest.raises(ValueError, match="columns missing"):
        build_database(pd.DataFrame(), path)
    with pytest.raises(ValueError, match="Duplicate source"):
        build_database(pd.concat([cleaning_result.ledger] * 2), path)
    bad = cleaning_result.ledger.copy()
    bad.loc[0, "is_completed_sale"] = False
    with pytest.raises(ValueError, match="eligibility flags"):
        build_database(bad, path)


def test_missing_manifest_is_actionable(tmp_path):
    with pytest.raises(FileNotFoundError, match="quantiva prepare"):
        load_verified_ledger(Settings(tmp_path))


def test_modified_processed_file_is_rejected(tmp_path):
    from quantiva.pipeline import prepare_data

    settings = Settings(tmp_path)
    settings.raw_file.parent.mkdir(parents=True)
    pd.DataFrame([["1", "A", "Item", 1, "2011-01-01", 1, None, "UK"]], columns=COLUMNS).to_excel(
        settings.raw_file, index=False
    )
    prepare_data(settings)
    assert len(load_verified_ledger(settings)) == 1
    with (settings.processed_dir / "transactions.parquet").open("ab") as stream:
        stream.write(b"changed")
    with pytest.raises(ValueError, match="checksum mismatch"):
        load_verified_ledger(settings)


def test_unsupported_monetary_precision_is_rejected(tmp_path, cleaning_result):
    bad = cleaning_result.ledger.copy()
    bad.loc[0, "UnitPrice"] = 1.00001
    with pytest.raises(ValueError, match="four decimal"):
        build_database(bad, tmp_path / "bad.db")


@pytest.mark.parametrize(
    "manifest",
    [
        {},
        [],
        {"outputs": None, "source_sha256": "invalid", "policy_version": "1.0.0"},
    ],
)
def test_malformed_manifest_is_reported_without_internal_key_errors(tmp_path, manifest):
    import json

    settings = Settings(tmp_path)
    settings.processed_dir.mkdir()
    (settings.processed_dir / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="Malformed processed manifest"):
        load_verified_ledger(settings)

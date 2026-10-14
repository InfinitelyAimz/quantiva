"""SQLite schema and atomic rebuilding from verified Phase 1 artifacts."""

import hashlib
import json
import logging
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import (
    URL,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    event,
    inspect,
    text,
)
from sqlalchemy.engine import Engine

from quantiva.config import Settings
from quantiva.ingestion import sha256

logger = logging.getLogger(__name__)
SCALE = 10_000
SCHEMA_VERSION = "2.0.0"
metadata = MetaData()
customers = Table("customers", metadata, Column("customer_id", String, primary_key=True))
countries = Table("countries", metadata, Column("country", String, primary_key=True))
products = Table(
    "products",
    metadata,
    Column("stock_code", String, primary_key=True),
    Column("display_description", String, nullable=True),
)
invoices = Table(
    "invoices",
    metadata,
    Column("invoice_no", String, primary_key=True),
    Column("is_cancelled", Boolean(create_constraint=True), nullable=False),
)
transactions = Table(
    "transactions",
    metadata,
    Column("source_row", Integer, primary_key=True, autoincrement=False),
    Column("invoice_no", ForeignKey("invoices.invoice_no"), nullable=False),
    Column("stock_code", ForeignKey("products.stock_code"), nullable=False),
    Column("customer_id", ForeignKey("customers.customer_id"), nullable=True),
    Column("country", ForeignKey("countries.country"), nullable=True),
    Column("invoice_date", DateTime, nullable=False),
    Column("description", String, nullable=True),
    Column("quantity", Integer, nullable=False),
    Column("unit_price_units", Integer, nullable=False),
    Column("revenue_units", Integer, nullable=False),
    Column("transaction_type", String, nullable=False),
    CheckConstraint("source_row >= 2", name="valid_source_row"),
    CheckConstraint("quantity != 0 AND typeof(quantity) = 'integer'", name="valid_quantity"),
    CheckConstraint("unit_price_units >= 0 AND typeof(unit_price_units) = 'integer'"),
    CheckConstraint("revenue_units = quantity * unit_price_units", name="line_amount_matches"),
    CheckConstraint(
        "transaction_type IN ('completed_sale','cancellation',"
        "'stock_adjustment_candidate','unlinked_negative','zero_value')"
    ),
    CheckConstraint(
        "(transaction_type != 'completed_sale') OR (quantity > 0 AND unit_price_units > 0)",
        name="eligible_sales",
    ),
    CheckConstraint("(transaction_type != 'cancellation') OR quantity < 0"),
    CheckConstraint(
        "(transaction_type != 'stock_adjustment_candidate') OR "
        "(quantity < 0 AND unit_price_units = 0)"
    ),
    CheckConstraint(
        "(transaction_type != 'zero_value') OR (quantity > 0 AND unit_price_units = 0)"
    ),
    CheckConstraint(
        "(transaction_type != 'unlinked_negative') OR (quantity < 0 AND unit_price_units > 0)"
    ),
)
for name, columns in {
    "ix_transaction_date": [transactions.c.invoice_date],
    "ix_transaction_invoice": [transactions.c.invoice_no],
    "ix_transaction_customer": [transactions.c.customer_id],
    "ix_transaction_product": [transactions.c.stock_code],
    "ix_transaction_country": [transactions.c.country],
    "ix_transaction_type_date": [transactions.c.transaction_type, transactions.c.invoice_date],
}.items():
    Index(name, *columns)
dataset_metadata = Table(
    "dataset_metadata",
    metadata,
    Column("key", String, primary_key=True),
    Column("value", String, nullable=False),
)


def database_engine(path: Path, *, require_exists: bool = True) -> Engine:
    """Open SQLite with foreign keys enabled on every connection."""
    if require_exists and not path.is_file():
        raise FileNotFoundError(f"Database missing: {path}. Run quantiva database first.")
    engine = create_engine(URL.create("sqlite", database=str(path)))

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    return engine


def load_verified_ledger(settings: Settings) -> pd.DataFrame:
    """Reject changed or incomplete source artifacts before import."""
    manifest_path = settings.processed_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError("Processed manifest missing. Run quantiva prepare first.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    required = {
        "transactions.parquet",
        "exclusions.parquet",
        "initial_inspection.json",
        "cleaning_report.json",
    }
    if set(manifest["outputs"]) != required:
        raise ValueError("Manifest does not describe the required Phase 1 outputs")
    if sha256(settings.raw_file) != manifest["source_sha256"]:
        raise ValueError("Raw workbook checksum differs from processed provenance")
    for name, digest in manifest["outputs"].items():
        if sha256(settings.processed_dir / name) != digest:
            raise ValueError(f"Processed checksum mismatch: {name}. Re-run quantiva prepare.")
    ledger = pd.read_parquet(settings.processed_dir / "transactions.parquet")
    report = json.loads((settings.processed_dir / "cleaning_report.json").read_text())
    if len(ledger) != report["cleaned_records"]:
        raise ValueError("Processed row count disagrees with cleaning report")
    return ledger


def build_database(ledger: pd.DataFrame, target: Path, provenance: dict | None = None) -> dict:
    """Build into a temporary sibling and replace only after successful checks.

    No append imports. A failed rebuild leaves the previous database intact.
    Callers must close existing database connections on Windows before rebuilding.
    """
    required = {
        "source_row",
        "InvoiceNo",
        "StockCode",
        "CustomerID",
        "Country",
        "InvoiceDate",
        "Description",
        "Quantity",
        "UnitPrice",
        "transaction_type",
        "is_cancelled",
        "is_completed_sale",
        "line_revenue_gbp",
    }
    if not required.issubset(ledger.columns):
        raise ValueError(f"Ledger columns missing: {sorted(required - set(ledger.columns))}")
    if ledger["source_row"].duplicated().any():
        raise ValueError("Duplicate source rows cannot be imported")
    expected_sales = ~ledger["is_cancelled"] & ledger["Quantity"].gt(0) & ledger["UnitPrice"].gt(0)
    if not np.array_equal(expected_sales, ledger["is_completed_sale"]):
        raise ValueError("Ledger eligibility flags do not match Phase 1 policy")
    if not np.array_equal(expected_sales, ledger["transaction_type"].eq("completed_sale")):
        raise ValueError("Ledger transaction types disagree with eligibility")
    price_scaled = ledger["UnitPrice"].to_numpy(dtype=float) * SCALE
    if not np.isfinite(price_scaled).all() or not np.allclose(
        price_scaled, np.rint(price_scaled), rtol=0, atol=1e-6
    ):
        raise ValueError("Prices must be finite and representable to four decimal GBP places")
    price_units = np.rint(price_scaled).astype("int64")
    revenue_units = ledger["Quantity"].to_numpy(dtype="int64") * price_units
    if not np.allclose(revenue_units / SCALE, ledger["line_revenue_gbp"], rtol=0, atol=1e-8):
        raise ValueError("Fixed-point amounts disagree with cleaned line revenue")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".db", delete=False) as temporary:
        temporary_path = Path(temporary.name)
    engine = database_engine(temporary_path)
    try:
        metadata.create_all(engine)
        with engine.begin() as connection:
            for table, column, source in [
                (customers, "customer_id", "CustomerID"),
                (countries, "country", "Country"),
            ]:
                records = [{column: str(v)} for v in sorted(ledger[source].dropna().unique())]
                if records:
                    connection.execute(table.insert(), records)
            # Latest known description; original descriptions remain at line grain.
            labels = (
                ledger.dropna(subset=["Description"])
                .sort_values(["InvoiceDate", "source_row"])
                .drop_duplicates("StockCode", keep="last")
                .set_index("StockCode")["Description"]
            )
            product_rows = [
                {"stock_code": str(code), "display_description": labels.get(code)}
                for code in sorted(ledger["StockCode"].unique())
            ]
            if product_rows:
                connection.execute(products.insert(), product_rows)
            invoice_rows = ledger[["InvoiceNo", "is_cancelled"]].drop_duplicates()
            if invoice_rows["InvoiceNo"].duplicated().any():
                raise ValueError("Invoice has contradictory cancellation flags")
            if not invoice_rows.empty:
                connection.execute(
                    invoices.insert(),
                    [
                        {"invoice_no": str(r.InvoiceNo), "is_cancelled": bool(r.is_cancelled)}
                        for r in invoice_rows.sort_values("InvoiceNo").itertuples(index=False)
                    ],
                )
            lines = ledger.sort_values("source_row").copy()
            lines["unit_price_units"] = pd.Series(price_units, index=ledger.index).loc[lines.index]
            lines["revenue_units"] = pd.Series(revenue_units, index=ledger.index).loc[lines.index]
            lines = lines.rename(
                columns={
                    "InvoiceNo": "invoice_no",
                    "StockCode": "stock_code",
                    "CustomerID": "customer_id",
                    "Country": "country",
                    "InvoiceDate": "invoice_date",
                    "Description": "description",
                    "Quantity": "quantity",
                }
            )
            columns = [column.name for column in transactions.columns]
            lines = lines[columns].astype(object).where(pd.notna(lines[columns]), None)
            for start in range(0, len(lines), 10_000):
                connection.execute(
                    transactions.insert(), lines.iloc[start : start + 10_000].to_dict("records")
                )
            connection.execute(
                text(
                    "CREATE VIEW completed_sales AS SELECT t.* FROM transactions t "
                    "INNER JOIN invoices i ON t.invoice_no=i.invoice_no "
                    "WHERE t.transaction_type='completed_sale' AND i.is_cancelled=0"
                )
            )
            info = {"schema_version": SCHEMA_VERSION, "rows": len(ledger), **(provenance or {})}
            connection.execute(
                dataset_metadata.insert(),
                [{"key": key, "value": json.dumps(value)} for key, value in sorted(info.items())],
            )
            if connection.execute(text("PRAGMA foreign_key_check")).fetchall():
                raise ValueError("Database foreign-key validation failed")
            count = connection.execute(text("SELECT COUNT(*) FROM transactions")).scalar_one()
            if count != len(ledger):
                raise ValueError("Database import row counts do not reconcile")
        with engine.connect() as connection:
            if connection.execute(text("PRAGMA integrity_check")).scalar_one() != "ok":
                raise ValueError("SQLite integrity check failed")
        engine.dispose()
        temporary_path.replace(target)
    finally:
        engine.dispose()
        temporary_path.unlink(missing_ok=True)
    summary = {
        "transaction_lines": len(ledger),
        "invoices": len(invoice_rows),
        "products": len(product_rows),
        "customers": int(ledger["CustomerID"].nunique()),
        "countries": int(ledger["Country"].nunique()),
    }
    logger.info("database_rebuild_complete summary=%s", json.dumps(summary))
    return summary


def rebuild_database(settings: Settings) -> dict:
    """Verify artifacts then atomically rebuild the local analytical database."""
    ledger = load_verified_ledger(settings)
    manifest = json.loads((settings.processed_dir / "manifest.json").read_text())
    return build_database(
        ledger,
        settings.database_file,
        {
            "source_sha256": manifest["source_sha256"],
            "ledger_sha256": manifest["outputs"]["transactions.parquet"],
            "policy_version": manifest["policy_version"],
        },
    )


def database_content_digest(path: Path) -> str:
    """Hash ordered schema definitions and rows, independent of SQLite page layout.

    Index creation order can change physical file bytes across Python processes.
    Reproducibility means identical schema/data, not identical internal page numbers.
    """
    digest = hashlib.sha256()
    engine = database_engine(path)
    try:
        with engine.connect() as connection:
            inspector = inspect(connection)
            # Canonical structural schema: constraint/index declaration order is irrelevant.
            for name in sorted(inspector.get_table_names()):
                schema = {
                    "name": name,
                    "columns": sorted(
                        [
                            (c["name"], str(c["type"]), c["nullable"], c["default"])
                            for c in inspector.get_columns(name)
                        ]
                    ),
                    "primary_key": inspector.get_pk_constraint(name)["constrained_columns"],
                    "foreign_keys": inspector.get_foreign_keys(name),
                    "checks": inspector.get_check_constraints(name),
                    "indexes": inspector.get_indexes(name),
                }
                for key in ["foreign_keys", "checks", "indexes"]:
                    schema[key] = sorted(
                        schema[key], key=lambda item: json.dumps(item, sort_keys=True)
                    )
                digest.update(json.dumps(schema, sort_keys=True).encode("utf-8"))
            for name in sorted(inspector.get_view_names()):
                digest.update(name.encode("utf-8"))
                digest.update(" ".join(inspector.get_view_definition(name).split()).encode("utf-8"))
            for name, table in sorted(metadata.tables.items()):
                digest.update(name.encode("utf-8"))
                keys = ",".join(column.name for column in table.primary_key.columns)
                for row in connection.execute(text(f"SELECT * FROM {name} ORDER BY {keys}")):
                    digest.update(json.dumps(list(row), separators=(",", ":")).encode("utf-8"))
                    digest.update(b"\n")
    finally:
        engine.dispose()
    return digest.hexdigest()

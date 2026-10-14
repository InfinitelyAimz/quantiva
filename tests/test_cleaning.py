"""Verify the business eligibility rules and complete audit accounting."""

import pandas as pd
import pytest

from quantiva.cleaning import clean_transactions
from quantiva.config import COLUMNS


def make_row(**changes):
    row = dict(zip(COLUMNS, ["100", "A", "Item", 2, "2011-01-01", 3.5, 123, "UK"], strict=True))
    row.update(changes)
    return row


def test_sales_anonymous_cancellation_and_adjustments_are_separate():
    raw = pd.DataFrame(
        [
            make_row(),
            make_row(InvoiceNo="101", CustomerID=None),
            make_row(InvoiceNo="C102", Quantity=-2),
            make_row(InvoiceNo="103", Quantity=-1, UnitPrice=0, Description="damaged"),
            make_row(InvoiceNo="104", Quantity=-1),
            make_row(InvoiceNo="105", UnitPrice=0),
        ]
    )
    ledger = clean_transactions(raw).ledger
    assert ledger["transaction_type"].tolist() == [
        "completed_sale",
        "completed_sale",
        "cancellation",
        "stock_adjustment_candidate",
        "unlinked_negative",
        "zero_value",
    ]
    assert ledger["is_completed_sale"].sum() == 2
    assert ledger["line_revenue_gbp"].tolist() == [7, 7, -7, 0, -3.5, 0]
    assert pd.isna(ledger.loc[1, "CustomerID"])
    assert ledger.loc[0, "CustomerID"] == "123"
    assert ledger.loc[2, "Quantity"] == -2


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"Quantity": 0}, "zero_quantity"),
        ({"Quantity": 1.5}, "invalid_quantity"),
        ({"Quantity": float("inf")}, "invalid_quantity"),
        ({"UnitPrice": -1}, "invalid_price"),
        ({"UnitPrice": float("inf")}, "invalid_price"),
        ({"InvoiceDate": "invalid"}, "invalid_timestamp"),
        ({"InvoiceNo": None}, "missing_invoice"),
        ({"StockCode": " "}, "missing_stock_code"),
        ({"InvoiceNo": "C1"}, "inconsistent_cancellation"),
    ],
)
def test_invalid_rows_are_audited(changes, reason):
    result = clean_transactions(pd.DataFrame([make_row(**changes)]))
    assert result.ledger.empty
    assert reason in result.exclusions.loc[0, "exclusion_reason"]
    assert result.report["quarantined_records"] == 1


def test_duplicate_removal_is_nonmutating_and_rows_reconcile():
    raw = pd.DataFrame([make_row(), make_row(), make_row(InvoiceNo="200", UnitPrice=-2)])
    original = raw.copy(deep=True)
    result = clean_transactions(raw)
    pd.testing.assert_frame_equal(raw, original)
    assert result.ledger["source_row"].tolist() == [2]
    assert result.exclusions["source_row"].tolist() == [3, 4]
    assert result.report["original_records"] == (
        result.report["cleaned_records"] + result.report["excluded_records"]
    )


@pytest.mark.parametrize("customer", [None, "not an ID", -1, 12.5, float("inf")])
def test_invalid_customer_does_not_remove_sales(customer):
    result = clean_transactions(pd.DataFrame([make_row(CustomerID=customer, Description=None)]))
    assert len(result.ledger) == 1
    assert result.ledger.loc[0, "is_completed_sale"]
    assert not result.ledger.loc[0, "has_valid_customer"]
    assert result.ledger.loc[0, "description_missing"]


def test_empty_input_has_stable_schema():
    result = clean_transactions(pd.DataFrame(columns=COLUMNS))
    assert result.ledger.empty
    assert result.exclusions.empty
    assert result.report["original_records"] == 0

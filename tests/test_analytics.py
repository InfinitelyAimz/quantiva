"""Hand-calculated KPI assertions independently constrain both implementations."""

import pandas as pd
import pytest
from sqlalchemy import text

from quantiva.analytics import (
    daily_calendar,
    describe_values,
    duplicate_sensitivity,
    monthly_calendar,
    pandas_kpis,
)
from quantiva.cleaning import clean_transactions
from quantiva.config import COLUMNS
from quantiva.database import build_database, database_engine
from quantiva.reconciliation import query_names, reconcile, run_query


def test_kpi_grains_and_revenue_filtering(cleaning_result, analytical_database):
    expected = {
        "gross_revenue_gbp": 21,
        "completed_orders": 3,
        "aov_gbp": 7,
        "units_sold": 9,
        "identifiable_customers": 1,
        "identifiable_revenue_gbp": 11,
        "revenue_per_identifiable_customer_gbp": 11,
        "repeat_customers": 1,
        "repeat_purchase_rate": 1,
    }
    assert pandas_kpis(cleaning_result.ledger) == expected
    assert run_query(analytical_database, "kpis").iloc[0]["gross_revenue_gbp"] == 21
    assert run_query(analytical_database, "average_order_value").iloc[0]["aov_gbp"] == 7
    assert reconcile(cleaning_result.ledger, analytical_database)["passed"].all()


def test_every_packaged_query_executes(analytical_database):
    for name in query_names():
        assert isinstance(run_query(analytical_database, name), pd.DataFrame)
    with pytest.raises(ValueError, match="Unknown query"):
        run_query(analytical_database, "../../private")


def test_reconciliation_detects_tampered_database(cleaning_result, analytical_database):
    engine = database_engine(analytical_database)
    try:
        with engine.begin() as connection:
            connection.execute(
                text("UPDATE transactions SET quantity=3,revenue_units=90000 WHERE source_row=2")
            )
    finally:
        engine.dispose()
    with pytest.raises(ValueError, match="reconciliation failed"):
        reconcile(cleaning_result.ledger, analytical_database)


def test_calendar_gaps_zero_sale_months_and_partial_periods(cleaning_result, analytical_database):
    daily = daily_calendar(cleaning_result.ledger).set_index("date")
    assert daily.loc["2011-01-02", "revenue_gbp"] == 0
    assert not daily.loc["2011-01-02", "has_transactions"]
    assert daily.loc["2011-03-03", "has_transactions"]
    assert daily.loc["2011-03-03", "boundary_day"]
    monthly = monthly_calendar(cleaning_result.ledger)
    assert monthly["complete_month"].tolist() == [True, True, False]
    assert monthly.loc[1, "growth_pct"] == -100
    assert pd.isna(monthly.loc[2, "growth_pct"])
    sql = run_query(analytical_database, "monthly_growth")
    assert sql["revenue_gbp"].tolist() == monthly["revenue_gbp"].tolist()
    assert sql["complete_month"].astype(bool).tolist() == monthly["complete_month"].tolist()
    assert sql.loc[1, "growth_pct"] == -100
    assert pd.isna(sql.loc[2, "growth_pct"])


def test_duplicate_sensitivity_respects_invoice_grain(cleaning_result):
    result = duplicate_sensitivity(cleaning_result.ledger, cleaning_result.exclusions).set_index(
        "metric"
    )
    assert result.loc["gross_revenue_gbp", "difference"] == 6
    assert result.loc["completed_orders", "difference"] == 0
    assert result.loc["aov_gbp", "duplicates_retained"] == 9
    assert result.loc["units_sold", "difference"] == 2


def test_empty_and_descriptive_statistics(tmp_path, cleaning_result):
    empty = cleaning_result.ledger.iloc[:0]
    path = tmp_path / "empty.db"
    build_database(empty, path)
    assert pandas_kpis(empty)["aov_gbp"] is None
    assert reconcile(empty, path)["passed"].all()
    assert daily_calendar(empty).empty
    assert monthly_calendar(empty).empty
    summary = describe_values(pd.Series([1, 2, 3]))
    assert summary["median"] == 2
    assert summary["mean"] == 2
    assert summary["variance"] == 1
    assert summary["iqr"] == 1
    assert describe_values(pd.Series([], dtype=float)) == {"count": 0}


def test_duplicate_sensitivity_does_not_restore_invalid_positive_lines():
    rows = [
        ["1", "A", "Item", 1, "2011-01-01", 2, None, "UK"],
        [None, "A", "Item", 1, "2011-01-01", 2, None, "UK"],
        ["2", "A", "Item", 1.5, "2011-01-01", 2, None, "UK"],
    ]
    cleaned = clean_transactions(pd.DataFrame(rows + rows, columns=COLUMNS))
    result = duplicate_sensitivity(cleaned.ledger, cleaned.exclusions).set_index("metric")
    assert result.loc["gross_revenue_gbp", "difference"] == 2
    assert result.loc["completed_orders", "difference"] == 0
    assert result.loc["units_sold", "difference"] == 1


@pytest.mark.parametrize(
    "column,new_value,metric",
    [
        ("StockCode", "REPLACED", "top_products"),
        ("Country", "REPLACED", "country_revenue"),
    ],
)
def test_reconciliation_rejects_mismatched_keys_even_when_totals_match(
    cleaning_result, analytical_database, column, new_value, metric
):
    changed = cleaning_result.ledger.copy()
    changed[column] = changed[column].where(changed[column].isna(), new_value)
    result = reconcile(changed, analytical_database, fail_on_difference=False)
    assert result.loc[result["metric"].eq("gross_revenue_gbp"), "passed"].all()
    assert not result.loc[result["metric"].str.startswith(metric + ":"), "passed"].all()
    with pytest.raises(ValueError, match="reconciliation failed"):
        reconcile(changed, analytical_database)

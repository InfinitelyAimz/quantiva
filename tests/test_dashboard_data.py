"""Filtered SQL correctness, empty scopes and invalidation after atomic rebuilds."""

from datetime import date

import pytest

from quantiva.dashboard.data import Filters, bundle, catalog, read_json, scope, signature
from quantiva.database import build_database


def test_full_and_filtered_kpis(analytical_database):
    info = catalog(analytical_database)
    data = bundle(analytical_database, Filters(info["start"], info["end"]))
    assert data["kpis"]["gross_revenue_gbp"] == 21
    assert data["kpis"]["completed_orders"] == 3
    assert data["kpis"]["repeat_purchase_rate"] == 1
    filtered = bundle(
        analytical_database, Filters(date(2011, 1, 1), date(2011, 1, 1), ("UK",), ("A",))
    )
    assert filtered["kpis"]["gross_revenue_gbp"] == 6
    assert filtered["kpis"]["completed_orders"] == 1
    assert filtered["kpis"]["units_sold"] == 2
    assert filtered["customers"].iloc[0]["frequency"] == 1
    assert filtered["products"]["stock_code"].tolist() == ["A"]
    assert filtered["countries"]["country"].tolist() == ["UK"]


def test_dates_gaps_and_empty_selection(analytical_database):
    data = bundle(analytical_database, Filters(date(2011, 1, 1), date(2011, 1, 3)))
    assert data["daily"]["revenue_gbp"].tolist() == [20, 0, 1]
    assert data["weekly"]["orders"].sum() == 3
    assert not data["monthly"]["complete_month"].any()
    assert data["monthly"]["growth_pct"].isna().all()
    complete = bundle(analytical_database, Filters(date(2011, 1, 1), date(2011, 3, 3)))
    gap = complete["weekly"].set_index("period").loc["2011-01-10"]
    assert gap["orders"] == 0 and gap["revenue_gbp"] == 0
    empty = bundle(analytical_database, Filters(date(2011, 1, 1), date(2011, 1, 3), ("FR",)))
    assert empty["kpis"]["completed_orders"] == 0
    assert empty["kpis"]["aov_gbp"] is None or empty["kpis"]["aov_gbp"] != empty["kpis"]["aov_gbp"]
    assert empty["customers"].empty
    assert len(empty["daily"]) == 3


def test_bound_values_cannot_inject_sql(analytical_database):
    f = Filters(date(2011, 1, 1), date(2011, 1, 3), ("UK' OR 1=1 --",))
    sql, params = scope(f)
    assert "OR 1=1" not in sql and "UK' OR 1=1 --" in params.values()
    assert bundle(analytical_database, f)["kpis"]["completed_orders"] == 0


def test_cache_changes_with_database_rebuild(analytical_database, cleaning_result):
    f = Filters(date(2011, 1, 1), date(2011, 3, 3))
    assert bundle(analytical_database, f)["kpis"]["gross_revenue_gbp"] == 21
    before = signature(analytical_database)
    changed = cleaning_result.ledger.copy()
    changed.loc[changed["is_completed_sale"], "Quantity"] *= 2
    changed["line_revenue_gbp"] = changed["Quantity"] * changed["UnitPrice"]
    build_database(changed, analytical_database)
    assert signature(analytical_database) != before
    assert bundle(analytical_database, f)["kpis"]["gross_revenue_gbp"] == 42


def test_bad_prerequisites_and_filters(analytical_database, tmp_path):
    with pytest.raises(FileNotFoundError):
        catalog(tmp_path / "missing.db")
    for f in [
        Filters(date(2011, 1, 3), date(2011, 1, 1)),
        Filters(date(2000, 1, 1), date(2011, 1, 1)),
    ]:
        with pytest.raises(ValueError):
            bundle(analytical_database, f)
    p = tmp_path / "bad.json"
    p.write_text("[]")
    with pytest.raises(ValueError):
        read_json(p)

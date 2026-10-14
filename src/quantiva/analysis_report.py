"""Generate measured Phase 2 findings, sensitivity, and descriptive tables."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import text

from quantiva.analytics import (
    daily_calendar,
    describe_values,
    duplicate_sensitivity,
    eligible_sales,
    monthly_calendar,
    pandas_kpis,
)
from quantiva.config import Settings
from quantiva.database import database_engine, load_verified_ledger
from quantiva.ingestion import sha256
from quantiva.reconciliation import query_names, reconcile, run_query


def collect_analysis(settings: Settings) -> dict:
    """Collect facts only after verifying source provenance and independent reconciliation."""
    ledger = load_verified_ledger(settings)
    if ledger.empty or not ledger["is_completed_sale"].any():
        raise ValueError("No eligible sales available for the full analytical report")
    engine = database_engine(settings.database_file)
    try:
        with engine.connect() as connection:
            info = {
                key: json.loads(value)
                for key, value in connection.execute(text("SELECT key,value FROM dataset_metadata"))
            }
            if info.get("ledger_sha256") != sha256(settings.processed_dir / "transactions.parquet"):
                raise ValueError("Database provenance is stale. Run quantiva database.")
            if connection.execute(text("PRAGMA foreign_key_check")).fetchall():
                raise ValueError("Foreign-key integrity failed")
    finally:
        engine.dispose()
    checks = reconcile(ledger, settings.database_file)
    queries = {name: run_query(settings.database_file, name) for name in query_names()}
    sales = eligible_sales(ledger)
    daily = daily_calendar(ledger)
    monthly = monthly_calendar(ledger)
    orders = queries["order_values"]
    customers = queries["customer_frequency"]
    products = queries["top_products"]
    countries = queries["country_revenue"]
    exclusions = pd.read_parquet(settings.processed_dir / "exclusions.parquet")
    sensitivity = duplicate_sensitivity(ledger, exclusions)
    quarantined = exclusions.loc[~exclusions["exclusion_reason"].eq("exact_duplicate")]
    negative_price_rows = quarantined.loc[
        pd.to_numeric(quarantined["UnitPrice"], errors="coerce").lt(0)
    ]
    quarantine_amount = float(
        (
            pd.to_numeric(negative_price_rows["Quantity"])
            * pd.to_numeric(negative_price_rows["UnitPrice"])
        ).sum()
    )
    statistics = {
        "order_value_gbp": describe_values(orders["revenue_gbp"]),
        "customer_spending_gbp": describe_values(customers["spending_gbp"]),
        "line_amount_gbp": describe_values(sales["line_revenue_gbp"]),
        "daily_revenue_calendar_gbp": describe_values(daily["revenue_gbp"]),
        "daily_revenue_observed_interior_gbp": describe_values(
            daily.loc[daily["has_transactions"] & ~daily["boundary_day"], "revenue_gbp"]
        ),
    }

    def corr(series1, series2, method):
        value = series1.corr(series2, method=method)
        return None if pd.isna(value) else float(value)

    # Pearson uses NumPy via pandas; rank-based Spearman avoids an extra dependency.
    correlations = {
        "invoice_units_value_pearson": corr(orders["units"], orders["revenue_gbp"], "pearson"),
        "invoice_units_value_rank": corr(
            orders["units"].rank(), orders["revenue_gbp"].rank(), "pearson"
        ),
        "customer_frequency_spending_pearson": corr(
            customers["frequency"], customers["spending_gbp"], "pearson"
        ),
        "customer_frequency_spending_rank": corr(
            customers["frequency"].rank(), customers["spending_gbp"].rank(), "pearson"
        ),
    }
    labels = ledger.groupby("StockCode")["Description"].nunique()
    product_behavior = pd.DataFrame(
        {"stock_code": labels.index, "distinct_descriptions": labels.values}
    )
    product_behavior["nonstandard_code_candidate"] = ~product_behavior["stock_code"].str.fullmatch(
        r"\d{5}[A-Za-z]{0,2}"
    )
    nonstandard = products.loc[~products["stock_code"].str.fullmatch(r"\d{5}[A-Za-z]{0,2}")]
    interior = daily.loc[~daily["boundary_day"]].copy()
    weekdays = (
        interior.groupby("weekday")
        .agg(
            calendar_days=("date", "count"),
            observed_days=("has_transactions", "sum"),
            mean_calendar_revenue_gbp=("revenue_gbp", "mean"),
            median_calendar_revenue_gbp=("revenue_gbp", "median"),
        )
        .reindex(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    )
    order_outliers = orders.loc[
        orders["revenue_gbp"].gt(
            statistics["order_value_gbp"]["q3"] + 1.5 * statistics["order_value_gbp"]["iqr"]
        )
    ]
    upper_order_cutoff = orders["revenue_gbp"].quantile(0.99)
    outliers = {
        "tukey_upper_fence_gbp": statistics["order_value_gbp"]["q3"]
        + 1.5 * statistics["order_value_gbp"]["iqr"],
        "above_tukey_fence_orders": len(order_outliers),
        "mean_orders_at_or_below_p99_gbp": float(
            orders.loc[orders["revenue_gbp"].le(upper_order_cutoff), "revenue_gbp"].mean()
        ),
        "top_one_percent_order_share_pct": float(
            100
            * orders.loc[orders["revenue_gbp"].gt(upper_order_cutoff), "revenue_gbp"].sum()
            / orders["revenue_gbp"].sum()
        ),
        "max_quantity": int(sales["Quantity"].max()),
        "max_unit_price_gbp": float(sales["UnitPrice"].max()),
    }
    # Aggregate cancellation evidence for extreme quantities without declaring matched returns.
    extreme = ledger.loc[ledger["Quantity"].abs().ge(sales["Quantity"].quantile(0.999))]
    extreme_groups = (
        extreme.groupby(["StockCode", "Quantity", "transaction_type"], dropna=False)
        .agg(lines=("source_row", "count"), signed_amount_gbp=("line_revenue_gbp", "sum"))
        .reset_index()
    )
    kpis = pandas_kpis(ledger)
    concentration = {
        "top_10_products_share_pct": float(products.head(10)["revenue_share_pct"].sum()),
        "top_100_products_share_pct": float(products.head(100)["revenue_share_pct"].sum()),
        "top_10_customers_known_revenue_share_pct": float(
            customers.head(10)["spending_gbp"].sum() / customers["spending_gbp"].sum() * 100
        ),
        "uk_revenue_share_pct": float(
            countries.loc[countries["country"].eq("United Kingdom"), "revenue_share_pct"].sum()
        ),
        "anonymous_revenue_share_pct": float(
            (kpis["gross_revenue_gbp"] - kpis["identifiable_revenue_gbp"])
            / kpis["gross_revenue_gbp"]
            * 100
        ),
        "nonstandard_code_revenue_gbp": float(nonstandard["revenue_gbp"].sum()),
    }
    coverage = {
        "start": str(ledger["InvoiceDate"].min()),
        "end": str(ledger["InvoiceDate"].max()),
        "calendar_days": len(daily),
        "observed_days": int(daily["has_transactions"].sum()),
        "no_transaction_dates": daily.loc[~daily["has_transactions"], "date"]
        .dt.strftime("%Y-%m-%d")
        .tolist(),
        "missing_days_by_weekday": daily.loc[~daily["has_transactions"], "weekday"]
        .value_counts()
        .to_dict(),
        "partial_calendar_months": monthly.loc[~monthly["complete_month"], "month"].tolist(),
        "multi_timestamp_invoices": int(
            ledger.groupby("InvoiceNo")["InvoiceDate"].nunique().gt(1).sum()
        ),
        "products_with_multiple_descriptions": int(labels.gt(1).sum()),
    }
    summary = {
        "quality_sensitivity": {
            "quarantined_negative_price_rows": len(negative_price_rows),
            "quarantined_negative_price_signed_gbp": quarantine_amount,
        },
        "kpis": kpis,
        "statistics": statistics,
        "correlations": correlations,
        "concentration": concentration,
        "coverage": coverage,
        "outliers": outliers,
        "database_counts": {
            "transaction_lines": len(ledger),
            "invoices": int(ledger["InvoiceNo"].nunique()),
            "products": int(ledger["StockCode"].nunique()),
            "customers": int(ledger["CustomerID"].nunique()),
            "countries": int(ledger["Country"].nunique()),
        },
        "reconciliation": {
            "comparisons": len(checks),
            "all_passed": bool(checks["passed"].all()),
            "max_absolute_difference": float(checks["absolute_difference"].max()),
        },
    }
    return {
        "summary": summary,
        "ledger": ledger,
        "sales": sales,
        "queries": queries,
        "daily": daily,
        "monthly": monthly,
        "orders": orders,
        "customers": customers,
        "products": products,
        "countries": countries,
        "sensitivity": sensitivity,
        "reconciliation": checks,
        "weekdays": weekdays,
        "product_behavior": product_behavior,
        "nonstandard": nonstandard,
        "extreme_groups": extreme_groups,
    }


def markdown_table(frame: pd.DataFrame, *, decimals: int = 2) -> str:
    """Write small Markdown tables without an optional tabulate dependency."""

    def value(v):
        if pd.isna(v):
            return "—"
        if isinstance(v, (float, np.floating)):
            return f"{v:,.{decimals}f}"
        return str(v).replace("|", "/").replace("\n", " ")

    header = "| " + " | ".join(str(c) for c in frame.columns) + " |"
    separator = "| " + " | ".join("---" for _ in frame.columns) + " |"
    rows = [
        "| " + " | ".join(value(v) for v in r) + " |"
        for r in frame.itertuples(index=False, name=None)
    ]
    return "\n".join([header, separator, *rows])


def write_analysis(settings: Settings, reports_dir: Path) -> dict:
    """Generate reports and figures from actual calculations; fail on reconciliation errors."""
    result = collect_analysis(settings)
    reports_dir.mkdir(parents=True, exist_ok=True)
    summary = result["summary"]
    (reports_dir / "phase_2_metrics.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    result["reconciliation"].to_csv(reports_dir / "reconciliation.csv", index=False)
    result["sensitivity"].to_csv(reports_dir / "duplicate_sensitivity.csv", index=False)
    result["monthly"].to_csv(reports_dir / "monthly_revenue.csv", index=False)
    from quantiva.visualization import create_figures

    create_figures(result, reports_dir / "figures")
    k = summary["kpis"]
    stats = summary["statistics"]
    concentration = summary["concentration"]
    growth = result["monthly"].dropna(subset=["growth_pct"])
    changes = growth.sort_values("growth_pct")
    cancellation = result["queries"]["adjustments"]
    cancellation_amount = float(
        cancellation.loc[
            cancellation["transaction_type"].eq("cancellation"), "signed_amount_gbp"
        ].sum()
    )
    top_product_table = markdown_table(
        result["products"][
            ["stock_code", "display_description", "revenue_gbp", "units", "revenue_share_pct"]
        ].head(10)
    )
    slow_product_table = markdown_table(
        result["products"]
        .sort_values(["units", "stock_code"])
        .head(10)[["stock_code", "display_description", "units", "orders"]]
    )
    correlation_table = markdown_table(
        pd.DataFrame(
            [
                {"relationship": key, "correlation": value}
                for key, value in summary["correlations"].items()
            ]
        )
    )
    findings = f"""# Phase 2 — measured analytical findings

Generated by `quantiva analyze` from verified Phase 1 Parquet artifacts and SQLite.
All required queries execute before this report is written. Monetary results below
are GBP. Definitions are in [kpi_specification.md](kpi_specification.md).

## Business KPIs

{markdown_table(pd.DataFrame([{"metric": key, "value": value} for key, value in k.items()]))}

Gross eligible revenue is **£{k["gross_revenue_gbp"]:,.2f}**, across
**{k["completed_orders"]:,} distinct invoices**, not transaction lines. AOV is
**£{k["aov_gbp"]:,.2f}**. Identifiable customers account for
£{k["identifiable_revenue_gbp"]:,.2f}; anonymous sales supply
{concentration["anonymous_revenue_share_pct"]:.2f}% of gross revenue. Revenue per
identifiable customer uses only that identifiable revenue. Repeat purchase rate is
{k["repeat_purchase_rate"]:.2%} within this observation period; it is not cohort retention.

## Revenue trend and calendar coverage

{markdown_table(result["monthly"])}

Among comparable adjacent full months, growth ranges from
{changes.iloc[0]["growth_pct"]:.2f}% in {changes.iloc[0]["month"]} to
{changes.iloc[-1]["growth_pct"]:.2f}% in {changes.iloc[-1]["month"]}.
These changes describe this retailer's activity; one year cannot establish stable
annual seasonality. December 2011 is truncated on 9 December at 12:50 and has no
published month-over-month growth. December 2010 lies inside the observation span,
but its Christmas gap does not prove complete transaction capture.

There are {summary["coverage"]["calendar_days"]} calendar dates and
{summary["coverage"]["observed_days"]} dates with any ledger activity. Missing
dates by weekday: {summary["coverage"]["missing_days_by_weekday"]}.
Zero recorded amounts on missing dates are not proof of zero demand. The weekday
chart includes all interior calendar dates and shows the denominator explicitly.

![Daily revenue](figures/daily_revenue.png)

Interpretation: the daily series includes calendar gaps and occasional large spikes.
Boundary dates are marked; the final day is incomplete. Investigate spikes before
using them as routine expected demand.

![Monthly revenue](figures/monthly_revenue.png)

Interpretation: compare the full-month bars; the partial final month is highlighted
and should not be read as a comparable collapse in monthly sales.

## Products

{top_product_table}

Top ten product codes contribute {concentration["top_10_products_share_pct"]:.2f}%
of gross revenue; the top 100 contribute {concentration["top_100_products_share_pct"]:.2f}%.
There are {summary["coverage"]["products_with_multiple_descriptions"]} stock codes
with multiple descriptions in the ledger. Product names are labels, not identifiers.
The SQL product label is the most recent nonmissing description; original labels remain on lines.

Highest-volume codes:

{markdown_table(result["queries"]["top_product_units"].head(10))}

Slow-moving codes (lowest positive units in eligible sales; ties sorted by code):

{slow_product_table}

They are low-volume codes in this finite window, not proven failed products; availability
and introduction dates are unknown. Codes with no eligible sales are not ranked as sellers.

![Top products](figures/top_products.png)

Interpretation: code-level revenue concentration highlights the main revenue contributors;
gross rankings can be influenced by exceptional bulk orders and charges.

![Product concentration](figures/product_concentration.png)

Interpretation: the cumulative curve quantifies how unevenly revenue is distributed
across selling product codes. The curve includes every eligible code.

Nonstandard-code candidates use a syntax heuristic (outside five digits plus up to
two letters). They contribute £{concentration["nonstandard_code_revenue_gbp"]:,.2f}.
This is an investigation list, not a verified merchandise taxonomy:

{markdown_table(result["nonstandard"][["stock_code", "display_description", "revenue_gbp"]])}

## Customers and geography

Top ten identifiable customers contribute
{concentration["top_10_customers_known_revenue_share_pct"]:.2f}% of known-customer
revenue. Purchase frequency is distinct eligible invoices, not lines. High spending
can reflect wholesale ordering; missing identifiers limit generalization to all shoppers.
Top customer spending ranges and ranks can be inspected locally with `quantiva query top_customers`.

![Customer spending](figures/customer_spending.png)

Interpretation: the log-transformed spending distribution makes the long tail visible
without dropping high-spending customers. Values are transformed for plotting only.

{markdown_table(result["countries"].head(10))}

UK share is {concentration["uk_revenue_share_pct"]:.2f}% and international/other share is
{100 - concentration["uk_revenue_share_pct"]:.2f}%. Country order distribution is in the
table. These are descriptive contributions, not estimates of population demand or
causal country effects.

![Country revenue](figures/country_revenue.png)

Interpretation: the source retailer is strongly concentrated in the UK. Small-country
comparisons are influenced by customer mix and cannot be generalized to national markets.

## Descriptive statistics and outliers

{markdown_table(pd.DataFrame(stats).T.reset_index().rename(columns={"index": "observation_grain"}))}

Invoice mean £{stats["order_value_gbp"]["mean"]:,.2f} versus median
£{stats["order_value_gbp"]["median"]:,.2f} indicates a right tail; invoice skewness is
{stats["order_value_gbp"]["skewness"]:.2f}. Sample standard deviation describes dispersion
in observed values, not forecast uncertainty. Invoice IQR is
£{stats["order_value_gbp"]["iqr"]:,.2f}. {summary["outliers"]["above_tukey_fence_orders"]:,}
invoices lie above the Tukey upper fence; this is a diagnostic flag, not an error rule.
The mean at or below the 99th percentile is
£{summary["outliers"]["mean_orders_at_or_below_p99_gbp"]:,.2f}, versus the full AOV.
Orders above that percentile contribute
{summary["outliers"]["top_one_percent_order_share_pct"]:.2f}% of gross revenue.

![Order distribution](figures/order_values.png)

Interpretation: log10(1 + GBP) keeps every positive eligible invoice and reveals
skewness. The lower mean in the sensitivity subset shows how extremes affect averages;
the subset does not replace reported revenue or AOV.

![Calendar pattern](figures/weekday_revenue.png)

Interpretation: weekday averages use interior calendar dates, including missing-record
dates as zero observed activity. They describe the recorded schedule, not causal
weekday effects or verified opening hours.

Correlations at matched grains:

{correlation_table}

Pearson measures linear association; rank correlation is less sensitive to magnitude
extremes. Units/value and frequency/spending have mechanical relationships because
value accumulates with purchases. These associations do not imply causality.

Maximum eligible quantity is {summary["outliers"]["max_quantity"]:,}; maximum price is
£{summary["outliers"]["max_unit_price_gbp"]:,.2f}. Notebook diagnostics show cancellation
counter-record candidates at extreme quantities without asserting one-to-one matches.

## Data-quality sensitivity

{markdown_table(result["sensitivity"])}

Retaining eligible exact duplicate rows changes sales amounts and units while distinct
invoice counting protects order totals. Identical rows could be legitimate repeated
items; the source lacks a unique line key. This sensitivity quantifies that assumption.

{markdown_table(cancellation)}

Signed cancellation-related movements are **£{cancellation_amount:,.2f}**. Adding them
to gross sales gives **£{k["gross_revenue_gbp"] + cancellation_amount:,.2f}** as an unmatched
signed-movement sensitivity, **not accounting net revenue**. Noncancelled negative
zero-price rows remain stock-adjustment candidates. Zero-price positive lines remain
outside completed-sales KPIs. There are
{summary["quality_sensitivity"]["quarantined_negative_price_rows"]}
quarantined negative-price records total
£{summary["quality_sensitivity"]["quarantined_negative_price_signed_gbp"]:,.2f} in raw line value;
their source descriptions are inspected in the notebook and are not treated as ordinary sales.

## Independent validation and limitations

{summary["reconciliation"]["comparisons"]:,} SQL/pandas comparisons passed, including
every monthly, geographic, and selling-product revenue group. Maximum absolute
difference is {summary["reconciliation"]["max_absolute_difference"]:.12g}; see
[reconciliation.csv](reconciliation.csv). Count checks are exact, monetary checks use
absolute tolerance 0.000001 GBP, and absent keys fail independently of amount.

No matched-return net accounting, profit, cohort retention, annual seasonality,
causal inference, forecasts, or RFM segments are claimed. Potential service/charge
codes remain included and labelled. Missing customers, unusual wholesale quantities,
incomplete observation boundaries, and missing dates must inform Phase 3 decisions.
"""
    (reports_dir / "findings.md").write_text(findings, encoding="utf-8")
    return summary

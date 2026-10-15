"""Readable UI labels and tables; machine-readable exports keep their source identifiers."""

from html import escape

import pandas as pd

MODEL_NAMES = {
    "random_forest": "Random Forest",
    "seasonal_naive": "Weekly Seasonal Naive",
    "naive": "Naive",
    "linear_regression": "Linear Regression",
}
LABELS = {
    "gross_revenue": "Gross completed sales",
    "revenue": "Revenue",
    "monetary": "Recorded spend",
    "prediction": "Predicted sales",
    "actual": "Recorded sales",
    "aov": "Average order value",
    "order_value": "Order value",
    "residual": "Prediction − recorded",
    "absolute_error": "Absolute error",
    "mae": "MAE",
    "rmse": "RMSE",
    "bias": "Forecast bias",
    "wape_pct": "WAPE",
    "growth_pct": "Monthly growth",
    "change_pct": "Change",
    "recency_days": "Recency (days)",
    "median_recency": "Median recency (days)",
    "median_frequency": "Median invoices",
    "frequency": "Distinct invoices",
    "rfm_score": "RFM Score",
    "r_score": "R score",
    "f_score": "F score",
    "m_score": "M score",
    "customer_id": "Customer ID",
    "invoice_no": "Invoice",
    "stock_code": "Stock code",
    "customers": "Customers",
    "orders": "Orders",
    "units": "Units",
    "units_sold": "Units sold",
    "completed_orders": "Completed orders",
    "complete_month": "Month coverage",
    "horizon": "Forecast day",
    "training_cutoff": "Training cutoff",
    "forecast_origin": "Forecast origin",
    "last_purchase": "Last purchase",
    "ledger_lines": "Recorded lines",
    "missing": "Missing values",
    "dates": "Dates",
    "deduplicated": "Duplicates excluded",
    "duplicates_retained": "Duplicates retained",
    "type": "Transaction type",
    "reason": "Exclusion reason",
    "field": "Field",
    "observations": "Days evaluated",
    "series": "Sales series",
    "experiment": "Scenario",
}
VALUES = {
    "actual_gbp": "Recorded sales",
    "prediction_gbp": "Predicted sales",
    "completed_sale": "Completed sales",
    "cancellation": "Cancellations",
    "stock_adjustment_candidate": "Adjustment candidates",
    "unlinked_negative": "Other negatives",
    "zero_value": "Zero-value lines",
    "exact_duplicate": "Exact duplicates",
    "negative_price": "Negative prices",
}
INTEGER_COLUMNS = {
    "customers",
    "orders",
    "completed_orders",
    "units",
    "units_sold",
    "frequency",
    "recency_days",
    "rfm_score",
    "r_score",
    "f_score",
    "m_score",
    "observations",
    "horizon",
    "passed",
    "failed",
    "lines",
    "missing",
    "dates",
}


def label(name: str) -> str:
    """Make acronyms/units explicit without changing technical column identifiers."""
    for code in ["GBP", "ZAR"]:
        if name.endswith("_" + code.lower()):
            base = name[:-4]
            suffix = "/day" if base in {"mae", "rmse", "bias"} else ""
            return f"{LABELS.get(base, base.replace('_', ' ').title())} ({code}{suffix})"
    return LABELS.get(name, name.replace("_", " ").title())


def friendly_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Use friendly values in the UI only; never apply this to CSV export frames."""
    shown = frame.copy(deep=True)
    for column in ["model", "series", "type", "reason", "experiment"]:
        if column in shown:
            shown[column] = shown[column].map(
                lambda value: MODEL_NAMES.get(
                    value, VALUES.get(value, str(value).replace("_", " "))
                )
            )
    if "metric" in shown:
        shown["metric"] = shown["metric"].map(label)
    if "complete_month" in shown:
        shown["complete_month"] = shown["complete_month"].map(
            {True: "Complete month", False: "Partial month"}
        )
    return shown


def table_html(frame: pd.DataFrame) -> str:
    """Bounded input, escaped values, scoped headers and right-aligned numeric cells."""
    shown = friendly_frame(frame)
    headers = "".join(f'<th scope="col">{escape(label(str(c)))}</th>' for c in shown)
    rows = []
    for values in shown.itertuples(index=False, name=None):
        cells = []
        for column, value in zip(shown.columns, values, strict=True):
            numeric = isinstance(value, (int, float)) and not isinstance(value, bool)
            if pd.isna(value):
                text = "Not available"
            elif numeric:
                text = f"{value:,.0f}" if column in INTEGER_COLUMNS else f"{value:,.2f}"
                if column.endswith("_pct"):
                    text += "%"
            else:
                text = str(value)
            cells.append(f'<td class="{"q-number" if numeric else "q-text"}">{escape(text)}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return (
        '<div class="q-table" tabindex="0" role="region" aria-label="Scrollable data table">'
        f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
    )


def log_monetary_available(values: pd.Series) -> bool:
    """Never silently drop non-positive observations from a logarithmic plot."""
    return bool(not values.empty and values.notna().all() and values.gt(0).all())

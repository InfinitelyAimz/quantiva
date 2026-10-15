"""Five BI views using shared calculations and components."""

from datetime import timedelta

import pandas as pd
import streamlit as st

from quantiva.config import Settings
from quantiva.dashboard.components import chart, filters, heading, kpi_cards, table
from quantiva.dashboard.currency import currency_state
from quantiva.dashboard.data import bundle, read_json
from quantiva.dashboard.evidence import load_evidence
from quantiva.dashboard.presentation import MODEL_NAMES, log_monetary_available
from quantiva.forecast_evaluation import summarize_predictions
from quantiva.ingestion import sha256
from quantiva.model_artifacts import forecast_saved, load_artifact, verify_artifact
from quantiva.segmentation import build_rfm

SALES_KPIS = {
    "gross_revenue_gbp": ("Gross completed sales", "gbp"),
    "completed_orders": ("Completed orders", "count"),
    "aov_gbp": ("Average order value", "gbp"),
    "units_sold": ("Units sold", "count"),
    "identifiable_customers": ("Identifiable purchasers", "count"),
    "repeat_purchase_rate": ("Within-period repeat rate", "pct"),
}


def overview(settings: Settings, root) -> None:
    currency = currency_state(st.session_state)
    heading(
        "Overview",
        "Recorded retail performance, customer activity and revenue concentration.",
    )
    selected = filters(settings.database_file)
    data = bundle(settings.database_file, selected)
    kpi_cards(data["kpis"], SALES_KPIS)
    if not data["kpis"]["completed_orders"]:
        st.info("No eligible sales match these filters. Broaden the dates or countries.")
        return
    a, b = st.columns([3, 2])
    with a:
        chart(
            data["monthly"].assign(
                month_coverage=data["monthly"]["complete_month"].map(
                    {True: "Complete month", False: "Partial month"}
                )
            ),
            "period",
            "revenue_gbp",
            "Monthly gross sales",
            currency=True,
            color="month_coverage",
            labels={
                "period": "Month",
                "revenue_gbp": "Gross sales (GBP)",
                "month_coverage": "Coverage",
            },
        )
        st.caption("Partial months are highlighted and should not be compared as full months.")
    with b:
        chart(
            data["countries"].head(8),
            "revenue_gbp",
            "country",
            "Revenue by country",
            labels={"revenue_gbp": "Gross sales (GBP)", "country": "Country"},
            category_orders={"country": data["countries"].head(8)["country"].tolist()},
        )
    chart(
        data["daily"],
        "period",
        "revenue_gbp",
        "Daily recorded eligible sales",
        kind="line",
        currency=True,
        labels={"period": "Calendar date", "revenue_gbp": "Observed gross sales (GBP)"},
    )
    st.caption(
        "Missing dates show zero recorded sales; they do not establish zero underlying demand."
    )
    a, b = st.columns(2)
    with a:
        chart(
            data["products"].head(8),
            "stock_code",
            "revenue_gbp",
            "Leading product codes",
            currency=True,
            hover_data=["description"],
            labels={"stock_code": "Stock code", "revenue_gbp": "Gross sales (GBP)"},
        )
    with b:
        chart(
            data["orders"],
            "order_value_gbp",
            None,
            "Order-value distribution",
            kind="histogram",
            nbins=45,
            labels={"order_value_gbp": "Recorded order value (GBP)"},
        )
    st.subheader("What the data says")
    full = data["monthly"].loc[data["monthly"]["complete_month"]]
    if not full.empty:
        best = full.loc[full["revenue_gbp"].idxmax()]
        st.write(
            f"**{best['period']}** is the highest complete month in this scope, "
            f"at {currency.money(best['revenue_gbp'])}."
        )
    k = data["kpis"]
    share = data["products"].head(10)["revenue_gbp"].sum() / k["gross_revenue_gbp"]
    st.write(
        f"The ten leading stock codes contribute **{share:.1%}** of selected revenue. "
        f"Anonymous purchases contribute "
        f"**{currency.money(k['gross_revenue_gbp'] - k['identifiable_revenue_gbp'])}**; "
        "customer analytics cover identifiable purchasers only."
    )
    st.caption(
        "Coverage: 1 Dec 2010–9 Dec 2011; December 2011 is partial. "
        "Source timestamps are wall time. Charges/postage remain eligible;"
        " gross sales are not profit or accounting net revenue. "
        "Zero observed dates do not prove zero demand. Charts describe "
        "association, not causation."
    )


def sales(settings: Settings, root) -> None:
    currency = currency_state(st.session_state)
    heading(
        "Sales Analytics",
        "Explore when sales were recorded and which products and countries contributed.",
    )
    selected = filters(settings.database_file, product=True)
    data = bundle(settings.database_file, selected)
    kpi_cards(
        data["kpis"],
        {k: SALES_KPIS[k] for k in ["gross_revenue_gbp", "completed_orders", "aov_gbp"]},
    )
    a, b = st.columns(2)
    period = a.selectbox("Time aggregation", ["daily", "weekly", "monthly"], format_func=str.title)
    metric = b.selectbox(
        "Trend metric",
        ["revenue_gbp", "orders", "units", "aov_gbp"],
        format_func=lambda x: {
            "revenue_gbp": "Gross revenue",
            "orders": "Distinct orders",
            "units": "Units sold",
            "aov_gbp": "Average order value",
        }[x],
    )
    chart(
        data[period],
        "period",
        metric,
        "Sales through time",
        kind="line",
        currency=metric.endswith("gbp"),
        labels={"period": "Observation period", metric: metric.replace("_", " ").title()},
    )
    st.caption(
        "Weekly periods start Monday; boundary weeks can be partial. Empty"
        " daily dates mean zero recorded revenue. "
        "Distinct orders are counted within each chosen period, not summed"
        " across daily rows."
    )
    st.subheader("Products & concentration")
    ranking = st.radio(
        "Rank products by",
        ["revenue_gbp", "units"],
        horizontal=True,
        format_func={"revenue_gbp": f"Revenue ({currency.code})", "units": "Units sold"}.get,
    )
    products = data["products"].sort_values(ranking, ascending=False)
    chart(
        products.head(15),
        "stock_code",
        ranking,
        "Top product codes",
        currency=ranking.endswith("gbp"),
        hover_data=["description"],
    )
    total = products["revenue_gbp"].sum()
    st.caption(
        f"Top ten revenue share: "
        f"{products.nlargest(10, 'revenue_gbp')['revenue_gbp'].sum() / total:.1%}"
        if total
        else "No eligible product revenue."
    )
    st.caption(
        "Descriptions are labels; stock codes are identifiers. Nonstandard"
        " codes may represent charges or manual entries."
    )
    table(products)
    st.subheader("Geographic comparison")
    metric = st.radio(
        "Country metric",
        ["revenue_gbp", "orders"],
        horizontal=True,
        format_func={"revenue_gbp": f"Revenue ({currency.code})", "orders": "Distinct orders"}.get,
    )
    chart(
        data["countries"],
        "country",
        metric,
        "Recorded activity by country",
        currency=metric.endswith("gbp"),
        category_orders={
            "country": data["countries"].sort_values(metric, ascending=False)["country"].tolist()
        },
    )
    countries = data["countries"]
    if not countries.empty and total:
        st.caption(
            f"Largest country's revenue share: {countries.iloc[0]['revenue_gbp'] / total:.1%}. "
            "Country is source billing geography, not a causal sales driver."
        )
    table(countries)
    st.subheader("Monthly growth & coverage")
    table(data["monthly"])
    st.caption(
        "Growth is shown only between adjacent complete months within "
        "source coverage AND selected dates. "
        "Large wholesale orders are retained; spikes are not automatically invalid."
    )


def customers(settings: Settings, root) -> None:
    heading(
        "Customer Intelligence",
        "Understand identifiable purchasing activity and descriptive customer segments.",
    )
    selected = filters(settings.database_file)
    data = bundle(settings.database_file, selected)
    kpi_cards(
        data["kpis"],
        {
            k: (label, unit)
            for k, label, unit in [
                ("identifiable_customers", "Identifiable purchasers", "count"),
                ("identifiable_revenue_gbp", "Known-customer revenue", "gbp"),
                ("revenue_per_identifiable_customer_gbp", "Revenue per purchaser", "gbp"),
                ("repeat_customers", "Repeat purchasers", "count"),
                ("repeat_purchase_rate", "Within-period repeat rate", "pct"),
            ]
        },
    )
    reference = pd.Timestamp(selected.end + timedelta(days=1))
    rfm = build_rfm(data["customers"], reference)
    st.caption(
        f"RFM reference date: {reference.date()} (day after filter end). "
        "Scores are recalculated within the selected dates/countries. "
        "Segment selection below affects only RFM charts/tables, not the "
        "customer KPI cards above."
    )
    if rfm.empty:
        st.info(
            "No identifiable eligible purchasers in this scope. Anonymous "
            "sales are excluded from RFM."
        )
        return
    picked = st.multiselect("Customer segments · empty means all", sorted(rfm["segment"].unique()))
    shown = rfm.loc[rfm["segment"].isin(picked)] if picked else rfm
    summary = shown.groupby("segment", as_index=False).agg(
        customers=("customer_id", "count"),
        revenue_gbp=("monetary_gbp", "sum"),
        median_recency=("recency_days", "median"),
        median_frequency=("frequency", "median"),
    )
    a, b = st.columns(2)
    with a:
        chart(
            summary.sort_values("customers", ascending=False),
            "customers",
            "segment",
            "Customers by segment",
            color="segment",
            showlegend=False,
            category_orders={
                "segment": summary.sort_values("customers", ascending=False)["segment"].tolist()
            },
            text="customers",
        )
    with b:
        chart(
            summary.sort_values("revenue_gbp", ascending=False),
            "revenue_gbp",
            "segment",
            "Recorded revenue by segment",
            color="segment",
            showlegend=False,
            category_orders={
                "segment": summary.sort_values("revenue_gbp", ascending=False)["segment"].tolist()
            },
        )
    st.subheader("Purchasing patterns")
    scale = st.radio("Monetary axis", ["Logarithmic", "Linear"], horizontal=True)
    use_log = scale == "Logarithmic" and log_monetary_available(shown["monetary_gbp"])
    if scale == "Logarithmic" and not use_log:
        st.warning(
            "Logarithmic axes require positive values. Showing all customers on a linear axis."
        )
    st.caption(
        "Logarithmic spacing compares multiples of spend and makes dense groups easier to see. "
        "Hover values remain in the selected currency; no outliers are removed."
        if use_log
        else "Linear spacing shows absolute differences in recorded spend. No outliers are removed."
    )
    a, b = st.columns(2)
    with a:
        chart(
            shown,
            "recency_days",
            "monetary_gbp",
            "Recency and recorded value",
            kind="scatter",
            color="segment",
            currency=True,
            opacity=0.55,
            log_y=use_log,
            height=450,
            labels={
                "monetary_gbp": "Recorded spend (GBP)" + (" · log scale" if use_log else ""),
                "recency_days": "Days since last purchase",
            },
        )
    with b:
        chart(
            shown,
            "frequency",
            "monetary_gbp",
            "Purchase frequency and recorded value",
            kind="scatter",
            color="segment",
            currency=True,
            opacity=0.55,
            log_y=use_log,
            height=450,
            labels={
                "monetary_gbp": "Recorded spend (GBP)" + (" · log scale" if use_log else ""),
                "frequency": "Distinct eligible invoices",
            },
        )
    a, b = st.columns(2)
    with a:
        chart(shown, "rfm_score", None, "RFM score distribution", kind="histogram", nbins=30)
    with b:
        chart(
            shown,
            "monetary_gbp",
            None,
            "Customer spending distribution",
            kind="histogram",
            nbins=35,
        )
    st.caption(
        "RFM scores are relative to the selected dates and countries, not absolute risk scores."
    )
    st.subheader("Segment summary & customer detail")
    table(summary)
    table(shown.sort_values("monetary_gbp", ascending=False))
    with st.expander("How RFM works · rules, ties and scope"):
        st.markdown(
            "Recency = days since latest eligible purchase; frequency = "
            "distinct eligible invoices; monetary = gross eligible GBP, "
            "converted only for display. "
            "Lower recency scores higher. Higher frequency/value score higher."
            " Empirical 20/40/60/80 percentiles define five-point scores; "
            "ties receive the same score (equal threshold goes to lower base "
            "bin). Fewer than five distinct values use evenly spaced dense "
            "ranks; "
            "constant values receive neutral score 3. No jitter, customer-ID "
            "tie breaking or forced equal bin sizes.\n\n"
            "First matching rule wins: **Champions** R≥4 F≥4 M≥4; **At Risk** "
            "R≤2 and (F≥3 or M≥4); "
            "**Hibernating** remaining R≤2; **Loyal Customers** remaining F≥4;"
            " **New Customers** remaining R≥4 F≤2; "
            "**Potential Loyalists** everyone else. These are mutually "
            "exclusive descriptive labels, not verified churn, lifetime value "
            "or ML clustering. "
            "Anonymous IDs are excluded; cancellations are not netted. IDs are"
            " pseudonymous source identifiers, not verified identities."
        )


def predictive(settings: Settings, root) -> None:
    currency = currency_state(st.session_state)
    heading(
        "Predictive Analytics",
        "Explore a historical seven-day sales forecast and the evidence behind it.",
    )
    st.caption(
        "This page uses the fixed Phase 3 full-data target. Date, country,"
        " product and customer-segment filters do not apply."
    )
    try:
        evidence = load_evidence(root / "reports")
    except (OSError, ValueError, KeyError) as exc:
        st.warning(
            f"Saved evaluation evidence is unavailable or invalid: {exc}. "
            "Run quantiva forecast-train."
        )
        return
    result = evidence["summary"]
    st.info(
        "Historical demonstration, not a live forecast. Target: recorded gross eligible sales, "
        "including charges. No calibrated prediction intervals are available."
    )
    st.subheader("Retrospective forecast demonstration — December 2011")
    try:
        demo = forecast_saved(settings.model_dir, trusted=True)
        _, _, metadata = load_artifact(settings.model_dir, trusted=True)
        if metadata["model_name"] != result["selected_model"]:
            raise ValueError("Model name disagrees with saved evaluation")
        if sha256(settings.model_dir / "metadata.json") != result["artifact_metadata_sha256"]:
            raise ValueError("Model metadata does not match saved evaluation provenance")
        chart(
            demo,
            "date",
            "prediction_gbp",
            "Seven-day historical sales forecast",
            kind="line",
            currency=True,
            hover_data=["horizon", "model", "training_cutoff", "model_version"],
        )
        table(demo)
        st.caption(
            f"{MODEL_NAMES.get(metadata['model_name'], metadata['model_name'])} · "
            f"training cutoff {metadata['training_end']} · seven calendar days. "
            "Zero predictions do not establish zero underlying demand."
        )
        st.caption(
            "Checksums, dependency versions and metadata validated during this session. "
            "Deployment is refitted after evaluation; its cutoff differs from "
            "the pretest model. This is not a live 2026 forecast."
        )
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        st.warning(
            f"Local forecast artifacts unavailable or invalid: {exc}. "
            "Run quantiva forecast-train locally. "
            "Evaluation evidence below remains accessible; this page never "
            "downloads or retrains a model."
        )
    st.subheader("Validation vs held-out test")
    sample = st.radio(
        "Evaluation period",
        ["validation", "test"],
        format_func=lambda x: "Held-out test" if x == "test" else "Expanding validation",
        horizontal=True,
    )
    scores = evidence[f"{sample}_metrics"]
    ranked = scores.sort_values("mae_gbp").copy()
    period_best = ranked.iloc[0]["model"]
    ranked["period_result"] = ranked["model"].map(
        lambda name: "Lowest MAE" if name == period_best else ""
    )
    table(ranked.drop(columns="experiment", errors="ignore"))
    chart(
        ranked,
        "mae_gbp",
        "model",
        "Mean absolute error (MAE)",
        color="model",
        showlegend=False,
        text="period_result",
        category_orders={"model": ranked["model"].tolist()},
    )
    st.caption(
        f"Lowest {'held-out test' if sample == 'test' else 'validation'} MAE: "
        f"{MODEL_NAMES[period_best]}. "
        "This comparison does not change the validation-selected model."
    )
    best = evidence["test_metrics"].sort_values("mae_gbp").iloc[0]
    st.warning(
        f"Weekly comparison: lowest held-out MAE belongs to {MODEL_NAMES[best['model']]} "
        f"({currency.money(best['mae_gbp'])}/day in this view). "
        f"Validation selected {MODEL_NAMES[result['selected_model']]}; "
        "its selection is not changed after test. "
        "Random Forest did not demonstrate superior held-out "
        "generalization. Linear Regression has validation results only."
    )
    with st.expander("How the experiment and metrics work"):
        st.write(
            f"Modeled history: {result['series']['modeling_start']}–"
            f"{result['series']['modeling_end']}. "
            "Seven calendar days are forecast recursively. Both source boundaries are excluded. "
            "Calendar gaps represent zero observed sales, not verified zero demand."
        )
        st.write(
            f"Displayed MAE/RMSE and bias are {currency.code}/day. "
            "Authoritative evaluation and selection remain GBP; fixed positive conversion "
            "does not change model ranking. WAPE = summed absolute errors / "
            "summed actual GBP ×100, unchanged by conversion and undefined for all-zero totals. "
            "Bias is prediction minus actual. Historical manual tuning "
            "independence is not independently verified; current code "
            "selection is validation-only."
        )
    predictions = evidence[sample]
    model = st.selectbox(
        "Diagnostic model",
        predictions["model"].unique().tolist(),
        index=list(predictions["model"].unique()).index(result["selected_model"]),
        format_func=MODEL_NAMES.get,
    )
    rows = predictions.loc[predictions["model"].eq(model)].copy()
    lines = rows.melt(
        id_vars=["date"],
        value_vars=["actual_gbp", "prediction_gbp"],
        var_name="series",
        value_name="revenue_gbp",
    )
    chart(
        lines,
        "date",
        "revenue_gbp",
        "Actual observed vs predicted",
        kind="line",
        color="series",
        currency=True,
    )
    chart(
        summarize_predictions(predictions, by="horizon"),
        "horizon",
        "mae_gbp",
        "Errors by forecast horizon",
        kind="line",
        color="model",
        currency=True,
    )
    rows["residual_gbp"] = rows["prediction_gbp"] - rows["actual_gbp"]
    chart(
        rows,
        "residual_gbp",
        None,
        "Residual distribution · positive overpredicts",
        kind="histogram",
        nbins=20,
    )
    rows["absolute_error_gbp"] = rows["residual_gbp"].abs()
    st.subheader("Largest forecast misses")
    table(
        rows.nlargest(5, "absolute_error_gbp")[
            [
                "date",
                "forecast_origin",
                "horizon",
                "actual_gbp",
                "prediction_gbp",
                "absolute_error_gbp",
            ]
        ]
    )
    st.caption(
        "Eight origins per horizon; lead is confounded with weekday. Test "
        "weights are fixed; past observed context advances between "
        "completed weeks. "
        "Large spikes and rising levels can cause forest underprediction. "
        "One short period cannot establish broad reliability."
    )
    with st.expander("Controlled sensitivities · validation only"):
        table(pd.DataFrame(result["sensitivities"]))
        st.write(
            "Saturday schedule learned from initial training only; "
            "initial-training p99 describes extreme-error influence without "
            "deleting orders. "
            "Named-charge exclusion changes the target and its errors are not "
            "primary-target improvements. Null autocorrelations mean they "
            "cannot be estimated."
        )


def quality(settings: Settings, root) -> None:
    currency = currency_state(st.session_state)
    heading(
        "Data Quality",
        "Understand the source, cleaning decisions and limits of the recorded sales.",
    )
    st.caption("Full-dataset quality reports; commercial filters on other pages do not apply.")
    report = read_json(settings.processed_dir / "cleaning_report.json")
    inspection = read_json(settings.processed_dir / "initial_inspection.json")
    types = report["transaction_types"]
    counts = {
        "raw": inspection["original_records"],
        "cleaned": report["cleaned_records"],
        "eligible": types.get("completed_sale", 0),
        "duplicates": report["duplicate_records_removed"],
        "missing_ids": inspection["missing_values"]["CustomerID"],
        "missing_descriptions": inspection["missing_values"]["Description"],
        "cancellations": types.get("cancellation", 0),
        "adjustments": types.get("stock_adjustment_candidate", 0),
        "zero_value": types.get("zero_value", 0),
        "quarantined": report["quarantined_records"],
    }
    labels = {
        "raw": "Raw source lines",
        "cleaned": "Cleaned ledger lines",
        "eligible": "Eligible completed-sale lines",
        "duplicates": "Excluded exact duplicates",
        "missing_ids": "Raw missing customer IDs",
        "missing_descriptions": "Raw missing descriptions",
        "cancellations": "Cancellation lines",
        "adjustments": "Stock-adjustment candidates",
        "zero_value": "Zero-value lines",
        "quarantined": "Quarantined invalid lines",
    }
    for title, keys in [
        ("Source & eligible sales", ["raw", "cleaned", "eligible"]),
        ("Cleaning & exclusions", ["duplicates", "quarantined", "missing_descriptions"]),
        (
            "Customer coverage & transaction types",
            ["missing_ids", "cancellations", "adjustments", "zero_value"],
        ),
    ]:
        st.subheader(title)
        kpi_cards(counts, {key: (labels[key], "count") for key in keys})
    a, b = st.columns(2)
    with a:
        chart(
            pd.DataFrame(types.items(), columns=["type", "lines"]),
            "type",
            "lines",
            "Cleaned transaction classes",
        )
    with b:
        chart(
            pd.DataFrame(inspection["missing_values"].items(), columns=["field", "missing"]),
            "field",
            "missing",
            "Raw missing-value counts",
        )
    chart(
        pd.DataFrame(report["exclusion_reasons"].items(), columns=["reason", "lines"]),
        "reason",
        "lines",
        "Excluded records by reason",
    )
    st.subheader("Calendar coverage")
    try:
        series = pd.read_parquet(settings.forecast_dir / "daily_series.parquet")
        chart(series, "date", "ledger_lines", "Daily ledger observation coverage", kind="line")
        gaps = series.loc[series["record_status"].eq("no_records")].copy()
        chart(
            gaps.assign(weekday=gaps["date"].dt.day_name())
            .groupby("weekday")
            .size()
            .reset_index(name="dates"),
            "weekday",
            "dates",
            "Calendar gaps by weekday",
        )
    except OSError:
        st.info(
            "Coverage series unavailable. Run quantiva forecast-prepare after "
            "preparing the database."
        )
    st.subheader("Lineage & interpretation")
    st.write("Raw UCI workbook → Cleaning → Parquet → SQLite → Analytics → Forecasting → Dashboard")
    with st.expander("Source provenance & processing details"):
        table(
            pd.DataFrame(
                {
                    "field": [
                        "Dataset",
                        "First timestamp",
                        "Last timestamp",
                        "Raw SHA256",
                        "Policy version",
                    ],
                    "value": [
                        "UCI Online Retail · DOI 10.24432/C5BW33",
                        inspection["date_min"],
                        inspection["date_max"],
                        report["source_sha256"],
                        report["policy_version"],
                    ],
                }
            )
        )
    st.write(
        "Exact duplicate lines are ambiguous without a unique line key. "
        "Missing customer IDs limit customer coverage. "
        "Nonstandard stock codes may be charges. Cancellations are signed "
        "movements, not matched physical returns. "
        "Two negative-price records are quarantined. Gaps do not establish"
        " zero demand. The final day is partial; first-day completeness is"
        " uncertain."
    )
    try:
        sensitivity = pd.read_csv(root / "reports/duplicate_sensitivity.csv")
        revenue = sensitivity.loc[sensitivity["metric"].eq("gross_revenue_gbp")]
        if not revenue.empty:
            values = revenue.iloc[0]
            chart(
                pd.DataFrame(
                    {
                        "policy": ["Deduplicated", "Duplicates retained"],
                        "revenue_gbp": [values["deduplicated"], values["duplicates_retained"]],
                    }
                ),
                "policy",
                "revenue_gbp",
                "Gross revenue sensitivity to exact duplicates",
                currency=True,
            )
            st.caption(
                f"Retaining eligible duplicate lines adds {currency.money(values['difference'])} "
                f"({values['change_pct']:.2f}%). "
                "This is a separate sensitivity, not the primary KPI."
            )
        table(sensitivity)
    except OSError:
        st.info("Duplicate sensitivity report missing. Run quantiva analyze.")
    st.subheader("Verification evidence")
    st.caption(
        "Stored reports describe earlier runs, not the current test suite."
        " No tests execute automatically on page load."
    )
    try:
        reconciliation = pd.read_csv(root / "reports/reconciliation.csv")
        st.write(
            f"Stored SQL/pandas comparisons: {len(reconciliation):,}; "
            f"passed: {int(reconciliation['passed'].sum()):,}."
        )
        table(
            pd.DataFrame([read_json(root / "reports/forecast_verification.json")]).drop(
                columns=["checks", "artifact_inference"], errors="ignore"
            )
        )
    except (OSError, ValueError, KeyError) as exc:
        st.info(f"Stored verification unavailable: {exc}")
    if st.button("Check current forecast artifact integrity"):
        try:
            verified = verify_artifact(settings.model_dir)
            st.success(
                "Current artifact checksums and repeat inference passed. "
                "This is not a test-suite run."
            )
            table(pd.DataFrame([verified]))
        except (OSError, ValueError, RuntimeError) as exc:
            st.warning(f"Current model integrity check failed: {exc}. Run quantiva forecast-train.")

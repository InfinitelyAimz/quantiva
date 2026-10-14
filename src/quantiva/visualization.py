"""Reproducible analytical charts with explicit units and coverage."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px

NAVY = "#101b2d"
BLUE = "#59a5f5"


def create_figures(analysis: dict, folder: Path) -> None:
    """Save the eight required charts plus an interactive daily Plotly chart."""
    folder.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "figure.facecolor": NAVY,
            "axes.facecolor": NAVY,
            "text.color": "#e8edf5",
            "axes.labelcolor": "#e8edf5",
            "xtick.color": "#b9c7da",
            "ytick.color": "#b9c7da",
            "axes.edgecolor": "#62728a",
            "font.size": 10,
            "axes.titleweight": "bold",
            "savefig.facecolor": NAVY,
        }
    )

    def save(name, title, draw, xlabel, ylabel):
        fig, ax = plt.subplots(figsize=(10, 5), layout="constrained")
        draw(ax)
        ax.set(title=title, xlabel=xlabel, ylabel=ylabel)
        ax.grid(axis="y", alpha=0.12)
        fig.savefig(folder / f"{name}.png", dpi=140)
        plt.close(fig)

    daily = analysis["daily"]

    def daily_draw(ax):
        ax.plot(daily["date"], daily["revenue_gbp"], color=BLUE, linewidth=1)
        boundary = daily.loc[daily["boundary_day"]]
        ax.scatter(boundary["date"], boundary["revenue_gbp"], color="#efa65d", label="Boundary day")
        ax.legend()

    save(
        "daily_revenue",
        "Daily gross completed-sales revenue — observation boundaries marked",
        daily_draw,
        "Source calendar date",
        "Observed revenue (GBP)",
    )
    monthly = analysis["monthly"]
    save(
        "monthly_revenue",
        "Monthly gross revenue — orange indicates partial coverage",
        lambda ax: ax.bar(
            monthly["month"],
            monthly["revenue_gbp"],
            color=[BLUE if v else "#efa65d" for v in monthly["complete_month"]],
        ),
        "Calendar month",
        "Gross revenue (GBP)",
    )
    top = analysis["products"].head(10).iloc[::-1]
    save(
        "top_products",
        "Top 10 stock codes by gross completed-sales revenue",
        lambda ax: ax.barh(top["stock_code"], top["revenue_gbp"], color=BLUE),
        "Gross revenue (GBP)",
        "Stock code (names in findings)",
    )
    country = analysis["countries"].head(10).iloc[::-1]
    save(
        "country_revenue",
        "Top 10 countries by gross completed-sales revenue",
        lambda ax: ax.barh(
            country["country"].fillna("Unknown"), country["revenue_gbp"], color=BLUE
        ),
        "Gross revenue (GBP)",
        "Country",
    )
    for name, frame, column, title in [
        (
            "order_values",
            analysis["orders"],
            "revenue_gbp",
            "Invoice value distribution — all eligible orders",
        ),
        (
            "customer_spending",
            analysis["customers"],
            "spending_gbp",
            "Spending distribution — identifiable customers only",
        ),
    ]:
        save(
            name,
            title,
            lambda ax, f=frame, c=column: ax.hist(
                np.log10(1 + f[c]), bins=50, color=BLUE, edgecolor=NAVY
            ),
            "log10(1 + value in GBP)",
            "Observation count",
        )
    product = analysis["products"]
    save(
        "product_concentration",
        "Cumulative contribution across eligible selling product codes",
        lambda ax: ax.plot(
            np.arange(1, len(product) + 1) / len(product) * 100,
            product["revenue_share_pct"].cumsum(),
            color=BLUE,
        ),
        "Selling product codes ranked by revenue (%)",
        "Cumulative revenue contribution (%)",
    )
    weekdays = analysis["weekdays"]
    save(
        "weekday_revenue",
        "Mean observed revenue by weekday — interior calendar dates",
        lambda ax: ax.bar(weekdays.index, weekdays["mean_calendar_revenue_gbp"], color=BLUE),
        "Weekday (includes no-record dates)",
        "Mean observed revenue (GBP/calendar day)",
    )
    figure = px.line(
        daily,
        x="date",
        y="revenue_gbp",
        template="plotly_dark",
        title="Daily observed gross revenue — gaps are not verified zero demand",
        labels={"date": "Source calendar date", "revenue_gbp": "Gross revenue (GBP)"},
        hover_data=["has_transactions", "boundary_day"],
        color_discrete_sequence=[BLUE],
    )
    figure.update_layout(paper_bgcolor=NAVY, plot_bgcolor=NAVY)
    figure.write_html(folder / "daily_revenue.html", include_plotlyjs=True, full_html=True)

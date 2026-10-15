"""Illustrative display conversion only; analytical inputs remain authoritative GBP."""

from collections.abc import MutableMapping
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

import pandas as pd

FX_DATE = "2011-12-08"
# ECB: GBP/EUR 0.8528 and ZAR/EUR 10.8374; cross-rate rounded to six decimals.
GBP_TO_ZAR = Decimal("12.708021")
FX_SOURCE = (
    "https://data-api.ecb.europa.eu/service/data/EXR/D.GBP+ZAR.EUR.SP00.A"
    "?startPeriod=2011-12-08&endPeriod=2011-12-08&format=csvdata"
)


@dataclass(frozen=True)
class Currency:
    """A display unit, never an exchange-rate lookup or a model input."""

    code: str

    def __post_init__(self):
        if self.code not in {"GBP", "ZAR"}:
            raise ValueError("Display currency must be GBP or ZAR")

    @property
    def factor(self) -> Decimal:
        return GBP_TO_ZAR if self.code == "ZAR" else Decimal(1)

    @property
    def symbol(self) -> str:
        return "R " if self.code == "ZAR" else "£"

    def money(self, value) -> str:
        if value is None or pd.isna(value):
            return "—"
        amount = (Decimal(str(value)) * self.factor).quantize(Decimal("0.01"), ROUND_HALF_UP)
        return f"{self.symbol}{amount:,.2f}"

    def label(self, value: str) -> str:
        return value.replace("GBP", self.code).replace("Gbp", self.code)

    @property
    def notice(self) -> str:
        if self.code == "GBP":
            return (
                "Display: GBP · original dataset currency. All calculations and artifacts use GBP."
            )
        return (
            f"Display: illustrative ZAR · £1 = R {GBP_TO_ZAR} fixed at {FX_DATE} (ECB cross-rate). "
            "These are not actual historical ZAR transactions. "
            "Calculations and artifacts remain GBP."
        )


def currency_state(state: MutableMapping) -> Currency:
    """Persist the choice separately from page-widget lifecycle; default to ZAR."""
    if state.get("display_currency") not in {"GBP", "ZAR"}:
        state["display_currency"] = "ZAR"
    return Currency(state["display_currency"])


def monetary_columns(frame: pd.DataFrame) -> list[str]:
    return [c for c in frame if str(c).endswith("_gbp")]


def display_values(frame: pd.DataFrame, currency: Currency) -> pd.DataFrame:
    """Copy and scale only explicitly monetary columns or mixed sensitivity rows."""
    shown = frame.copy(deep=True)
    factor = float(currency.factor)
    for column in monetary_columns(frame):
        shown[column] = shown[column] * factor
    if "metric" in frame:
        mask = frame["metric"].astype(str).str.endswith("_gbp")
        for column in ["deduplicated", "duplicates_retained", "difference"]:
            if column in shown:
                shown[column] = shown[column].astype(float)
                shown.loc[mask, column] = shown.loc[mask, column] * factor
    return shown


def table_values(frame: pd.DataFrame, currency: Currency, *, export: bool = False) -> pd.DataFrame:
    """Label converted columns, row units and export provenance without mutating inputs."""
    shown = display_values(frame, currency)
    columns = monetary_columns(frame)
    shown = shown.rename(
        columns={c: c.removesuffix("gbp") + currency.code.lower() for c in columns}
    )
    mixed = "metric" in frame and frame["metric"].astype(str).str.endswith("_gbp").any()
    if mixed:
        mask = frame["metric"].astype(str).str.endswith("_gbp")
        shown.loc[mask, "metric"] = frame.loc[mask, "metric"].str.replace(
            "_gbp$", "_" + currency.code.lower(), regex=True
        )
        shown["unit"] = [currency.code if value else "count" for value in mask]
    if export and (columns or mixed):
        shown["source_currency"] = "GBP"
        shown["display_currency"] = currency.code
        shown["gbp_to_zar_rate"] = str(GBP_TO_ZAR)
        shown["fx_reference_date"] = FX_DATE
        shown["illustrative_conversion"] = currency.code == "ZAR"
    return shown

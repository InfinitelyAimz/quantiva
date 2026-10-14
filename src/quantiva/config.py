"""Central configuration; paths are independent of the working directory."""

import os
from dataclasses import dataclass
from pathlib import Path

DATASET_PAGE = "https://archive.ics.uci.edu/dataset/352/online+retail"
DOWNLOAD_URL = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"
COLUMNS = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
]


@dataclass(frozen=True)
class Settings:
    """Local paths; environment overrides are resolved once per invocation."""

    data_dir: Path

    @classmethod
    def from_environment(cls) -> "Settings":
        root = Path(__file__).resolve().parents[2]
        return cls(Path(os.environ.get("QUANTIVA_DATA_DIR", root / "data")).resolve())

    @property
    def raw_file(self) -> Path:
        return self.data_dir / "raw" / "Online Retail.xlsx"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def database_file(self) -> Path:
        return self.processed_dir / "quantiva.db"

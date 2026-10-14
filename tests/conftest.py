"""Shared small fixtures cover grains, missing IDs, and non-sale records."""

import pandas as pd
import pytest

from quantiva.cleaning import clean_transactions
from quantiva.config import COLUMNS
from quantiva.database import build_database


@pytest.fixture
def cleaning_result():
    rows = [
        ["1", "A", "Old name", 2, "2011-01-01 10:00", 3, 10, "UK"],
        ["1", "B", "Second item", 1, "2011-01-01 10:01", 4, 10, "UK"],
        ["2", "A", "New name", 5, "2011-01-01 11:00", 2, None, None],
        ["C3", "A", "New name", -2, "2011-01-03", 3, 20, "FR"],
        ["4", "A", "New name", 1, "2011-01-03", 1, 10, "UK"],
        ["5", "B", None, 2, "2011-03-03", 0, None, "UK"],
        ["6", "A", "damaged", -1, "2011-01-03", 0, None, "UK"],
        ["7", "A", "New name", -1, "2011-01-03", 1, 10, "UK"],
    ]
    return clean_transactions(pd.DataFrame(rows + [rows[0]], columns=COLUMNS))


@pytest.fixture
def analytical_database(tmp_path, cleaning_result):
    path = tmp_path / "quantiva.db"
    build_database(cleaning_result.ledger, path)
    return path

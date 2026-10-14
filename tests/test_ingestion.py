"""Small synthetic fixtures test engineering behavior, never business results."""

import io
import zipfile

import pandas as pd
import pytest
import requests

from quantiva.config import COLUMNS
from quantiva.ingestion import download_dataset, load_raw, sha256
from quantiva.inspection import inspect_data


def test_download_existing_file_never_requests_or_overwrites(tmp_path, monkeypatch):
    path = tmp_path / "Online Retail.xlsx"
    path.write_bytes(b"preserve original")

    def unexpected(*args, **kwargs):
        pytest.fail("An existing workbook must not trigger a request")

    monkeypatch.setattr(requests, "get", unexpected)
    before = sha256(path)
    assert download_dataset(path) == path
    assert sha256(path) == before


def test_download_failure_is_actionable_and_leaves_no_workbook(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise requests.Timeout("test timeout")

    monkeypatch.setattr(requests, "get", fail)
    path = tmp_path / "Online Retail.xlsx"
    with pytest.raises(RuntimeError, match="download and extract"):
        download_dataset(path)
    assert not path.exists()


def test_download_extracts_only_workbook_and_records_provenance(tmp_path, monkeypatch):
    workbook = io.BytesIO()
    pd.DataFrame(columns=COLUMNS).to_excel(workbook, index=False)
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("Online Retail.xlsx", workbook.getvalue())
        bundle.writestr("../unwanted.txt", "do not extract")

    class Response:
        content = archive.getvalue()

        def raise_for_status(self):
            pass

    monkeypatch.setattr(requests, "get", lambda *a, **kw: Response())
    path = tmp_path / "Online Retail.xlsx"
    download_dataset(path)
    assert load_raw(path).empty
    assert path.with_suffix(".provenance.json").exists()
    assert not (tmp_path.parent / "unwanted.txt").exists()


def test_schema_validation(tmp_path):
    path = tmp_path / "bad.xlsx"
    pd.DataFrame({"Quantity": [1]}).to_excel(path, index=False)
    with pytest.raises(ValueError, match="Required columns missing"):
        load_raw(path)


def test_inspection_distinguishes_adjustments_and_duplicates():
    rows = [
        ["1", "A", "Item", 2, "2011-01-01", 3, None, "UK"],
        ["C2", "A", "Item", -1, "2011-01-02", 3, 12, "UK"],
        ["3", "A", "damaged", -1, "2011-01-03", 0, None, "UK"],
    ]
    frame = pd.DataFrame(rows + [rows[0]], columns=COLUMNS)
    report = inspect_data(frame)
    assert report["original_records"] == 4
    assert report["duplicate_records"] == 1
    assert report["cancelled_negative_quantity_records"] == 1
    assert report["noncancelled_negative_quantity_records"] == 1
    assert report["missing_values"]["CustomerID"] == 3

"""Canary-only checks; no Quantiva model/data fixtures or output regeneration."""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

FOLDER = Path(__file__).resolve().parent
ROOT = FOLDER.parents[1]
SPEC = importlib.util.spec_from_file_location("quantiva_canary", FOLDER / "canary.py")
canary = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(canary)


def test_environment_mirrors_accepted_lock_and_linux_closure():
    lines = (FOLDER / "environment.yml").read_text(encoding="utf-8").splitlines()
    significant = [line for line in lines if line.strip() and not line.lstrip().startswith("#")]
    assert significant[:8] == [
        "name: quantiva-compatibility-canary",
        "channels:",
        "  - conda-forge",
        "  - nodefaults",
        "dependencies:",
        "  - python=3.11.9=hb806964_0_cpython",
        "  - pip=24.0",
        "  - pip:",
    ]
    assert all(line.startswith("      - ") for line in significant[8:])
    pins = [line.removeprefix("      - ") for line in significant[8:]]
    accepted = [line for line in (ROOT / "requirements-lock.txt").read_text().splitlines() if line]
    assert pins == accepted + ["pexpect==4.9.0", "ptyprocess==0.7.0"]
    assert len(pins) == len(set(pins)) == 88
    for distribution, (_, expected) in canary.EXPECTED_PACKAGES.items():
        assert f"{distribution}=={expected}" in pins


@pytest.fixture
def matching_runtime(monkeypatch):
    monkeypatch.setattr(canary.platform, "python_version", lambda: "3.11.9")
    monkeypatch.setattr(canary.platform, "python_implementation", lambda: "CPython")
    monkeypatch.setattr(canary.platform, "system", lambda: "Linux")
    monkeypatch.setattr(
        canary,
        "inspect_package",
        lambda name, module, expected: {"package": name, "passed": True},
    )
    monkeypatch.setattr(canary, "check_pip", lambda: {"passed": True})


def test_matching_observation_cannot_claim_completed_cloud_acceptance(matching_runtime):
    report = canary.collect_diagnostics()
    assert report["process_runtime_verdict"] == "PASS"
    assert report["cloud_acceptance"] == "UNVERIFIED"
    assert report["cold_restart_or_rebuild_verified"] is False
    assert report["linux_target"] == "PASS"
    assert {row["package"] for row in report["packages"]} >= {"pexpect", "ptyprocess"}


@pytest.mark.parametrize("actual", ["3.11.10", "3.12.0"])
def test_python_patch_or_minor_mismatch_fails_closed(matching_runtime, monkeypatch, actual):
    monkeypatch.setattr(canary.platform, "python_version", lambda: actual)
    report = canary.collect_diagnostics()
    assert report["process_runtime_verdict"] == report["cloud_acceptance"] == "NO-GO"


def test_non_cpython_fails_closed(matching_runtime, monkeypatch):
    monkeypatch.setattr(canary.platform, "python_implementation", lambda: "PyPy")
    assert canary.collect_diagnostics()["process_runtime_verdict"] == "NO-GO"


def test_import_failure_prevents_runtime_pass(matching_runtime, monkeypatch):
    def broken_import(name):
        raise ImportError("native extension unavailable")

    monkeypatch.setattr(canary.importlib, "import_module", broken_import)
    report = canary.collect_diagnostics()
    assert report["process_runtime_verdict"] == "NO-GO"
    assert not report["forecast_imports"][0]["passed"]


def test_failed_pip_check_prevents_runtime_pass(matching_runtime, monkeypatch):
    monkeypatch.setattr(canary, "check_pip", lambda: {"passed": False, "returncode": 1})
    assert canary.collect_diagnostics()["process_runtime_verdict"] == "NO-GO"


@pytest.mark.parametrize("installed,imported", [("2.4.5", "2.4.5"), ("2.4.6", "2.4.5")])
def test_distribution_and_imported_versions_must_both_match(monkeypatch, installed, imported):
    monkeypatch.setattr(canary, "version", lambda name: installed)
    monkeypatch.setattr(
        canary.importlib, "import_module", lambda name: SimpleNamespace(__version__=imported)
    )
    assert not canary.inspect_package("numpy", "numpy", "2.4.6")["passed"]


def test_missing_package_and_import_are_reported(monkeypatch):
    def missing_version(name):
        raise canary.PackageNotFoundError(name)

    def missing_import(name):
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(canary, "version", missing_version)
    monkeypatch.setattr(canary.importlib, "import_module", missing_import)
    row = canary.inspect_package("numpy", "numpy", "2.4.6")
    assert row["installed"] is None and not row["import_succeeded"] and not row["passed"]


def test_pip_uses_observed_interpreter_and_exit_code(monkeypatch):
    def run(command, **kwargs):
        assert command == [sys.executable, "-m", "pip", "check"]
        assert kwargs == {"capture_output": True, "text": True, "timeout": 60, "check": False}
        return SimpleNamespace(returncode=1, stdout="dependency conflict", stderr="")

    monkeypatch.setattr(canary.subprocess, "run", run)
    assert canary.check_pip()["passed"] is False


@pytest.mark.parametrize("failure", [OSError("pip unavailable"), subprocess.TimeoutExpired([], 60)])
def test_pip_execution_errors_fail_closed(monkeypatch, failure):
    def run(*args, **kwargs):
        raise failure

    monkeypatch.setattr(canary.subprocess, "run", run)
    assert canary.check_pip()["passed"] is False


def test_actual_streamlit_process_and_rerun():
    app = AppTest.from_file(str(FOLDER / "canary.py")).run(timeout=90)
    assert not app.exception
    first = json.loads(app.json[0].value)
    assert first["process_runtime_verdict"] == "PASS"
    assert first["process"]["pid"] == os.getpid()
    assert first["process"]["sys_executable"] == sys.executable
    assert first["process"]["sys_version"] == sys.version
    assert first["pip_check"]["command"] == [sys.executable, "-m", "pip", "check"]
    assert first["cloud_acceptance"] == "UNVERIFIED"
    app.button[0].click().run(timeout=90)
    assert not app.exception
    second = json.loads(app.json[0].value)
    assert first["process_instance"] == second["process_instance"]
    assert first["checked_at_utc"] != second["checked_at_utc"]
    assert second["process_runtime_verdict"] == "PASS"

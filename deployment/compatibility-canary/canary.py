"""Isolated, artifact-free probe of the actual Streamlit serving interpreter."""

import importlib
import json
import os
import platform
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version

import psutil
import streamlit as st

EXPECTED_PYTHON = "3.11.9"
EXPECTED_PACKAGES = {
    "numpy": ("numpy", "2.4.6"),
    "pandas": ("pandas", "2.3.3"),
    "scikit-learn": ("sklearn", "1.9.1"),
    "scipy": ("scipy", "1.17.1"),
    "joblib": ("joblib", "1.6.0"),
    "streamlit": ("streamlit", "1.66.0"),
    "psutil": ("psutil", "7.2.2"),
}
LINUX_PACKAGES = {"pexpect": ("pexpect", "4.9.0"), "ptyprocess": ("ptyprocess", "0.7.0")}
FORECAST_IMPORTS = {
    "sklearn.compose": ["ColumnTransformer"],
    "sklearn.ensemble": ["RandomForestRegressor"],
    "sklearn.linear_model": ["LinearRegression"],
    "sklearn.pipeline": ["Pipeline"],
    "sklearn.preprocessing": ["OneHotEncoder", "StandardScaler"],
}


def inspect_package(distribution, module_name, expected):
    """Check installed metadata and the module imported in this very process."""
    row = {"package": distribution, "expected": expected}
    try:
        row["installed"] = version(distribution)
    except PackageNotFoundError:
        row["installed"] = None
    try:
        module = importlib.import_module(module_name)
        row["imported"] = getattr(module, "__version__", None)
        row["import_succeeded"] = True
    except Exception as exc:  # Native import failures must remain visible in the canary.
        row.update(imported=None, import_succeeded=False, error=f"{type(exc).__name__}: {exc}")
    row["passed"] = (
        row["import_succeeded"] and row["installed"] == expected and row["imported"] == expected
    )
    return row


def check_pip():
    """Only pip check is a subprocess; interpreter/import evidence is collected above."""
    command = [sys.executable, "-m", "pip", "check"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=60, check=False)
        return {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "passed": result.returncode == 0,
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"command": command, "passed": False, "error": f"{type(exc).__name__}: {exc}"}


def collect_diagnostics():
    """Observe the serving process without reading Quantiva data or modifying its runtime."""
    system = platform.system()
    expected = EXPECTED_PACKAGES | (LINUX_PACKAGES if system == "Linux" else {})
    packages = [inspect_package(name, *spec) for name, spec in expected.items()]
    imports = []
    for module_name, names in FORECAST_IMPORTS.items():
        try:
            module = importlib.import_module(module_name)
            for name in names:
                getattr(module, name)
            imports.append({"module": module_name, "names": names, "passed": True})
        except Exception as exc:
            imports.append(
                {"module": module_name, "passed": False, "error": f"{type(exc).__name__}: {exc}"}
            )
    pip_check = check_pip()
    python_passed = (
        platform.python_implementation() == "CPython"
        and platform.python_version() == EXPECTED_PYTHON
    )
    passed = (
        python_passed and all(row["passed"] for row in packages + imports) and pip_check["passed"]
    )
    return {
        "schema_version": 1,
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "process": {
            "pid": os.getpid(),
            "sys_version": sys.version,
            "sys_executable": sys.executable,
            "implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "expected_python": EXPECTED_PYTHON,
            "python_passed": python_passed,
            "system": system,
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "linux_target": "PASS" if system == "Linux" else "NOT VERIFIED",
        "packages": packages,
        "forecast_imports": imports,
        "pip_check": pip_check,
        "process_runtime_verdict": "PASS" if passed else "NO-GO",
        "cloud_acceptance": "UNVERIFIED" if passed else "NO-GO",
        "cold_restart_or_rebuild_verified": False,
        "scope": "Single process observation; hosted Linux and a cold repeat require owner review.",
    }


@st.cache_resource(show_spinner=False)
def process_identity():
    """Remain stable across reruns; a newly started worker receives a new token."""
    return {
        "instance_id": str(uuid.uuid4()),
        "pid": os.getpid(),
        "started_at_utc": datetime.fromtimestamp(psutil.Process().create_time(), UTC).isoformat(),
    }


def main():
    st.set_page_config(page_title="Quantiva | Compatibility canary", layout="wide")
    st.title("Quantiva — compatibility canary")
    st.caption("Option A runtime probe. No datasets, database, model or credentials are used.")
    st.button("Refresh diagnostics")
    with st.spinner("Checking this serving interpreter, imports and pip consistency…"):
        report = collect_diagnostics()
    report["process_instance"] = process_identity()
    report["effective_streamlit_config"] = {
        "server.address": st.get_option("server.address"),
        "server.port": st.get_option("server.port"),
        "server.headless": st.get_option("server.headless"),
    }
    if report["process_runtime_verdict"] == "PASS":
        st.success("PASS — exact versions, imports and pip check in this process.")
    else:
        st.error("NO-GO — this process does not meet the accepted runtime contract.")
    st.info(
        "A local PASS is not cloud approval. Record the hosted Linux observation, then a cold "
        "restart/rebuild with a new process start time. A changed token alone is insufficient. "
        "Do not weaken version or integrity checks."
    )
    st.json(report, expanded=True)
    payload = json.dumps(report, indent=2, allow_nan=False) + "\n"
    st.download_button(
        "Download observation JSON",
        data=payload,
        file_name="quantiva-canary-observation.json",
        mime="application/json",
    )
    # A public canary never dumps environment variables, hostname, secrets or arbitrary files.
    print("QUANTIVA_CANARY_OBSERVATION " + json.dumps(report, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()

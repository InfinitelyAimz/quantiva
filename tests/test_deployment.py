"""Adversarial provisioning tests; synthetic bytes never become dashboard data."""

import copy
import hashlib
import io
import json
import runpy
import subprocess
import sys
import tarfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
import requests

from quantiva import deployment as deploy


def archive_bytes(entries):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as archive:
        for name, value, kind in entries:
            member = tarfile.TarInfo(name)
            member.type, member.size = kind, len(value) if kind == tarfile.REGTYPE else 0
            if kind in {tarfile.SYMTYPE, tarfile.LNKTYPE}:
                member.linkname = "../../outside"
            archive.addfile(member, io.BytesIO(value) if member.isfile() else None)
    return output.getvalue()


@pytest.fixture
def package(tmp_path):
    entries = [(p, p.encode(), tarfile.REGTYPE) for p in sorted(deploy.RUNTIME_PATHS)]
    body = archive_bytes(entries)
    manifest = {
        "schema_version": 1,
        "archive": {
            "url": "https://example.invalid/approved/versioned-bundle.tar.gz",
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        },
        "files": {
            p: {"bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()}
            for p, value, _ in entries
        },
        "publication_review": {"approved": True},
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    return path, manifest, body, entries


class Response:
    url = "https://example.invalid/approved/versioned-bundle.tar.gz"
    history = ()
    status_code = 200
    headers = {}

    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size):
        for n in range(0, len(self.body), chunk_size):
            yield self.body[n : n + chunk_size]


def mock_download(monkeypatch, body):
    monkeypatch.setattr(deploy.requests, "get", lambda *a, **k: Response(body))


def test_verified_install_and_reuse(package, tmp_path, monkeypatch):
    path, manifest, body, _ = package
    mock_download(monkeypatch, body)
    cache = tmp_path / "cache"
    installed = deploy.provision(path, cache)
    deploy.verify_installed(installed.parent, manifest)
    monkeypatch.setattr(deploy.requests, "get", lambda *a, **k: pytest.fail("Unexpected download"))
    assert deploy.provision(path, cache) == installed
    (installed / "models/context.csv").write_bytes(b"corrupted")
    with pytest.raises(deploy.ProvisioningError, match="integrity"):
        deploy.provision(path, cache)


@pytest.mark.parametrize("damage", ["corrupt", "truncated", "oversize"])
def test_bad_download_never_installed(package, tmp_path, monkeypatch, damage):
    path, _, body, _ = package
    damaged = {"corrupt": b"X" + body[1:], "truncated": body[:-15], "oversize": body + b"X"}
    mock_download(monkeypatch, damaged[damage])
    cache = tmp_path / "cache"
    with pytest.raises(deploy.ProvisioningError):
        deploy.provision(path, cache)
    assert list(cache.iterdir()) == [cache / "initialization.lock"]


@pytest.mark.parametrize(
    ("name", "kind"),
    [
        ("../escape", tarfile.REGTYPE),
        ("/absolute", tarfile.REGTYPE),
        ("data\\models\\escape", tarfile.REGTYPE),
        ("C:/escape", tarfile.REGTYPE),
        ("data/models/context.csv", tarfile.SYMTYPE),
        ("data/models/context.csv", tarfile.LNKTYPE),
        ("data/models/context.csv", tarfile.FIFOTYPE),
        ("private.txt", tarfile.REGTYPE),
    ],
)
def test_malicious_archive(package, tmp_path, name, kind):
    _, manifest, _, _ = package
    archive = tmp_path / "malicious.tar.gz"
    archive.write_bytes(archive_bytes([(name, b"evil", kind)]))
    destination = tmp_path / "extracted"
    destination.mkdir()
    with pytest.raises(deploy.ProvisioningError):
        deploy.extract_archive(archive, destination, manifest)
    assert not (tmp_path / "escape").exists()


@pytest.mark.parametrize("damage", ["missing", "duplicate", "wrong_size", "wrong_hash"])
def test_member_integrity(package, tmp_path, damage):
    _, manifest, _, entries = package
    rows = list(entries)
    if damage == "missing":
        rows.pop()
    elif damage == "duplicate":
        rows.append(rows[0])
    else:
        name, data, kind = rows[0]
        rows[0] = (name, b"X" * (len(data) + (damage == "wrong_size")), kind)
    archive = tmp_path / "invalid.tar.gz"
    archive.write_bytes(archive_bytes(rows))
    with pytest.raises(deploy.ProvisioningError):
        deploy.extract_archive(archive, tmp_path / "extract", manifest)


def test_interrupted_download_recovers(package, tmp_path, monkeypatch):
    path, _, body, _ = package

    class Broken(Response):
        def iter_content(self, chunk_size):
            yield self.body[:10]
            raise requests.ConnectionError("interrupted")

    monkeypatch.setattr(deploy.requests, "get", lambda *a, **k: Broken(body))
    cache = tmp_path / "cache"
    with pytest.raises(deploy.ProvisioningError, match="download failed"):
        deploy.provision(path, cache)
    assert not list(cache.glob("staging-*"))
    mock_download(monkeypatch, body)
    assert deploy.provision(path, cache).is_dir()


def test_redirects_are_checked_before_following(package, tmp_path, monkeypatch):
    path, _, body, _ = package
    redirect = Response(b"")
    redirect.status_code = 302
    redirect.headers = {"Location": "http://example.invalid/insecure"}
    calls = []

    def get(*args, **kwargs):
        assert kwargs["allow_redirects"] is False
        calls.append(args[0])
        return redirect

    monkeypatch.setattr(deploy.requests, "get", get)
    with pytest.raises(deploy.ProvisioningError, match="HTTPS"):
        deploy.provision(path, tmp_path / "cache")
    assert len(calls) == 1
    redirect.headers = {"Location": "https://example.invalid/signed?temporary=1"}
    responses = iter([redirect, Response(body)])
    monkeypatch.setattr(deploy.requests, "get", lambda *a, **k: next(responses))
    assert deploy.provision(path, tmp_path / "cache").is_dir()


def test_unavailable_download(package, tmp_path, monkeypatch):
    path, _, _, _ = package

    def unavailable(*args, **kwargs):
        raise requests.HTTPError("unavailable")

    monkeypatch.setattr(deploy.requests, "get", unavailable)
    with pytest.raises(deploy.ProvisioningError, match="download failed"):
        deploy.provision(path, tmp_path / "cache")


def test_interrupted_extraction_recovers(package, tmp_path, monkeypatch):
    path, _, body, _ = package
    mock_download(monkeypatch, body)
    real_extract = deploy.extract_archive

    def interrupted(archive, destination, manifest):
        (destination / "partial").write_bytes(b"partial")
        raise OSError("disk write interrupted")

    monkeypatch.setattr(deploy, "extract_archive", interrupted)
    cache = tmp_path / "cache"
    with pytest.raises(deploy.ProvisioningError, match="provisioning failed"):
        deploy.provision(path, cache)
    assert not list(cache.glob("staging-*"))
    monkeypatch.setattr(deploy, "extract_archive", real_extract)
    assert deploy.provision(path, cache).is_dir()


def test_concurrent_initialization(package, tmp_path, monkeypatch):
    path, manifest, body, _ = package
    calls = []

    def slow_get(*args, **kwargs):
        calls.append(1)
        time.sleep(0.15)
        return Response(body)

    monkeypatch.setattr(deploy.requests, "get", slow_get)
    barrier = threading.Barrier(4)

    def initialize(_):
        barrier.wait()
        result = deploy.provision(path, tmp_path / "cache")
        deploy.verify_installed(result.parent, manifest)
        return result

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(initialize, range(4)))
    assert len(set(results)) == 1
    assert len(calls) == 1


def test_lock_timeout(tmp_path):
    lock = tmp_path / "lock"
    with deploy.initialization_lock(lock):
        with pytest.raises(deploy.ProvisioningError, match="Timed out"):
            with deploy.initialization_lock(lock, timeout=0):
                pytest.fail("Acquired another owner's lock")


def test_manifest_and_configuration_fail_closed(package, tmp_path, monkeypatch):
    path, manifest, _, _ = package
    cases = []
    for url in [None, "http://example.invalid/data", "https://u:p@example.invalid/data"]:
        value = copy.deepcopy(manifest)
        value["archive"]["url"] = url
        cases.append(value)
    for field, value in [("bytes", deploy.MAX_ARCHIVE_BYTES + 1), ("sha256", "invalid")]:
        changed = copy.deepcopy(manifest)
        changed["archive"][field] = value
        cases.append(changed)
    changed = copy.deepcopy(manifest)
    changed["files"]["private.txt"] = changed["files"][next(iter(deploy.RUNTIME_PATHS))]
    cases.append(changed)
    changed = copy.deepcopy(manifest)
    changed["publication_review"]["approved"] = False
    cases.append(changed)
    monkeypatch.setattr(deploy.requests, "get", lambda *a, **k: pytest.fail("Unexpected network"))
    for value in cases:
        path.write_text(json.dumps(value))
        with pytest.raises(deploy.ProvisioningError):
            deploy.provision(path, tmp_path / "never-created")
    assert not (tmp_path / "never-created").exists()
    monkeypatch.delenv("QUANTIVA_DEPLOYMENT", raising=False)
    assert deploy.deployment_data(tmp_path) is None
    monkeypatch.setenv("QUANTIVA_DEPLOYMENT", "wrong")
    with pytest.raises(deploy.ProvisioningError):
        deploy.deployment_data(tmp_path)


def test_environment_and_trusted_public_manifest():
    root = Path(__file__).resolve().parents[1]
    content = (root / "environment.yml").read_text()
    assert "python=3.11.9=hb806964_0_cpython" in content
    assert "  - pip=26.2.2\n" in content
    assert "pip==" not in content
    lines = {line.strip().removeprefix("- ") for line in content.splitlines()}
    pins = set((root / "requirements-lock.txt").read_text().splitlines())
    pins = {line for line in pins if line and not line.startswith("#")}
    pins.remove("pip==24.0")
    inline = {line for line in lines if "==" in line}
    assert inline == pins | {"pexpect==4.9.0", "ptyprocess==0.7.0"}
    assert "-e ." in lines
    manifest = json.loads((root / "deployment/community-cloud/artifacts.json").read_text())
    deploy.validate_manifest(manifest)
    assert manifest["archive"]["url"] == (
        "https://github.com/InfinitelyAimz/quantiva/releases/download/"
        "deployment-runtime-v1/quantiva-runtime.tar.gz"
    )
    assert manifest["archive"]["sha256"] == (
        "bc2adbd925f3a59c0b424a5ee2284951701db7f615958d0c3f1acd8667ee7f9d"
    )
    assert manifest["archive"]["bytes"] == 32788556
    assert manifest["publication_review"]["approved"] is True


def test_builder_is_deterministic_and_never_overwrites(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[1]
    builder = runpy.run_path(str(root / "scripts/build_deployment_bundle.py"))["build_bundle"]
    source = tmp_path / "source"
    for name in deploy.RUNTIME_PATHS:
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
    (source / "data/processed/cleaning_report.json").write_text(
        json.dumps({"source_sha256": "a" * 64})
    )
    (source / "reports").mkdir()
    (source / "reports/forecast_results.json").write_text("{}")
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **k: "b" * 40)
    first = builder(source, tmp_path / "first")
    second = builder(source, tmp_path / "second")
    assert first == second
    approved = json.loads((root / "deployment/community-cloud/artifacts.json").read_text())
    attribution = {
        "dataset": "Online Retail",
        "creator": "Daqing Chen",
        "repository": "UCI Machine Learning Repository",
        "doi": "10.24432/C5BW33",
        "original_dataset_url": "https://archive.ics.uci.edu/dataset/352/online+retail",
        "license": "CC BY 4.0",
        "license_name": "Creative Commons Attribution 4.0 International",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "non_endorsement": (
            "Quantiva is an independent project. No endorsement by UCI or the original "
            "dataset creator is claimed or implied."
        ),
    }
    for key, value in attribution.items():
        assert first["provenance"][key] == approved["provenance"][key] == value
    for key in ["citation", "changes", "software_licensing", "model_source"]:
        assert first["provenance"][key] == approved["provenance"][key]
    document = (root / "deployment/community-cloud/README.md").read_text(encoding="utf-8")
    assert attribution["non_endorsement"] in document
    assert attribution["original_dataset_url"] in document
    assert "Future release attribution notice" in document
    assert first["archive"]["url"] is None
    assert first["publication_review"]["approved"] is False
    with pytest.raises(FileExistsError):
        builder(source, tmp_path / "first")
    with pytest.raises(ValueError, match="outside"):
        builder(source, source / "inside")


def test_initialization_across_processes(package, tmp_path):
    path, manifest, body, _ = package
    archive = tmp_path / "fixture.tar.gz"
    archive.write_bytes(body)
    script = """
import sys,time
from pathlib import Path
from quantiva import deployment as d
manifest,archive,cache,downloads=map(Path,sys.argv[1:])
def local_download(config,destination):
    with downloads.open('a') as log: log.write('download\\n')
    time.sleep(.15)
    destination.write_bytes(archive.read_bytes())
d.download_archive=local_download
d.provision(manifest,cache)
"""
    calls = tmp_path / "downloads.txt"
    processes = [
        subprocess.Popen(
            [
                sys.executable,
                "-B",
                "-c",
                script,
                str(path),
                str(archive),
                str(tmp_path / "cache"),
                str(calls),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(3)
    ]
    for process in processes:
        stdout, stderr = process.communicate(timeout=30)
        assert process.returncode == 0, (stdout, stderr)
    assert calls.read_text().splitlines() == ["download"]
    deploy.verify_installed(tmp_path / "cache" / manifest["archive"]["sha256"], manifest)

"""Opt-in, first-party deployment artifacts; never train or relax model checks."""

import hashlib
import json
import os
import re
import shutil
import tarfile
import tempfile
import time
from contextlib import ExitStack, contextmanager
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests

RUNTIME_PATHS = frozenset(
    {
        "data/processed/quantiva.db",
        "data/processed/cleaning_report.json",
        "data/processed/initial_inspection.json",
        "data/processed/forecasting/daily_series.parquet",
        "data/models/selected.joblib",
        "data/models/context.csv",
        "data/models/metadata.json",
        "data/models/manifest.json",
    }
)
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_EXPANDED_BYTES = 200 * 1024 * 1024
CHUNK_BYTES = 1024 * 1024


class ProvisioningError(ValueError):
    """An unavailable or untrusted deployment must fail closed."""


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_BYTES), b""):
            result.update(chunk)
    return result.hexdigest()


def validate_manifest(manifest: dict, *, require_url: bool = True) -> None:
    """Trust comes from reviewed repository configuration, not from the download."""
    try:
        if manifest["schema_version"] != 1 or set(manifest["files"]) != RUNTIME_PATHS:
            raise ProvisioningError("Deployment manifest has an unexpected schema or allowlist")
        rows = [manifest["archive"], *manifest["files"].values()]
        for row in rows:
            if not re.fullmatch(r"[0-9a-f]{64}", row["sha256"]):
                raise ProvisioningError("Deployment manifest has an invalid SHA256")
            if type(row["bytes"]) is not int or row["bytes"] <= 0:
                raise ProvisioningError("Deployment manifest has an invalid file size")
        if manifest["archive"]["bytes"] > MAX_ARCHIVE_BYTES:
            raise ProvisioningError("Deployment archive exceeds the size limit")
        if sum(row["bytes"] for row in manifest["files"].values()) > MAX_EXPANDED_BYTES:
            raise ProvisioningError("Deployment files exceed the expanded size limit")
        url = manifest["archive"]["url"]
        if url is None and not require_url:
            return
        if require_url and manifest.get("publication_review", {}).get("approved") is not True:
            raise ProvisioningError("Artifact publication has not been approved")
        parsed = urlsplit(url) if isinstance(url, str) else None
        if (
            parsed is None
            or parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path in {"", "/"}
        ):
            raise ProvisioningError("Configure an approved immutable HTTPS artifact URL first")
    except (KeyError, TypeError, AttributeError) as exc:
        raise ProvisioningError("Malformed deployment manifest") from exc


@contextmanager
def initialization_lock(path: Path, timeout: float = 180):
    """An OS-released lock survives crashes without stale ownership markers."""
    with path.open("a+b") as handle:
        if path.stat().st_size == 0:
            handle.write(b"0")
            handle.flush()
        deadline = time.monotonic() + timeout
        while True:
            try:
                if os.name == "nt":
                    import msvcrt

                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as exc:
                if time.monotonic() >= deadline:
                    raise ProvisioningError(
                        "Timed out waiting for artifact initialization"
                    ) from exc
                time.sleep(0.1)
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def verify_installed(folder: Path, manifest: dict) -> None:
    """Rehash every file; never trust only a completion marker or cached PASS."""
    if folder.is_symlink():
        raise ProvisioningError("Deployment directory cannot be a symlink")
    actual = set()
    for path in folder.rglob("*"):
        if path.is_symlink() or not (path.is_dir() or path.is_file()):
            raise ProvisioningError("Deployment contains a link or special file")
        if path.is_file():
            actual.add(path.relative_to(folder).as_posix())
    if actual != RUNTIME_PATHS:
        raise ProvisioningError("Installed deployment does not match the artifact allowlist")
    for name, row in manifest["files"].items():
        path = folder / name
        if path.stat().st_size != row["bytes"] or digest(path) != row["sha256"]:
            raise ProvisioningError(f"Deployment artifact integrity failure: {name}")


def download_archive(manifest: dict, destination: Path) -> None:
    """Bound memory/disk and connection/read/overall time; no automatic retries."""
    archive = manifest["archive"]
    started = time.monotonic()
    try:
        with ExitStack() as stack:
            url = archive["url"]
            for _ in range(6):
                response = stack.enter_context(
                    requests.get(url, stream=True, timeout=(10, 30), allow_redirects=False)
                )
                response.raise_for_status()
                if response.status_code not in {301, 302, 303, 307, 308}:
                    break
                url = urljoin(url, response.headers.get("Location", ""))
                parsed = urlsplit(url)
                if parsed.scheme != "https" or not parsed.hostname or parsed.username:
                    raise ProvisioningError("Artifact redirect is not an approved HTTPS transport")
                if time.monotonic() - started > 180:
                    raise ProvisioningError("Artifact redirects exceeded the time limit")
            else:
                raise ProvisioningError("Artifact download exceeded the redirect limit")
            received = 0
            with destination.open("xb") as stream:
                for chunk in response.iter_content(CHUNK_BYTES):
                    received += len(chunk)
                    if received > archive["bytes"] or time.monotonic() - started > 180:
                        raise ProvisioningError("Artifact download exceeded its size or time limit")
                    stream.write(chunk)
        if received != archive["bytes"] or digest(destination) != archive["sha256"]:
            raise ProvisioningError("Artifact archive size or SHA256 mismatch")
    except requests.RequestException as exc:
        raise ProvisioningError(
            "Approved artifact download failed; no fallback was attempted"
        ) from exc


def extract_archive(archive: Path, destination: Path, manifest: dict) -> None:
    """Manually copy exact regular members, never tar.extract or extractall."""
    seen = set()
    try:
        with tarfile.open(archive, "r:gz") as bundle:
            for member in bundle:
                if member.name not in RUNTIME_PATHS or member.name in seen or not member.isfile():
                    raise ProvisioningError("Archive has an unexpected, duplicate or linked member")
                row = manifest["files"][member.name]
                if member.size != row["bytes"] or member.sparse is not None or member.pax_headers:
                    raise ProvisioningError(
                        "Archive member has an invalid size or extended metadata"
                    )
                seen.add(member.name)
                path = destination / member.name
                path.parent.mkdir(parents=True, exist_ok=True)
                source = bundle.extractfile(member)
                if source is None:
                    raise ProvisioningError("Archive member cannot be read")
                with source, path.open("xb") as output:
                    shutil.copyfileobj(source, output, CHUNK_BYTES)
            if seen != RUNTIME_PATHS:
                raise ProvisioningError("Archive is missing required artifacts")
        verify_installed(destination, manifest)
    except (tarfile.TarError, EOFError) as exc:
        raise ProvisioningError("Invalid or truncated deployment archive") from exc


def provision(manifest_path: Path, cache: Path) -> Path:
    """Install one complete immutable generation, with atomic visibility to readers."""
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        validate_manifest(manifest)
        cache.mkdir(parents=True, exist_ok=True)
        target = cache / manifest["archive"]["sha256"]
        with initialization_lock(cache / "initialization.lock"):
            if target.exists() or target.is_symlink():
                verify_installed(target, manifest)
                return target / "data"
            # Interrupted work is never reused. Unique staging stays on the same filesystem.
            with tempfile.TemporaryDirectory(prefix="staging-", dir=cache) as temporary:
                staging = Path(temporary)
                download_archive(manifest, staging / "bundle.tar.gz")
                extracted = staging / "verified"
                extracted.mkdir()
                extract_archive(staging / "bundle.tar.gz", extracted, manifest)
                os.replace(extracted, target)
            return target / "data"
    except ProvisioningError:
        raise
    except (OSError, ValueError) as exc:
        raise ProvisioningError(
            "Artifact provisioning failed; existing project data was not used"
        ) from exc


def deployment_data(root: Path) -> Path | None:
    """No activation means no network, cache writes, or changes to normal local startup."""
    enabled = os.environ.get("QUANTIVA_DEPLOYMENT", "0")
    if enabled == "0":
        return None
    if enabled != "1":
        raise ProvisioningError("QUANTIVA_DEPLOYMENT must be 0 or 1")
    cache = Path(
        os.environ.get(
            "QUANTIVA_DEPLOYMENT_CACHE", Path(tempfile.gettempdir()) / "quantiva-deployment"
        )
    )
    return provision(root / "deployment/community-cloud/artifacts.json", cache)

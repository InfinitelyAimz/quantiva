"""Build a private deterministic eight-file archive; never publish or overwrite."""

import argparse
import gzip
import hashlib
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path

from quantiva.deployment import RUNTIME_PATHS, digest, extract_archive, validate_manifest


def build_bundle(root: Path, output: Path) -> dict:
    root, output = root.resolve(), output.resolve()
    if output.is_relative_to(root):
        raise ValueError("The deployment archive must stay outside the Git worktree")
    # Never overwrite an existing private candidate or backup directory.
    output.mkdir(parents=True, exist_ok=False)
    files = {}
    for name in sorted(RUNTIME_PATHS):
        path = root / name
        if not path.is_file() or any(p.is_symlink() for p in [path, *path.parents]):
            raise ValueError(f"Expected a regular first-party artifact: {name}")
        files[name] = {"bytes": path.stat().st_size, "sha256": digest(path)}
    archive = output / "quantiva-runtime.tar.gz"
    with archive.open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.USTAR_FORMAT) as bundle:
                for name in sorted(files):
                    info = tarfile.TarInfo(name)
                    info.size, info.mode, info.mtime = files[name]["bytes"], 0o644, 0
                    with (root / name).open("rb") as source:
                        bundle.addfile(info, source)
    manifest = {
        "schema_version": 1,
        "archive": {"url": None, "bytes": archive.stat().st_size, "sha256": digest(archive)},
        "files": files,
        "provenance": {
            "accepted_project_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip(),
            "dataset": "Online Retail",
            "creator": "Daqing Chen",
            "repository": "UCI Machine Learning Repository",
            "citation": "Chen, D. (2015). Online Retail. UCI Machine Learning Repository.",
            "doi": "10.24432/C5BW33",
            "original_dataset_url": "https://archive.ics.uci.edu/dataset/352/online+retail",
            "source_workbook_sha256": json.loads(
                (root / "data/processed/cleaning_report.json").read_text(encoding="utf-8")
            )["source_sha256"],
            "forecast_report_lf_sha256": hashlib.sha256(
                (root / "reports/forecast_results.json").read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest(),
            "license": "CC BY 4.0",
            "license_name": "Creative Commons Attribution 4.0 International",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "changes": (
                "Quantiva's SQLite database, analytical outputs and forecasting artifacts are "
                "derived from the original UCI dataset through documented cleaning, normalization, "
                "relational modeling, feature engineering and model fitting."
            ),
            "non_endorsement": (
                "Quantiva is an independent project. No endorsement by UCI or the original "
                "dataset creator is claimed or implied."
            ),
            "software_licensing": (
                "The dataset's CC BY 4.0 license does not license Quantiva's own software. "
                "No explicit Quantiva software license is currently provided; no new software "
                "license is introduced by this attribution."
            ),
            "model_source": "Owner-built accepted Quantiva model; never a third-party pickle.",
        },
        "publication_review": {
            "approved": False,
            "exposure": "Transaction-level UCI records and pseudonymous customer identifiers.",
            "excluded": "Raw workbook, environments, credentials, private files, pipeline extras.",
        },
    }
    validate_manifest(manifest, require_url=False)
    # Verify the bytes actually archived, including detecting source changes during packaging.
    with tempfile.TemporaryDirectory(dir=output) as temporary:
        extract_archive(archive, Path(temporary), manifest)
    (output / "publication-review.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    archive.chmod(0o444)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    result = build_bundle(Path(__file__).resolve().parents[1], args.output_directory)
    print(json.dumps(result, indent=2))

"""Check portfolio references and headline facts without rewriting analytical evidence."""

import ast
import csv
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

from PIL import Image


def markdown_rows(text: str) -> dict[str, list[str]]:
    """Extract the simple keyed Markdown tables used by the portfolio documents."""
    return {
        cells[0]: cells[1:]
        for line in text.splitlines()
        if line.startswith("|") and (cells := [c.strip() for c in line.strip("|").split("|")])
    }


def anchors(text: str) -> set[str]:
    """Resolve ordinary GitHub heading fragments, including duplicate suffixes."""
    counts: dict[str, int] = {}
    result = set()
    for title in re.findall(r"^#{1,6} (.+)$", text, re.M):
        slug = re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")
        number = counts.get(slug, 0)
        counts[slug] = number + 1
        result.add(f"{slug}-{number}" if number else slug)
    return result


def verify_portfolio(root: Path | None = None) -> dict:
    """Fail on broken local references, stale headline tables or invented CLI commands."""
    root = (root or Path(__file__).resolve().parents[1]).resolve()
    required_paths = [
        root / "README.md",
        root / "docs/technical_scope.md",
        root / "reports/portfolio_case_study.md",
        root / "reports/phase_1_progress.md",
        root / "reports/phase_2_progress.md",
        root / "reports/phase_3_progress.md",
        root / "reports/phase_4_progress.md",
        root / "reports/phase_5_progress.md",
        root / "docs/architecture.md",
        root / "docs/reproducibility.md",
        root / "docs/methodology.md",
        root / "docs/dashboard_gallery.md",
    ]
    paths = sorted(set(required_paths) | set((root / "docs").glob("*.md")))
    errors = []
    for name in ["cv_project_bullets.md", "interview_talking_points.md", "portfolio_summary.md"]:
        if (root / "docs" / name).exists():
            errors.append(f"Personal preparation document in public tree: docs/{name}")
    internal_paths = (
        "AGENTS.md",
        "PROJECT_SPECIFICATION.md",
        "PHASE_2_SPECIFICATION.md",
        "PHASE_3_SPECIFICATION.md",
        "PHASE_4_SPECIFICATION.md",
        "PHASE_4_UI_REFINEMENT_SPECIFICATION.md",
        "PHASE_5_SPECIFICATION.md",
        "reports/public_repository_audit.md",
        "reports/public_repository_inventory.csv",
    )
    for name in internal_paths:
        if (root / name).exists():
            errors.append(f"Internal instruction document in public tree: {name}")
    local_links = 0
    images = set()
    documents = {}
    for path in paths:
        if not path.is_file():
            errors.append(f"Missing deliverable: {path.relative_to(root)}")
            continue
        text = path.read_text(encoding="utf-8")
        documents[path.relative_to(root).as_posix()] = text
        if re.search(r"\b[A-Za-z]:[\\/]|/(?:Users|home)/", text):
            errors.append(f"Machine-specific path: {path.relative_to(root)}")
        prose = re.sub(r"```.*?```", "", text, flags=re.S)
        for target in re.findall(r"!?\[[^\]]*\]\(([^\s)]+)\)", prose):
            parsed = urlsplit(target)
            if path.name == "README.md" and Path(unquote(parsed.path)).name in (
                *internal_paths,
                "PHASE_5_SPECIFICATION.md",
            ):
                errors.append(f"README links to internal instructions: {target}")
            if parsed.scheme:
                continue  # Network links are reviewed separately; no flaky online test.
            local_links += 1
            destination = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            if not destination.is_relative_to(root) or not destination.exists():
                errors.append(f"Broken/local-escape reference in {path.name}: {target}")
                continue
            if parsed.fragment and destination.suffix == ".md":
                if unquote(parsed.fragment) not in anchors(destination.read_text(encoding="utf-8")):
                    errors.append(f"Missing heading in {path.name}: {target}")
            if destination.suffix == ".png":
                try:
                    with Image.open(destination) as capture:
                        size = capture.size
                        capture.verify()
                    images.add((destination.relative_to(root).as_posix(), *size))
                except OSError:
                    errors.append(f"Unreadable screenshot: {destination.name}")

    metrics = json.loads((root / "reports/phase_2_metrics.json").read_text())
    quality = json.loads((root / "reports/phase_1_quality.json").read_text())["cleaning"]
    k = metrics["kpis"]
    expected = {
        "Gross eligible completed-sales revenue": f"£{k['gross_revenue_gbp']:,.2f}",
        "Completed orders": f"{k['completed_orders']:,}",
        "Average order value": f"£{k['aov_gbp']:,.2f}",
        "Units sold": f"{k['units_sold']:,}",
        "Identifiable purchasers": f"{k['identifiable_customers']:,}",
        "Within-period repeat purchasers": f"{k['repeat_customers']:,}",
        "Within-period repeat rate": f"{k['repeat_purchase_rate'] * 100:.2f}%",
    }
    checks = 0
    for name in ["README.md", "reports/portfolio_case_study.md", "docs/technical_scope.md"]:
        rows = markdown_rows(documents.get(name, ""))
        wanted = dict(expected)
        if name.startswith("reports/"):
            wanted.update(
                {
                    "Original source records": f"{quality['original_records']:,}",
                    "Cleaned ledger records": f"{quality['cleaned_records']:,}",
                    "Eligible completed-sales lines": (
                        f"{quality['transaction_types']['completed_sale']:,}"
                    ),
                }
            )
        for label, value in wanted.items():
            checks += 1
            if rows.get(label) != [value]:
                errors.append(f"Stale/missing fact in {name}: {label} = {value}")
        names = {
            "naive": "Naive",
            "seasonal_naive": "Weekly Seasonal Naive",
            "linear_regression": "Linear Regression",
            "random_forest": "Random Forest",
        }
        comparisons = {}
        for period in ["validation", "test"]:
            with (root / f"reports/forecast_{period}_comparison.csv").open(newline="") as handle:
                comparisons[period] = {
                    r["model"]: f"{float(r['mae_gbp']):,.2f}" for r in csv.DictReader(handle)
                }
        for model, label in names.items():
            checks += 1
            values = [
                comparisons["validation"][model],
                comparisons["test"].get(model, "Not evaluated"),
            ]
            if rows.get(label) != values:
                errors.append(f"Stale/missing forecast comparison in {name}: {label}")

    segments = json.loads((root / "reports/phase_4_verification.json").read_text())[
        "rfm_segment_counts"
    ]
    case_rows = markdown_rows(documents.get("reports/portfolio_case_study.md", ""))
    for segment, count in segments.items():
        checks += 1
        if case_rows.get(segment) != [f"{count:,}"]:
            errors.append(f"Stale/missing RFM count: {segment}")

    cli = ast.parse((root / "src/quantiva/cli.py").read_text())
    allowed = set()
    for node in ast.walk(cli):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (
                node.func.attr == "add_argument"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and node.args[0].value == "command"
            ):
                allowed = set(
                    ast.literal_eval(next(k.value for k in node.keywords if k.arg == "choices"))
                )
    commands = set()
    for name, text in documents.items():
        commands.update(re.findall(r"(?:quantiva\.exe|\.venv/bin/quantiva)\s+([a-z][a-z-]*)", text))
        for script in re.findall(r"python\.exe (scripts/[\w]+\.py)", text):
            if not (root / script).is_file():
                errors.append(f"Missing script in {name}: {script}")
    if not allowed or commands != allowed:
        errors.append(
            f"Documented CLI mismatch: unknown={sorted(commands - allowed)}, "
            f"missing={sorted(allowed - commands)}"
        )
    if len(images) != 6 or any((w, h) != (1440, 1000) for _, w, h in images):
        errors.append("Expected six reused 1440x1000 portfolio screenshots")
    if errors:
        raise ValueError("Portfolio verification failed:\n" + "\n".join(errors))
    return {
        "documents": len(documents),
        "local_references": local_links,
        "headline_fact_checks": checks,
        "cli_commands": sorted(commands),
        "required_technical_documents": len(required_paths),
        "personal_preparation_absent": True,
        "screenshots": [name for name, _, _ in sorted(images)],
        "result": "passed",
    }


if __name__ == "__main__":
    print(json.dumps(verify_portfolio(), indent=2))

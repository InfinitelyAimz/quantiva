# Phase 5 — portfolio documentation and reproducibility verification

> Historical technical evidence: measurements, test counts and verification scope
> describe the implementation milestone recorded here, not a new execution.
> Later technical corrections are identified in the follow-up evidence.

Recorded milestone date: **15 October 2026**.

## Technical baseline verification

The Phase 4 implementation baseline passed 105 tests with warnings treated as
errors in 20.35s; Ruff lint/format and dependency consistency checks passed.
The documentation work builds on the same accepted application tree.

## Repository review and implementation

Reviewed methodology, quality and evaluation reports, all three notebooks, the
dependency lock, CLI, verification scripts and existing screenshot evidence.

Detailed analytical reports already existed. Gaps were a current landing page,
cross-phase architecture/reproduction navigation, a cohesive business case study
and accurate professional descriptions. The old README still said Phase 4 was
proposed and Phase 5 had not begun. Public milestone reports preserve historical
measurements, implementation decisions, reproduction evidence and limitations.

| Deliverable | Change |
| --- | --- |
| [README](../README.md) | Business questions, preview, capabilities, measured findings, architecture, setup, checks, attribution and current status |
| [Case study](portfolio_case_study.md) | Verified project narrative, decisions, RFM, baseline comparison and limits |
| [Architecture](../docs/architecture.md) | Real modules, data flow, stored/generated/application boundaries |
| [Reproducibility](../docs/reproducibility.md) | Exact commands, checksum, stage dependencies, writes, cross-platform guidance and troubleshooting |
| [Methodology index](../docs/methodology.md) | Central route to preserved Phase 1–4 reports and caveats |
| [Gallery](../docs/dashboard_gallery.md) | Six existing verified screenshots; no added image copies |
| [Documentation verifier](../scripts/verify_portfolio.py) | Required technical documents, local references/anchors, image decoding/dimensions, headline tables and CLI choices; also runs in CI |

No application, dataset, SQL, cleaning, model, feature, dependency or evaluation
change is included. Source currency remains GBP; ZAR remains illustrative.

## Fresh-checkout reproduction

Used a separate fresh checkout of the Phase 4 baseline. Created a
fresh Python 3.11 environment, installed `requirements-lock.txt`, then installed
the package editable with `--no-deps --no-build-isolation`. No environment packages,
prepared data or saved models were copied from the primary workspace.

The official download reproduced source SHA-256
`43465a06f2ccf7c8b5bd2892bc7defb52f97487934fe93b16ae4c3936424676d`.
All following stages completed with exit code zero:

| Commands, after environment installation | Result |
| --- | --- |
| `quantiva download`, `inspect`, `prepare`, `database` | Source, ledger/audit/manifest and SQLite regenerated |
| `quantiva analyze` | Metrics, findings, CSV evidence and figures regenerated |
| `quantiva forecast-prepare`, `forecast-train`, `forecast-compare` | Frozen training/evaluation experiment and saved models regenerated |
| `quantiva forecast`, `forecast-verify` | Saved-model loading, seven-date inference and repeatability passed |
| `python scripts/verify_data.py` | Seven integrity checks passed |
| `python scripts/verify_analytics.py` | Five conditions, 14 queries and 3,982 comparisons passed |
| `python scripts/verify_forecasting.py` | 30 checks passed |
| `python scripts/verify_dashboard.py` | 63 checks passed |
| `python scripts/execute_notebooks.py` | All three notebooks completed in fresh kernels |
| `python -m pip check` | No broken requirements |
| `python -m pytest -q -W error -p no:cacheprovider` | 105 passed |

Phase 2 metrics JSON and forecasting results JSON match the primary evidence
exactly as parsed values. All nine forecasting CSVs match after normalizing text
line endings, including validation/test predictions, comparisons, sensitivities,
horizons, folds and demonstration. This preserves unfavorable held-out results,
parameters, dates, target policy, model selection and metadata lineage.

Source/data/model generation and report writes were confined to that separate
checkout. It is expected to contain regenerated outputs. The primary workspace's
historical analytical evidence was preserved.

## Initial Phase 5 quality assurance

[Machine-readable verification](phase_5_verification.json) records stage outcomes,
timings, comparisons and checks without machine-specific absolute paths.

| Check | Result |
| --- | --- |
| Primary `python -m pytest -q -W error -p no:cacheprovider` | 105 passed in 18.61s |
| Ruff lint and formatting verification | Passed |
| `python -m pip check`; installed versions versus dependency lock | Passed; no mismatches |
| Primary Phase 1–4 verification | 7 data checks, 3,982 SQL/pandas comparisons, 30 forecast checks and 63 dashboard checks passed |
| `python scripts/verify_portfolio.py` | Initial 11-document structure passed; the current public documentation contract replaces internal process documents |
| Three documentation failure probes in the temporary checkout | Broken local link, stale revenue and invented CLI command each rejected |
| README external links | UCI, DOI, license and author profile each returned HTTP 200 |
| Fresh-artifact browser smoke test | Overview amounts correct; Predictive page loaded seven regenerated forecast rows and five charts without exceptions |
| Protected primary-workspace evidence | 191 of 193 pre-existing tracked/data files unchanged; only README and CI workflow intentionally changed |
| `git diff --check` | Passed |

For primary-workspace verification, loaded the four existing verifier modules in
memory and omitted only final `write_text` report expressions: forecasting line 92
and dashboard line 127. All verification logic ran; their source files and historical
reports remained unchanged. The fresh checkout ran the unmodified scripts directly,
including report generation. Test/cache outputs were kept outside the primary tree.

Six captures were visually reviewed and reused. Historical `.png` names contain
JPEG-encoded bytes; image decoding and dimensions pass. Renaming historical evidence
would create unnecessary reference churn, so names and bytes remain intact and the
gallery explains this. No duplicate screenshots were added.

The fresh-app smoke check is additional reproduction evidence, not a new 40-state
visual audit. The earlier final acceptance covered all five pages, both currencies
and themes at 600px/1280px. Application code is unchanged in Phase 5.

## Technical limitations

Public deliverables describe the implemented system, measured evidence and
reproducible workflow. No public deployment or hosted service is claimed.

Windows Python 3.11 is tested. macOS/Linux instructions are command equivalents,
not independent platform validation. Existing browser evidence is practical QA,
not universal device testing or formal accessibility certification. Illustrative
FX, missing-ID bias, duplicate ambiguity, uncertain gaps, partial boundaries,
short history and a stronger held-out seasonal baseline remain explicit.

No analytical replacement or accuracy gain is proposed. Optional future work is
immutable experiment records, independent new history, calibrated intervals,
broader accessibility and production-specific operational design.

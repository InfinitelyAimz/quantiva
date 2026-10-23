# Quantiva Community Cloud preparation

Status: the owner-approved runtime archive is published as `deployment-runtime-v1`
and its public download has passed independent size and SHA-256 verification.
The separate dashboard deployment is authorized, with hosted acceptance still pending.
The existing compatibility canary remains a separate application and branch.

## Deployment contract

- Repository: `InfinitelyAimz/quantiva`.
- Proposed deployment branch: `deployment/community-cloud`, based on accepted main
  `ccf0b1b41b56ead1f13b07796d25e50bdc4e1fb5`.
- Main file: `app/Home.py`; Python selector: `3.11`.
- Root `environment.yml` reuses the canary's CPython **3.11.9** conda-forge build,
  Conda-owned pip **26.2.2**, 85 unchanged application/development pins and Linux
  closure `pexpect==4.9.0` / `ptyprocess==0.7.0`. The root reproduction lock is unchanged.
- An editable local package install (`-e .`) exposes `quantiva` and packaged SQL,
  preserving source-relative path resolution. The environment file is at the root
  so the local package path is relative to that root; verify this in Cloud build logs.
- NumPy **2.4.6**, pandas **2.3.3**, scikit-learn **1.9.1**, SciPy **1.17.1** and
  joblib **1.6.0** remain exact. Do not substitute another Python patch or libraries.
- All existing model checksum, metadata, dependency and evaluation-provenance
  checks remain in force. There is no retraining or precomputed-only fallback.

Community Cloud searches the entrypoint directory, then the root, for dependency
files. This branch has no competing environment file beside `app/Home.py`.
Do not deploy the canary entrypoint or repurpose its application.

## Private package and publication review

`artifacts.json` is the reviewable allowlist and trust anchor. It records actual
archive/file SHA256 values, exact lengths, accepted project provenance, UCI source
checksum, evaluation-report checksum and CC BY 4.0 attribution. Its URL points to the
versioned `deployment-runtime-v1/quantiva-runtime.tar.gz` release asset and
`publication_review.approved` is `true`, following explicit owner approval and
independent public-download verification. The original archive and all file hashes
are unchanged. Provisioning remains opt-in through `QUANTIVA_DEPLOYMENT=1`.

The archive itself contains exactly eight regular files:

| Path | Bytes |
| --- | ---: |
| `data/processed/quantiva.db` | 156139520 |
| `data/processed/cleaning_report.json` | 658 |
| `data/processed/initial_inspection.json` | 1891 |
| `data/processed/forecasting/daily_series.parquet` | 15743 |
| `data/models/selected.joblib` | 132916 |
| `data/models/context.csv` | 7441 |
| `data/models/metadata.json` | 7177 |
| `data/models/manifest.json` | 269 |

The database contains transaction-level records and pseudonymous customer IDs. Public
distribution and the dashboard's customer-detail exports expose these UCI identifiers;
the bundle is not anonymous or aggregate-only. No names or contact fields are part of
the database schema. Descriptions are source free text and require review too.

### Dataset attribution and software licensing

Dataset: **Online Retail**. Creator: **Daqing Chen**.
Repository: **UCI Machine Learning Repository**.
[Original dataset](https://archive.ics.uci.edu/dataset/352/online+retail).
[DOI: 10.24432/C5BW33](https://doi.org/10.24432/C5BW33).
License: **Creative Commons Attribution 4.0 International (CC BY 4.0)**.
[License terms](https://creativecommons.org/licenses/by/4.0/).

Quantiva's SQLite database, analytical outputs and forecasting artifacts are derived
from the original UCI dataset through documented cleaning, normalization, relational
modeling, feature engineering and model fitting.

Quantiva is an independent project. No endorsement by UCI or the original dataset creator is claimed or implied.

The dataset's CC BY 4.0 license does not license Quantiva's own software. No explicit
Quantiva software license is currently provided; this documentation introduces none.
Do not represent the dataset license as a license for all Quantiva code or model
reuse. Any separate licensing decision requires owner approval.

Publish the attribution and checksum manifest alongside any approved archive. Keep
them outside the existing eight-file archive; its bytes and approved digest stay fixed.

### Future release attribution notice — draft only

The following notice is prepared for future release notes. It is not a published
release or authorization to distribute the archive:

> This release distributes Quantiva runtime artifacts derived from **Online Retail**
> by **Daqing Chen**, UCI Machine Learning Repository (2015).
> [Original dataset](https://archive.ics.uci.edu/dataset/352/online+retail) ·
> [DOI: 10.24432/C5BW33](https://doi.org/10.24432/C5BW33).
> The dataset is licensed under **Creative Commons Attribution 4.0 International**
> ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)).
>
> Quantiva's SQLite database, analytical outputs and forecasting artifacts are
> derived through documented cleaning, normalization, relational modeling, feature
> engineering and model fitting. The database contains transaction-level records
> and pseudonymous customer identifiers; it is not anonymized data.
>
> Quantiva is an independent project. No endorsement by UCI or the original dataset creator is claimed or implied.
>
> CC BY 4.0 applies to the UCI dataset; it does not establish a license for Quantiva's
> own software. No new software license is introduced. Consult the accompanying
> artifact manifest for provenance, exact contents and SHA-256 verification.

The raw workbook, pipeline Parquets/manifests, environments, credentials, private
documents and private backups are excluded. Six existing reports remain in Git:
forecast results, validation/test predictions, duplicate sensitivity, reconciliation
and forecast verification. Keep their accepted versions; do not regenerate on startup.

To reproduce a package locally from the accepted artifacts, choose a **new absolute
directory outside the checkout**:

```text
python scripts/build_deployment_bundle.py --output-directory <new-private-directory>
```

The builder refuses an existing destination or a directory inside the checkout.
It emits deterministic USTAR/gzip bytes without source timestamps, user names or
host paths; verifies extracted bytes; writes a private publication-review manifest;
and makes the completed archive read-only. No upload or Git command is performed
except reading the current commit ID for provenance. Build from the audited project
state and inspect the resulting provenance before approving a later package.

## Provisioning behavior

Normal local startup is unchanged. Only `QUANTIVA_DEPLOYMENT=1` enables provisioning.
On Community Cloud this nonsecret string may be provided at the top level of its
secrets configuration; Streamlit 1.66.0 loads top-level string values into the process
environment. Do not add credentials. Optional `QUANTIVA_DEPLOYMENT_CACHE` selects
a writable cache; otherwise the operating system's temporary directory is used.

The bootstrap downloads the fixed approved HTTPS URL, checking redirects before
following them. It allows at most five redirects, 64 MiB compressed and 200 MiB
expanded, with exact manifest sizes also enforced. Connection/read timeouts are
10/30 seconds and the transfer budget is 180 seconds, checked between chunks.
It streams to disk rather than buffering the database in memory.

The repository's approved archive digest authenticates the expected first-party
bytes. A download-supplied manifest is never trusted. Every extracted member must
match the exact path, type, size and SHA256 allowlist. Links, traversal, duplicates,
sparse/extended metadata, missing and additional members are rejected.

Initialization is protected by a bounded OS file lock (Windows `msvcrt`, Linux
`flock`). The operating system releases ownership on process termination. Unique
staging directories are never reused; normal exceptions clean them up. A hard-killed
process can leave an unused staging directory, but it cannot become a valid install.
Only a fully verified directory is atomically renamed into its digest-addressed
location. Every reuse rehashes all eight files; a corrupt installed generation fails
closed instead of falling back to the original local data or downloading a replacement.
No accepted source artifact is overwritten. Reports stay rooted in the checkout.

Joblib deserialization is permitted only for the separately approved owner-built
artifact matching the committed digest. Never expose user-selectable model URLs or
uploads. Existing model-loader checks run after provisioning and remain unchanged.

## Approval and first cloud deployment

The current publication and separate dashboard deployment are owner-authorized.
For subsequent artifact versions, the following actions require owner review again:

1. Approve publication of the exact reviewed eight-file package and its attribution.
2. Choose an immutable hosting location, for example a versioned GitHub release
   asset or an approved object store. No host, release name or URL has been reserved.
   Do not use a mutable `latest` URL. A host may replace bytes, but digest checks
   must reject any replacement rather than accept it silently.
3. Approve the exact final HTTPS URL and set it in `artifacts.json`; change the
   publication approval flag only after that approval. Preserve all verified hashes.
4. Separately approve pushing the locally committed deployment branch and uploading
   the package. Local commit authorization does not authorize either external action.
5. Approve creating a **separate** dashboard Cloud application with the entrypoint
   and environment above, proposed public subdomain still to be chosen.

After those approvals, configure `QUANTIVA_DEPLOYMENT="1"`. Retain the canary.
Inspect build logs to confirm the root Conda file, exact interpreter, all runtime
versions, local package installation and `pip check`. Confirm the serving process,
not just a build subprocess, runs CPython 3.11.9. Do not run the reproduction lock's
pip 24.0 self-installation in this deployment environment.

First startup must download, verify and install the bundle before reading catalog
data. Retain build/provisioning observations privately. With no valid bundle or
approval, a clear startup error and no fallback is the expected behavior. Repeat
after a cold reboot/rebuild and verify recovery if temporary storage was lost.

## Verification and acceptance

Local checks:

```text
python -B -m pytest tests -q -W error -p no:cacheprovider
python -B -m ruff check .
python -B -m ruff format --check .
python -B -m pip check
python -B scripts/verify_portfolio.py
```

Run data, SQL, forecasting and dashboard checks against accepted artifacts too.
Forecast/dashboard scripts write reports: copy scripts and reports into a private
verification directory and point `QUANTIVA_DATA_DIR` at the accepted data rather
than overwriting evidence. Expected counts: 7 data checks, 3982 SQL reconciliations,
30 forecasting checks and 63 dashboard checks. Preserve the original 105 tests.

Cloud acceptance must include:

- All five pages load without setup, missing-artifact or integrity warnings.
- Both themes and GBP/ZAR; navigation persistence; dates, country/product filters,
  customer segments, empty-result scopes and CSV exports behave correctly.
- Browser widths 600px and 1280px show readable charts and complete KPI values.
- All seven saved-model predictions match accepted evidence and repeated inference.
  Evaluation metrics/model ranking stay unchanged; seasonal naive's better held-out
  performance remains disclosed. No cloud retraining or metadata editing.
- Historical 2010–2011 coverage, partial boundary periods, forecast limitations and
  fixed illustrative ZAR conversion remain clear. No live-data claim is introduced.
- The current model-integrity button passes, before and after a cold restart.
- Measure actual Linux/container peak and idle memory, extraction, cold/warm page
  times, cache churn and at least two simultaneous sessions. The approximate 2.7 GB
  platform maximum is not guaranteed. Check headroom against the observed allocation.

The prior Windows single-session measurements were 260.8 MiB peak RSS and 674.1 MiB
private commitment, with an 84.72-second first Overview render. These are historical
local observations, not Cloud guarantees. Do not call HTTP health full page readiness.

## Rollback and limitations

Before release, retain the last verified deployment commit, package URL and digest.
If a controlled cloud test fails, stop promotion; do not relax checks or retrain.
For an already accepted deployment, obtain approval to restore its configuration
through a normal follow-up branch commit or Cloud deployment selection. Restore the
matching manifest/package pair, leaving main, model evidence and history intact.
Do not delete branches or repurpose the canary as rollback. This first dashboard
deployment has no previously verified production application to fall back to.

Windows tests cannot establish Linux locking, exact Conda activation, joblib platform
equivalence, cloud memory limits or browser acceptance. Those remain explicit cloud
gates. No historical GitHub PR references or caches are claimed to have been purged.

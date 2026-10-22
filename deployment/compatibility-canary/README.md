# Quantiva runtime compatibility canary

This isolated Option A probe tests the serving interpreter and dependencies before
attempting any deployment of Quantiva's five-page dashboard. It does not import
Quantiva, read datasets/models/databases, train anything or modify analytical evidence.
The production entry point remains `app/Home.py`.

## Environment

`environment.yml` requests the normal conda-forge Linux x86_64 build of CPython
**3.11.9** (`hb806964_0_cpython`). Its pip section mirrors all 86 accepted
`requirements-lock.txt` pins, then adds the Linux dependency closure
`pexpect==4.9.0` and `ptyprocess==0.7.0`. Inline pins avoid ambiguity about paths
relative to Conda's temporary pip requirements file. The configuration test rejects
drift from the accepted lock. No Quantiva package installation is needed by this probe.

The in-process contract includes NumPy **2.4.6**, pandas **2.3.3**, scikit-learn
**1.9.1**, SciPy **1.17.1** and joblib **1.6.0**. Streamlit **1.66.0** and psutil
**7.2.2** are also checked. Linux additionally checks pexpect and ptyprocess.
Forecasting pipeline classes are imported without loading any model.

Community Cloud documents Conda support and searches the entry point's directory
before the repository root. That allows this environment file to apply to the
canary without replacing the dashboard's packaging or root Streamlit configuration.
Recognized configuration does **not** prove that Cloud activates the requested Python.
Only diagnostics from the actual hosted serving process can establish that.

## Local checks

From the checkout root, using the existing verified Python 3.11.9 environment:

```powershell
.\.venv\Scripts\python.exe -B -m pytest deployment/compatibility-canary/test_canary.py -q -W error -p no:cacheprovider
.\.venv\Scripts\python.exe -B -m ruff check --no-cache deployment/compatibility-canary
.\.venv\Scripts\python.exe -B -m ruff format --check --no-cache deployment/compatibility-canary
.\.venv\Scripts\python.exe -B -m streamlit run deployment/compatibility-canary/canary.py --server.address=127.0.0.1 --server.port=8510 --browser.gatherUsageStats=false
```

A Windows runtime match validates local canary behavior, not Linux/Conda activation
or Community Cloud compatibility. The UI tests use the existing local environment;
they do not create or solve the Conda environment. They intentionally require the
accepted interpreter and package versions. Tests are scoped explicitly because the
existing project suite's default discovery remains `tests/`.

If an approved Linux machine already has Conda, the separate environment can be
created using `conda env create -f deployment/compatibility-canary/environment.yml`.
Run it with `conda run -n quantiva-compatibility-canary python -m streamlit run
deployment/compatibility-canary/canary.py`. This command is preparation guidance,
not a claim that the Conda solve or Linux execution has passed. Do not install OS
tooling solely to run this probe without authorization.

## Proposed Community Cloud configuration

| Setting | Value |
|---|---|
| Repository | `InfinitelyAimz/quantiva` |
| Temporary branch | `deployment/compatibility-canary` |
| Main file path | `deployment/compatibility-canary/canary.py` |
| Advanced Python selector | Explicitly choose `3.11` |
| Conda file | `deployment/compatibility-canary/environment.yml` |
| Secrets / credentials / data directory override | None |
| Proposed subdomain | `quantiva-runtime-canary` |
| Proposed URL | `https://quantiva-runtime-canary.streamlit.app/` |

The branch must be reviewed and published with owner approval first. The proposed
URL is not reserved or deployed; availability is unknown. Do not accidentally
select `main` or `app/Home.py`. Do not add a competing dependency file beside the
canary. No custom bootstrap, alternate interpreter subprocess or Docker workaround
is involved. Cloud manages its launch port; the report records effective address,
port and headless configuration. The accepted root loopback config is unchanged.
If routing fails, stop for review rather than changing production settings.

## Build and runtime acceptance

1. Retain the complete build log. Check the selected Conda file, normal Python
   build, package installation and any platform overrides. Installation logs alone
   are insufficient; failure to solve, provision or activate the environment is
   **NO-GO for this configuration**.
2. Open the canary URL. Download its observation JSON and retain the corresponding
   `QUANTIVA_CANARY_OBSERVATION` runtime log privately. It records `sys.version`,
   `sys.executable`, PID, process creation time, implementation/platform, installed
   and imported versions, native forecasting imports and the pip check command,
   exit status and output. Do not commit diagnostic outputs, logs or local paths.
3. Require Linux, CPython **3.11.9 exactly**, every required package version, all
   imports, and `pip check` exit status zero. A mismatch or missing check is
   **NO-GO**; never relax the comparisons or alter Quantiva metadata/checksums.
4. Use Cloud's cold reboot/rebuild operation and retain that operation's logs.
   Download a second passing observation. Require a changed process creation time
   and a new process instance token. PID may be reused. Widget refresh, a browser
   reload or clearing Streamlit caches is not a cold restart; a changed UUID alone
   does not prove a new process.
5. Recompare accepted source/artifact hashes. Record the tested branch commit and
   Cloud URL with both observations. Only then may the owner conclude **GO for
   the runtime gate**. The app itself never promotes one matching observation to
   cloud acceptance: `cloud_acceptance` remains `UNVERIFIED` until manual review.
6. Stop after the canary. A passing runtime gate does not approve artifact uploads,
   full-dashboard deployment, model deserialization, browser acceptance or the
   full application's cloud resource usage. Those remain separate checks.

Only `pip check` is executed in a child process, using the observed
`sys.executable`. Python version, imported module versions, native class imports
and platform details are gathered directly in the Streamlit script's process.
The probe reads no environment variables, secrets, hostnames or arbitrary files.
Its only export is the displayed/downloadable observation JSON and structured log.

## Authorization boundary

Local preparation does not authorize a push, hosting-account authentication,
account connection, application creation, deployment or artifact upload. Obtain
explicit owner approval before any of those actions. Do not switch to a
precomputed-forecast mode if this configuration fails.

## Official references

- [Community Cloud dependency discovery and Conda support](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)
- [Python selector and deployment settings](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [Conda Python management](https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-python.html)

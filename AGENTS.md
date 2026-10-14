# Repository workflow

- Preserve existing work, commits, and Git history.
- Develop Phase 3 on `phase-3`. Future phases use `phase-4`, `phase-5`, etc., without a `codex/` prefix.
- Before edits, commits, or pushes for a phase, inspect the active branch, local and remote branches, uncommitted changes, and existing phase commits. Inspect an existing phase branch before switching to it and preserve its work.
- Verify the active phase branch before every commit. Never commit or push directly to `main`.
- Run relevant checks, push the phase branch, and open a draft pull request targeting `main` when there are changes to propose. Verify that the branch exists on GitHub.
- Do not merge branches or enable automatic merging. Do not reset, force-push, delete branches, or rewrite history.
- If phase commits are already on local or remote `main`, report them; do not rewrite `main` to remove them.
- Stop and ask the user before corrective action for conflicts, unexpected remote changes, or other synchronization issues.
- Do not begin a subsequent project phase without explicit user approval.
- Report the branch, commit SHA, test results, and pull request link at completion.

These instructions reflect the user's updated workflow and supersede older branch names and commit/push restrictions in saved phase specifications. Requirements in `PROJECT_SPECIFICATION.md` and the applicable phase specification remain authoritative for implementation scope.

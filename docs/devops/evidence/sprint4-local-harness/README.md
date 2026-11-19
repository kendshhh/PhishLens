# Local evidence harness (Windows)

These are the exact one-off November 19 harnesses with one portability change:
the PostgreSQL binary directory now comes from `PHISHLENS_TEST_PG_BIN` instead of
the author's existing local archive path. They never use a shared database.

Prerequisites: Python 3.12, Node 24, Git, uv (or install the identical pinned dev
requirements with pip), PostgreSQL 17 binaries and installed Microsoft Edge.
Run from a repository checkout containing these evidence files, using PowerShell:

```powershell
$work = Join-Path (Get-Location) 'output/sprint4-local-verification'
New-Item -ItemType Directory -Force $work | Out-Null
git worktree add --detach "$work/source" ba67296af4023f89145fe2e509371ca6e9084462
py -3.12 -m venv "$work/source/.review-env"
uv pip sync --python "$work/source/.review-env/Scripts/python.exe" "$work/source/backend/requirements-dev.txt"
npm --prefix "$work/source" ci
Copy-Item docs/devops/evidence/sprint4-local-harness/*.py $work
Copy-Item docs/devops/evidence/sprint4-local-harness/*.mjs $work
$env:PHISHLENS_TEST_PG_BIN = 'C:/path/to/installed/PostgreSQL/17/bin'
& "$work/source/.review-env/Scripts/python.exe" "$work/run_local_postgres.py"
& "$work/source/.review-env/Scripts/python.exe" "$work/run_web_postgres.py"
Remove-Item Env:PHISHLENS_TEST_PG_BIN
```

Use a new output directory when reproducing. `run_local_postgres.py` verifies
migration, seed, full regressions and dump/restore. `run_web_postgres.py` runs the
browser journey. Each creates its own SCRAM-authenticated loopback-only cluster
with a random port and password, stops its API/database processes in `finally`,
and removes temporary password/key/token fixture files. Retained clusters contain
only synthetic data. Do not publish raw logs or cluster directories. Share only
reviewed redacted aggregates and synthetic screenshots.

The browser test intercepts the Auth SDK module and test Auth requests. It verifies
application code, real JWT signature/claims validation after substituted key
retrieval, real TF-IDF inference and actual PostgreSQL transactions. It does not
verify the packaged Neon SDK, live cookies, email delivery, OTP, session revocation,
Vercel rewrites, shared service health, deployment or recovery time.

The first browser attempt used Uvicorn's Windows Proactor default and received a
controlled storage 503. The corrected harness uses the repository's documented
`backend.core.event_loop:new_event_loop` factory. A subsequent assertion was also
corrected to expand **About this result** before reading its provenance. Those
failed harness attempts were cleaned up and are not counted as passing results.

The web harness rebuilds `web/dist` in development mode and removes Vercel output;
rebuild with the intended public settings before making a deployable artifact.

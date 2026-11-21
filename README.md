# PhishLens

PhishLens is an AI-powered phishing email detection and analysis
system. It helps users identify suspicious emails, understand
risk indicators, and manage saved analysis reports.

## Current Status — November 21, 2026

The current release decision is **NO-GO**. The latest observed GitHub `main` is
`811980c2cbf70d9957146bf329627f0826a018f1`. This closeout is prepared on
`codex/devops-staging-closeout-20261121`, based on the staging-history repair
commit `3c858f7df51666e0545dea1a6dd5997574c16d43` (a descendant of that main).
The implementation is recorded in commit
`a80b95e146cd03a96ffca156ccfe5721ac871b68`; its workflow has not run in hosted
GitHub Actions.
The original developer checkout at `16f955321caf5dc368181be7ce5c00643750545d`
remains dirty and was preserved. Production serves main with analysis intentionally disabled.
Staging serves a different SHA and requires Bearer authentication for
saved-report history. The review branch now includes strict anonymous-auth
smoke handling, bounded retries and failure summaries, early local-server crash
detection/log retention, and fail-closed hosted deployment gates. Focused Node
tests pass; no hosted workflow rerun or authenticated CRUD acceptance is
recorded. The live endpoint probe from this workstation timed out, so it did
not refresh the prior read-only staging observation.

Render currently reports auto-deploy off for both services, while production's
latest deploy record says `new_commit`; resolve that configuration/evidence
discrepancy before relying on deployment behavior. The effective GitHub required
checks and private Render-to-Neon role mapping are also not verified. There is
no approved release score; no percentage should be reported.

Use the [DevOps evidence index](docs/devops/README.md) for the current release
record, environment map, scorecard, staging failure evidence, runbooks and
closeout prompt. See [PIPELINE.md](PIPELINE.md) for the current delivery view
and [pipeline metrics](docs/devops/metrics.md) for dated, bounded measurements.
Historical status reports remain dated snapshots. The isolated Chrome software
audit and synthetic browser evidence for Issue #131 are recorded in
[the installed-browser audit](docs/frontend/issue-131/audit.md).

## Planned Features

- Submit email content for analysis.
- Classify emails as phishing or legitimate.
- Display risk levels, indicators, and explanations.
- View saved analysis history.
- Update notes and feedback.
- Delete saved analyses.

## Technology Stack

| Component | Selected Technology |
|---|---|
| Frontend | Chrome extension using HTML, CSS, and JavaScript |
| Backend | Python with FastAPI |
| Database | PostgreSQL hosted on Neon |
| AI | Local TF-IDF v12a, Llama judge, then TF-IDF + linear-kernel KRR + LightGBM review |
| Version control | Git and GitHub |
| CI/CD | GitHub Actions with gated staging deployment; production deploy trigger is unresolved |
| Backend hosting | Render Free; https://phishlens-api-ocvt.onrender.com |

Scans run locally in Chrome. The extension contacts the backend only for explicit
saved-report and history operations. The backend owns database access and replays
the classifiers before saving a local review. Its matching save configuration is
`AI_MODE=tfidf`; it attributes LLM audits to the browser.

The implementation is verified locally, with benchmark history preserved
separately. This combined workflow has no new accuracy qualification or public
deployment claim. See [setup, workflow and limits](docs/ai/live-workflow.md).

Neon hosts PostgreSQL; Render hosts the FastAPI backend.

See the current [architecture and environment map](docs/architecture.md) and
[architecture decision record](docs/adr/0001-application-and-deployment-architecture.md).

### Database Decision

The team selected PostgreSQL hosted on Neon, replacing MySQL
from the original project proposal.

This change must be recorded in the scope change log and
communicated to the instructor at Consultation 1.

## Team Roles

| Member | Role | Primary Responsibility |
|---|---|---|
| Kendra | DevOps Engineer | Git workflow, CI/CD, deployment, secrets, and delivery evidence |
| Wilberr | AI Engineer | Model integration, inference, evaluation, and AI output structure |
| Trixia | Backend Developer | API foundation, database models, migrations, and validation |
| Leyan | Fullstack Developer | Saved-history API/UI integration and shared API contract |
| Andrei | Frontend Developer | Chrome extension interface and user-facing states |

Members coordinate before editing shared files or another
member's components.

## Original Sprint 1 Goals (Historical)

- Establish the repository and collaboration workflow.
- Create a backlog covering the instructor's requirements.
- Implement and migrate related database tables.
- Connect the frontend to a database-backed API endpoint.
- Run automatic install, lint, and build checks on every pull request.
- Deploy the walking skeleton to a live public URL through the pipeline.
- Demonstrate one successful AI inference call through the backend.

## Collaboration and Delivery Workflow

The [DevOps Secretary pilot](docs/devops/secretary.md) adds a trusted PR evidence
report, exact-commit staging extension builds, and production observation.
It requires owner setup and review before activation; it cannot approve or merge.
See the guide for click-by-click setup, manual tests, costs and disable steps.

Our target workflow is:

1. Create an assigned issue with acceptance criteria.
2. Create a task branch from updated main.
3. Implement and verify the change.
4. Open a pull request and request teammate review.
5. Pass the automated checks before merging.
6. Merge approved work into main.
7. Deploy the successfully checked version using the owner-approved Render
   policy, then verify the observed trigger and exact deployed SHA.
8. Verify deployed behavior and record evidence. The current automatic-deploy
   setting is unresolved; see the [DevOps evidence index](docs/devops/README.md).

See [CONTRIBUTING.md](CONTRIBUTING.md) for commands and team ownership.

### Automation Status

CI, extension validation, packaging and staging workflows are configured, but
their effective required-check contract and current hosted staging acceptance
are not verified. The latest staging smoke patch passes locally; the hosted
workflow still needs an authenticated CRUD session and exact-candidate
acceptance. Production analysis is disabled, and no browser/release candidate is
accepted. See [PIPELINE.md](PIPELINE.md), the
[DevOps evidence index](docs/devops/README.md),
[metrics](docs/devops/metrics.md), and the
[deployment and recovery runbook](docs/devops/runbook.md).

Sprint 1 acceptance targets:

- Automatic dependency installation, lint, and build checks on every PR.
- Protected main with required checks and at least one teammate review.
- Automatic deployment after successful checks on every merge to main.
- A public walking skeleton connected to the database.
- Pipeline documentation and baseline metrics.

The automatic-deployment target is not currently verified: Render metadata says
auto-deploy is off, while the latest production deployment record says
`new_commit`.

Pull request checkboxes document verification.
They do not replace automated checks or reviewer approval.

## Local Setup

The backend database schema, synthetic demo seed and FastAPI scaffold can run locally.
For schema rehearsal, use an empty disposable PostgreSQL 17 database; the current CI
runtime uses Python 3.12 and PostgreSQL 17. See [the schema and migration guide](docs/schema.md)
for the migration chain, schema details, and seed side effects. Local results do not
establish hosted staging or production behavior.

### Backend Setup

Create a Python virtual environment, install `requirements.txt`, and set `DATABASE_URL`
in a private `.env` to an empty disposable local PostgreSQL database. The backend
explicitly loads this file. For a local disposable database, use a role that owns the
database and can create objects in its `public` schema so Alembic can apply migrations.
Do not place staging or production credentials in this file. Use the URL format
`postgresql://USER:URL_ENCODED_PASSWORD@HOST/phishlens_dev?sslmode=require`;
for Neon; for local PostgreSQL, a local URL such as
`postgresql+psycopg://phishlens:local-only-password@127.0.0.1:55432/phishlens_dev`
works with the `psycopg` driver. The current Alembic setup reads `DATABASE_URL`.

To create a disposable PostgreSQL 17 database with Docker (Docker Desktop or Docker
Engine must already be installed), run this from any terminal:

```sh
docker run --detach --name phishlens-docs-db \
  --env POSTGRES_USER=phishlens \
  --env POSTGRES_PASSWORD=local-only-password \
  --env POSTGRES_DB=phishlens_dev \
  --publish 55432:5432 postgres:17
```

Use `postgresql+psycopg://phishlens:local-only-password@127.0.0.1:55432/phishlens_dev`
for this container. The password is only a disposable local example; never reuse it
for a hosted database. If port `55432` is occupied, choose another host port and use
that port in `DATABASE_URL`. When finished, `docker rm --force phishlens-docs-db`
removes the container and its disposable database.

From the repository root on macOS/Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
test -e .env || cp .env.example .env
# Fill DATABASE_URL in .env privately before continuing.
.venv/bin/python -m alembic -c backend/alembic.ini upgrade head
.venv/bin/python scripts/seed_demo.py
```

From the repository root on Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Fill DATABASE_URL in .env privately before continuing.
.\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
.\.venv\Scripts\python.exe scripts/seed_demo.py
```

The seed uses only synthetic data and refuses a database other than `phishlens_dev`.
It is safe to repeat on the disposable database, but it can create the fixed demo rows
or correct the fixed analysis subject. Each teammate needs their own private `.env`; Git does
not distribute credentials. See [docs/schema.md](docs/schema.md) for field types and
the deletion policy. `.env.example` contains only settings read by the local app.
Hosted staging credentials and GitHub environment secrets are listed by name in
[the staging runbook](docs/devops/staging.md); configure them only in their protected
stores.

### Run AI analysis locally

PhishLens uses the bundled TF-IDF v12a model. The extension scores selected
text locally and sends it to `POST /api/analyses` when a user chooses Save.
Set `AI_MODE=tfidf` in the backend's private `.env` to enable matching saves.
Use `POST /analyses` for a direct inference call without a database write.
The default `AI_MODE=mock` is for development and CI. See the
[AI contract and setup](docs/ai.md) for model provenance, score policy and evidence.

Start the backend from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --loop backend.core.event_loop:new_event_loop
```

Use the explicit loop factory for saved-analysis persistence. On Windows it
selects SelectorEventLoop, which Psycopg async connections require. It also
works with `--reload`; reload is optional. On macOS/Linux, use
`.venv/bin/python -m uvicorn backend.app.main:app --loop backend.core.event_loop:new_event_loop`.
The staging startup script uses the same factory.

Call the analysis endpoint directly after starting in TF-IDF mode:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/analyses `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"text":"Your account will be closed today."}'
```

With `AI_MODE=gemini` and valid credentials configured, verify the provider connection:

```powershell
.\.venv\Scripts\python.exe scripts\test_gemini_connection.py
```

For local development, set `API_BASE_URL` in `extension/js/config.js` to
`http://127.0.0.1:8000` and add `http://127.0.0.1:8000/*` to the manifest's
`host_permissions`. Reload the extension after changing configuration. The default
source package targets production; the separate staging package targets staging.

## Install in Chrome

PhishLens requires Chrome 127 or newer. There is no Chrome Web Store listing yet.
To install from the public GitHub repository:

1. Download the repository ZIP and extract it to a folder you will keep.
2. From that folder, run `npm run phishlens -- setup-models --download`. This
   downloads and verifies about 1.1 GB of local LLM weights; without them, scans
   report **Uncertain** when the full review cannot run.
3. Open `chrome://extensions`, enable **Developer mode**, choose **Load unpacked**,
   and select the extracted `extension` folder.
4. To check an email, select its text, right-click, and choose **Analyze selection
   with PhishLens**. The PhishLens popup opens with your selection and the result.
5. Optionally, pin PhishLens from Chrome's Extensions menu. Its toolbar button opens
   the same view in the side panel, which stays open while you read email.

PhishLens shows a ready state before scanning, progress while local models load,
a result or an explicit uncertainty/error state, and a Clear action. Scanning stays
in Chrome. The full local review also requires WebGPU with shader-f16 support.
Saving a report or refreshing shared history contacts the configured API.

## Configuration and Secrets

- Never commit real credentials or private `.env` files.
- Use `.env.example` to document configuration without real secrets.
- Keep database credentials and security secrets on the backend.
- Configure deployment secrets through the host or CI secret store.
- Use synthetic emails for tracked examples and demonstrations.
- Keep private datasets and downloaded model files out of Git.

The Chrome extension does not automatically read `.env` files.
Its public backend origin is configured in `extension/js/config.js` for both
analysis and history. See [staging instructions](docs/devops/staging.md) for the
separate acceptance package.

For a presenter-ready synthetic walkthrough with exact package identity, accessible
keyboard steps, screenshots and environment labels, see the
[clean-install and demo guide](docs/frontend/issue-141/demo-guide.md).

## Project Requirements

The instructor's guide is the main authority for requirements,
workflow, deliverables, and grading:

[Read the instructor guide](https://csp221a.vercel.app/)

[Consultation 2 preparation and remaining requirements](docs/devops/consultation-2.md)
records the demo agenda, evidence gaps and Sprint 3/4 handoff.

## Selected TF-IDF integration pilot

The current live implementation follows the teacher's per-scan workflow:
**TF-IDF v12a → local LLM judge → TF-IDF + KRR + LightGBM reevaluation → reviewed
result or Uncertain**. See [the live workflow and setup](docs/ai/live-workflow.md).

The branch `codex/tfidf-v12a-workflow-20261029` connects the frozen v12a model
to local Chrome selection scanning and the contributors' optional saved-report
workflow. See [setup and debugging](docs/TFIDF_DEBUGGING.md),
[the integration plan](docs/tfidf-integration-plan.md), and
[preserved benchmark evidence](benchmark-records/index.html).

Quick developer checks: `npm run doctor`, `npm test`, `npm run lint`, and
`npm run phishlens -- records-check`. Load `extension/` unpacked in Chrome.
Scanning stays local. Saving requires explicit upload consent and a matching
`AI_MODE=tfidf` backend. Hosted configuration and databases are managed separately.

The selected candidate passed eight measured scoped benchmark checks; the
original independent OOD/adversarial and fresh authenticated bank coverage remain
incomplete. Integration checks do not replace those measurements.

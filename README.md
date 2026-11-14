# PhishLens

PhishLens is an AI-powered phishing email detection and analysis
system. It helps users identify suspicious emails, understand
risk indicators, and manage saved analysis reports.

## Current Status — November 14, 2026

Current `main` is `ddc0ab1`. Backend, extension, PostgreSQL integration,
dependency-security, CodeQL, and workflow checks are configured; main is protected
and successful main changes auto-deploy through Render. The refreshed 28-day
delivery snapshot is in [pipeline metrics](docs/devops/metrics.md).

Sprint acceptance is not complete. Merged [PR #192](https://github.com/kendshhh/PhishLens/pull/192)
adds synthetic browser acceptance evidence, and merged [PR #193](https://github.com/kendshhh/PhishLens/pull/193)
adds a guarded Auth acceptance procedure; neither is evidence of a connected
staging run or live Auth acceptance. [PR #196](https://github.com/kendshhh/PhishLens/pull/196)
adds deterministic AI evaluation on AI changes and fail-closed Gemini spend checks,
but remains open. Its 40-case result is development regression evidence, not a
held-out quality result or an approved model threshold. [PR #198](https://github.com/kendshhh/PhishLens/pull/198)
records an exact-SHA production smoke that stopped before analysis because the
production model mode was unavailable; it made no analysis request, database
write, or paid call. Its staging CRUD evidence used a test-branch SHA, not current
main. Merged [PR #189](https://github.com/kendshhh/PhishLens/pull/189) reconciles
historical Sprint 2 CRUD evidence but leaves hosted acceptance on hold pending
confirmation of the selected backend, database and authentication target.
On November 14, read-only `/version` probes reported production at
`ddc0ab16d5cdee97d88de2cd2b899e6ee6ba2213` (`main`) with
`provider_mode=unavailable`, and staging at `dcd234e0e012e1a869e182e64d34728343d17637`
with `provider_mode=tfidf`. Both `/health` and `/ready` returned HTTP 200;
readiness reported a connected database but does not identify its Neon branch.
Current DevOps acceptance gaps and named handoffs are tracked in the
[Sprint 1–3 closeout](docs/devops/kendra-sprint-1-3-status-2026-11-14.md).
The isolated Chrome software audit and synthetic browser evidence for Issue #131
are recorded in [the installed-browser audit](docs/frontend/issue-131/audit.md).

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
| CI/CD | GitHub Actions and Render deployment after CI passes |
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
7. Automatically deploy the successfully checked version.
8. Verify the deployed behavior and record evidence.

See [CONTRIBUTING.md](CONTRIBUTING.md) for commands and team ownership.

### Automation Status

Backend CI/CD is configured and verified. Extension tests, validation, packaging,
isolated API integration, and hosted staging checks are configured. Full application
acceptance remains pending for installed Chrome, production persistence, and real AI.
See [PIPELINE.md](PIPELINE.md) for implemented checks,
[metrics](docs/devops/metrics.md) for the measured snapshot, and the
[runbook](docs/devops/runbook.md) for deployment and recovery.

Sprint 1 acceptance targets:

- Automatic dependency installation, lint, and build checks on every PR.
- Protected main with required checks and at least one teammate review.
- Automatic deployment after successful checks on every merge to main.
- A public walking skeleton connected to the database.
- Pipeline documentation and baseline metrics.

Pull request checkboxes document verification.
They do not replace automated checks or reviewer approval.

## Local Setup

The backend database schema, synthetic demo seed and FastAPI scaffold can run now.

### Backend Setup

Create a Python virtual environment, install `requirements.txt`, and set a development
Neon `DATABASE_URL` in a private `.env`. The backend explicitly loads this file. The
database role needs `CONNECT` on the development database and `USAGE, CREATE` on its
`public` schema so Alembic can apply migrations. Use the Neon URL format
`postgresql://USER:URL_ENCODED_PASSWORD@HOST/phishlens_dev?sslmode=require`;
the backend uses the `psycopg` driver. The current Alembic setup reads `DATABASE_URL`.

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

The seed uses only synthetic data, refuses a database other than `phishlens_dev`, and
is safe to run more than once. Each teammate needs their own private `.env`; Git does
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

PhishLens requires Chrome 116 or newer. There is no Chrome Web Store listing yet.
To install from the public GitHub repository:

1. Download the repository ZIP and extract it to a folder you will keep.
2. From that folder, run `npm run phishlens -- setup-models --download`. This
   downloads and verifies about 1.1 GB of local LLM weights; without them, scans
   report **Uncertain** when the full review cannot run.
3. Open `chrome://extensions`, enable **Developer mode**, choose **Load unpacked**,
   and select the extracted `extension` folder.
4. Pin PhishLens from Chrome's Extensions menu if you want its toolbar button.
   Click the button to open the side panel, or select email text, right-click, and
   choose **Analyze selection with PhishLens**.

The side panel shows a ready state before scanning, progress while local models load,
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

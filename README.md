# PhishLens

PhishLens is an AI-powered phishing email detection and analysis
system. It helps users identify suspicious emails, understand
risk indicators, and manage saved analysis reports.

## Current Status — October 28, 2026

Sprint 2 is in integration and acceptance. Backend and extension checks run in CI;
disposable PostgreSQL gates migrations, seed, and saved-analysis CRUD. Render
production auto-deploys checked `main`, and the staging service has passed exact-SHA
health, readiness, and guarded synthetic CRUD verification. Saved-analysis API
CRUD is implemented. Production record persistence across refresh or redeploy,
installed-Chrome acceptance, and real-provider AI evaluation still need separate
evidence. See the [current DevOps backlog audit](docs/devops/backlog-audit-2026-10-28.md).

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
| AI | DistilBERT running through the backend |
| Version control | Git and GitHub |
| CI/CD | GitHub Actions and Render deployment after CI passes |
| Backend hosting | Render Free; https://phishlens-api-ocvt.onrender.com |

The Chrome extension communicates with the backend API.
The backend owns database access and AI processing.

Neon hosts PostgreSQL; Render hosts the FastAPI backend.

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

See [the AI contract and setup](docs/ai.md) for the provider, token limits, score
mapping, threshold, indicator sources, and optional local CPU model. The
[October 18 DevOps handoff](docs/devops/ai-review-2026-10-18.md) records verification
and the current model, hosting, and extension integration limitations.

The extension sends selected text to `POST /analyses`. The backend runs in mock mode
when `AI_MODE=mock`; the response and extension UI label this as a mock, not an AI result.
To use Gemini, set `AI_MODE=gemini`, `GEMINI_API_KEY`, and a valid `GEMINI_MODEL` in the
private `.env`. The Google API key must never be added to the extension.

Start the backend from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --loop backend.core.event_loop:new_event_loop
```

Use the explicit loop factory for saved-analysis persistence. On Windows it
selects SelectorEventLoop, which Psycopg async connections require. It also
works with `--reload`; reload is optional. On macOS/Linux, use
`.venv/bin/python -m uvicorn backend.app.main:app --loop backend.core.event_loop:new_event_loop`.
The staging startup script uses the same factory.

Call the analysis endpoint directly (mock mode works without Gemini credentials):

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

Then load the `extension` folder as an unpacked Chrome extension, highlight email text,
and choose **Analyze selection with VeriQo**. The popup displays the model result or
reports a configuration/provider error.

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

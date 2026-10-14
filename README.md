# PhishLens

PhishLens is an AI-powered phishing email detection and analysis
system. It helps users identify suspicious emails, understand
risk indicators, and manage saved analysis reports.

## Current Status

The project is in Sprint 1: foundation and walking skeleton.

Backend CI and Render automatic deployment are implemented. PostgreSQL migration,
repeatable seed, and seed integrity checks run in isolated CI. Public /health and
/ready respond successfully; readiness performs a real database query.
The complete frontend/database user flow and AI feature remain unfinished.

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

## Sprint 1 Goals

- Establish the repository and collaboration workflow.
- Create a backlog covering the instructor's requirements.
- Implement and migrate related database tables.
- Connect the frontend to a database-backed API endpoint.
- Run automatic install, lint, and build checks on every pull request.
- Deploy the walking skeleton to a live public URL through the pipeline.
- Demonstrate one successful AI inference call through the backend.

## Collaboration and Delivery Workflow

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

Backend CI/CD is configured and verified. Extension checks and full application
integration remain pending. See [PIPELINE.md](PIPELINE.md) for implemented checks,
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
Chrome extension loading instructions remain dependent on the frontend implementation.

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
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Fill DATABASE_URL in .env privately before continuing.
.\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
.\.venv\Scripts\python.exe scripts/seed_demo.py
```

The seed uses only synthetic data, refuses a database other than `phishlens_dev`, and
is safe to run more than once. Each teammate needs their own private `.env`; Git does
not distribute credentials. See [docs/schema.md](docs/schema.md) for field types and
the deletion policy. A complete application setup is not available yet.

Run the backend from the repository root on Windows:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

Open http://127.0.0.1:8000/health for process status and /ready for a database query.
The root URL / has no homepage. For migrations, use a direct URL in DATABASE_URL:
MIGRATION_DATABASE_URL is not implemented by the current Alembic configuration.
Verify the Neon branch privately; the name phishlens_dev also exists on production
and therefore does not alone establish development isolation. Do not run the demo
seed against production merely because its database-name guard permits it.

## Configuration and Secrets

- Never commit real credentials or private `.env` files.
- Use `.env.example` to document configuration without real secrets.
- Keep database credentials and security secrets on the backend.
- Configure deployment secrets through the host or CI secret store.
- Use synthetic emails for tracked examples and demonstrations.
- Keep private datasets and downloaded model files out of Git.

The Chrome extension does not automatically read `.env` files.
Its public backend URL configuration will be documented separately.

## Project Requirements

The instructor's guide is the main authority for requirements,
workflow, deliverables, and grading:

[Read the instructor guide](https://csp221a.vercel.app/)

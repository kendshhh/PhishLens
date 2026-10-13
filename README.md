# PhishLens

PhishLens is an AI-powered phishing email detection and analysis
system. It helps users identify suspicious emails, understand
risk indicators, and manage saved analysis reports.

## Planned Features

- Submit email content for analysis.
- Classify emails as phishing or legitimate.
- Display risk indicators and explanations.
- View saved analysis history.
- Update notes and feedback.
- Delete saved analyses.

## Technology Stack

- Frontend: Chrome extension using HTML, CSS, and JavaScript
- Backend: Python with FastAPI
- Database: PostgreSQL hosted on Neon
- AI: DistilBERT running through the backend
- Version control: Git and GitHub
- CI/CD: GitHub Actions and automated public deployment
- Hosting provider: To be finalized

The frontend communicates with the backend API.
The backend owns database access and AI processing.

## Team Roles

| Member | Role | Primary Responsibility |
|---|---|---|
| Kendra | DevOps Engineer | Git workflow, CI/CD, deployment, secrets, and delivery evidence |
| Wilberr | AI Engineer | Model integration, inference, evaluation, and AI output structure |
| Trixia | Backend Developer | API foundation, database models, migrations, and validation |
| Leyan | Fullstack Developer | Saved-history API/UI integration and shared API contract |
| Andrei | Frontend Developer | Chrome extension interface and user-facing states |

## Current Status

The project is in Sprint 1: foundation and walking skeleton.
Application implementation and deployment are not complete.

## Sprint 1 Goals

- Establish the repository and collaboration workflow.
- Create a backlog covering the instructor's requirements.
- Implement and migrate related database tables.
- Connect the frontend to a database-backed API endpoint.
- Run install, lint, and build checks on pull requests.
- Deploy the walking skeleton to a public URL automatically.
- Demonstrate one successful AI inference call through the backend.

## Local Setup

Create a Python virtual environment and install `requirements.txt`. Set a **development**
Neon connection URL as `DATABASE_URL` in `.env`. The backend explicitly loads `.env`; it
does not rely on the shell to load it. Keep `.env` private and out of Git. The application
role needs `CONNECT` on its development database and `USAGE, CREATE` on the `public`
schema so Alembic can apply migrations.

From the repository root on Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Fill DATABASE_URL in .env privately before continuing.
.\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
.\.venv\Scripts\python.exe scripts/seed_demo.py
```

From the repository root on macOS/Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
test -e .env || cp .env.example .env
# Fill DATABASE_URL in .env privately before continuing.
.venv/bin/python -m alembic -c backend/alembic.ini upgrade head
.venv/bin/python scripts/seed_demo.py
```

The seed uses only synthetic data, refuses a database other than `phishlens_dev`,
and is safe to run more than once. Each teammate needs a private `.env` with a
development database URL; Git does not distribute credentials. Schema details and the deletion policy
are in [docs/schema.md](docs/schema.md).

Never commit real credentials or a `.env` file.
Use `.env.example` to document required configuration.

## Project Requirements

Instructor guide: https://csp221a.vercel.app/

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
- Database: MySQL
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

Setup instructions will be added and verified as components
are implemented.

Never commit real credentials or a `.env` file.
Use `.env.example` to document required configuration.

## Project Requirements

Instructor guide: https://csp221a.vercel.app/
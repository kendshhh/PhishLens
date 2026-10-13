# PhishLens

PhishLens is an AI-powered phishing email detection and analysis
system. It helps users identify suspicious emails, understand
risk indicators, and manage saved analysis reports.

## Current Status

The project is in Sprint 1: foundation and walking skeleton.

Application implementation, CI/CD configuration, and public
deployment are not complete.

## Planned Features

- Submit email content for analysis.
- Classify emails as phishing or legitimate.
- Display risk indicators and explanations.
- View saved analysis history.
- Update notes and feedback.
- Delete saved analyses.

## Technology Stack

| Component | Selected Technology |
|---|---|
| Frontend | Chrome extension using HTML, CSS, and JavaScript |
| Backend | Python with FastAPI |
| Database | MySQL |
| AI | DistilBERT running through the backend |
| Version control | Git and GitHub |
| Planned CI/CD | GitHub Actions and automated public deployment |
| Hosting provider | To be finalized |

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

CI/CD is not configured yet.

Sprint 1 must establish:

- Automatic dependency installation, lint, and build checks on every PR.
- Protected main with required checks and teammate review.
- Automatic deployment after successful checks on every merge to main.
- A public walking skeleton connected to the database.
- Pipeline documentation and baseline metrics.

Pull request checkboxes document verification.
They do not replace automated checks or reviewer approval.

## Local Setup

Setup instructions will be added and verified as components
are implemented.

Never commit real credentials or a `.env` file.
Use `.env.example` to document required configuration.

The Chrome extension does not automatically read `.env` files.
Its public backend URL configuration will be documented separately.
Database credentials and backend secrets must remain on the backend.

## Project Requirements

The instructor's guide is the main authority for requirements,
workflow, deliverables, and grading:

[Read the instructor guide](https://csp221a.vercel.app/)
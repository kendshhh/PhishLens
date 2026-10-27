# Scope Changes

## October 21 verification follow-up

The October 13 status below is historical: reviewed migrations, repeated seed,
database-backed history and production readiness now have recorded CI/deployment
evidence. Current main is 149808e; see the
[playbook close-out](devops/playbook-closeout-2026-10-21.md). PostgreSQL/Neon remains
the implementation decision; instructor notification/acceptance is still not
established. Chrome remains the UI, with public extension demonstration acceptance
pending the team/instructor. AI mock wiring is labeled; real model quality/hosting
acceptance and persisted CRUD are not inferred from a working history view.

## 2026-10-13 — Database selection

### Original Plan

MySQL, as declared in the project proposal.

### Updated Decision

PostgreSQL hosted on Neon.

### Reason

The team selected Neon to provide hosted PostgreSQL
for development and public deployment.

### Impact

- Trixia will use PostgreSQL-compatible dependencies and migrations.
- Kendra will configure Neon connection secrets per environment.
- CI database checks will use PostgreSQL rather than MySQL.
- The frontend continues to access data only through FastAPI.

The email-analysis resource, CRUD requirements, and related-table
design remain part of the project.

### Status

- Neon production and development branches created.
- Application connection not tested.
- Migrations not applied.
- Instructor notification pending Consultation 1.

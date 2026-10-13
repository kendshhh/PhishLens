# Scope Changes

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
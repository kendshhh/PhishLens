# Neon Auth staging DevOps preflight — 2026-11-15

## Scope

This is a redacted preflight record from Render control-plane metadata, Neon branch/Auth metadata, and read-only SQL. It is not hosted Auth acceptance. No deployment, environment change, trusted-origin change, account creation, application-report write, or test was run.

## Targets and deployment identity

| Component | Observed state |
| --- | --- |
| Render staging | `phishlens-staging`, `https://phishlens-staging.onrender.com`; auto deploy disabled; configured from `main` |
| Current staging deploy | Render lists `dep-dbsqptmc6qcc739tmnt0` as live at SHA `053d97c7cd984705d5ca20c0e2bc4c06ea7a4bb9` |
| Neon staging | Project `patient-bird-25428852`; branch `pr-58-staging` / `br-delicate-paper-b381z98i`; branch state `ready` |
| Application database | `phishlens_dev` |
| Neon Auth | Provisioned on the staging branch; Auth database `neondb`; base URL `https://ep-soft-fog-b3orfa8a.neonauth.c-4.ap-southeast-1.aws.neon.tech/neondb/auth` |
| Production separation | Neon `production` branch is separate and is the project's default/primary branch |
| Render production API | `phishlens-api`; auto deploy enabled when checks pass; current live SHA `6544364b07c0fcc9fcbc9ee8d405d96d5d1f414c` |

The Render service metadata does not expose its environment-variable values. The connected dashboard view did not resolve to this PhishLens service, so this preflight cannot prove that Render's configured credential maps to the Neon branch/database above. It also cannot verify either service's runtime `REPORT_AUTH_MODE`. Production must be explicitly configured as `demo`; the code default is not evidence of that setting.

## Auth configuration observed on staging

- Trusted origins: none. The expected extension origin is not currently trusted.
- Localhost is allowed.
- Email/password and signup are enabled; email verification is required using OTP.

No Auth settings or trusted origins were changed.

## Runtime database role and baseline

Read-only SQL on `phishlens_dev` connected as `phishlens_staging_app` and observed:

- Database CONNECT and `public` schema USAGE: yes.
- CREATE on database/schema: no.
- SELECT/INSERT/UPDATE/DELETE on `users` and `analyzed_emails`: yes.
- No privileges on `alembic_version`; no TRUNCATE, REFERENCES, or TRIGGER on application tables; no public sequences.
- The runtime role is not a superuser and has no role/database creation, replication, or RLS-bypass flags.
- TEMPORARY is available through the database's inherited PUBLIC privilege.
- The application tables and migration table are owned by `neondb_owner`.

The migration head, read separately as `neondb_owner`, is `0004_neon_auth_subject`.

Pre-run synthetic baseline:

| Check | Count |
| --- | ---: |
| `demo@phishlens.test` user | 1 |
| Demo user with no Neon Auth subject | 1 |
| Reports owned by the demo user | 1 |
| Fixed seed report with the expected synthetic subject | 1 |

These are counts and a fixed synthetic-row match only; report bodies and credentials were not read.

## Startup and rollback notes

[`scripts/start_staging.py`](../../scripts/start_staging.py) applies `alembic upgrade head` using the separate migration credential, then runs the seeder and API with the restricted runtime URL. [`scripts/seed_demo.py`](../../scripts/seed_demo.py) can insert missing synthetic demo rows or correct the fixed report's subject. It refuses to seed if the demo user is linked to Auth or the fixed report belongs to another user.

Keep migration `0004_neon_auth_subject` in place for rollback: its downgrade drops the subject column and unique constraint. A rollback should use the previously approved app revision and explicit demo mode, without downgrading this migration or changing database grants.

## Staging pause and remaining owner gates

Render events record the staging service suspended at `2026-11-15T14:33:22Z` and resumed at `2026-11-15T14:36:37Z` (22:33–22:36 Asia/Shanghai). Several staging deployments also occurred that day. Auto deploy is off, but this does not establish a team-wide pause of manual deployments or other tests.

Still pending before any live Auth run:

1. Kendra confirms credential rotation and, using redacted evidence, verifies the active Render runtime and migration credentials map to this exact Neon branch/database.
2. Kendra verifies explicit `REPORT_AUTH_MODE=demo` in production and records the staging mode; neither value was visible in the available Render session.
3. Kendra and Trixia agree on the exact backend SHA paired with Leyan's final package, the test window, operator availability, and a pause of other staging work.
4. Leyan supplies package source/ZIP hashes and installed-Chrome identity; the expected extension origin remains untrusted until separately reviewed and authorized.

The supplied local commit `0f1650e0ebe5313723a8e81cb06e0ef3fed118c` is not present in the current checkout. The checkout was already dirty and five commits behind its tracked branch; no pull or push was performed.



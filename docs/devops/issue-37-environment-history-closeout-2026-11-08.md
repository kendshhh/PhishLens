# Issue #37 environment and history review — November 8, 2026

This records the remaining `.env.example`, hosted secret-scope, repository
history, and Chrome file-URL permission findings for [issue #37](https://github.com/kendshhh/PhishLens/issues/37).
It records names and control placement only. Secret values and email addresses
were not copied into this file.

## Local environment example

The root `.env.example` now separates local application configuration from
hosted service and GitHub Actions settings. The local variables match the
application readers in `backend/core/config.py` and `backend/app/main.py`:
`DATABASE_URL`, `APP_ENV`, `AI_MODE`, `GEMINI_API_KEY`, `GEMINI_MODEL`, and
`MODEL_PATH`. The staging launcher additionally reads
`STAGING_DATABASE_HOST`, `STAGING_APP_DATABASE_ROLE`, and
`STAGING_MIGRATION_DATABASE_URL`; those remain blank examples and are marked
hosted-only. `DATABASE_URL` is documented as a local/development target.

`.gitignore` excludes `.env` and `.env.*`, with only `.env.example` re-included.
Model caches, private datasets, extension model assets, and local runtime files
are ignored. Render injects `PORT` and `RENDER_GIT_COMMIT`; `PYTHON_VERSION` is
Render build configuration. None are local application inputs.

## Hosted scope review

### Render service settings

On November 8, the Render Environment pages were opened for the PhishLens
production and staging services. Values remained masked; no copy/show controls
were used. Neither page showed a linked environment group or a secret-file
entry. The service-level key names were:

| Service | Environment variable names |
| --- | --- |
| `phishlens-api` (production) | `AI_MODE`, `APP_ENV`, `DATABASE_URL`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `PYTHON_VERSION` |
| `phishlens-staging` | `AI_MODE`, `APP_ENV`, `DATABASE_URL`, `PYTHON_VERSION`, `STAGING_APP_DATABASE_ROLE`, `STAGING_DATABASE_HOST`, `STAGING_MIGRATION_DATABASE_URL` |

The Render connector's service metadata does not return environment-variable
names or values; this name-only check was performed in the Dashboard. It does
not establish the effective permission scope of a Render API key or the
credentials stored inside `DATABASE_URL`, `GEMINI_API_KEY`, or
`STAGING_MIGRATION_DATABASE_URL`.

### GitHub Actions settings

The repository Actions settings show no repository-level secrets. The two
secrets are scoped to environments:

| Environment | Secret | Variables | Deployment controls observed |
| --- | --- | --- | --- |
| `staging` | `RENDER_STAGING_API_KEY` | `SECRETARY_PREVIEW_ENABLED`, `SECRETARY_PRODUCTION_DB_HOST`, `SECRETARY_STAGING_DB_HOST` | Required reviewer `inaki3023`; self-review prevented; no wait timer; administrator bypass off; `main`, `refs/pull/*/merge`, and `refs/pull/33/merge` allowed. |
| `production-observer` | `RENDER_OBSERVER_API_KEY` | None | `main` only; no required reviewer or wait timer; administrator bypass on. |
| `veriqo-staging` | None | None | No branch restriction, reviewer, or wait timer; administrator bypass on. |

The `staging` environment is the one used by the current staging workflows. The
`veriqo-staging` environment has no matching `environment:` reference in the
tracked `.github/workflows` files and no secrets or variables. It is recorded
as an unused leftover; it was not deleted. `xxTrixia` is the issue's backup
reviewer but is not currently configured as a staging environment approver.

There are no repository-level Actions secrets. Repository-level variables are
`RENDER_STAGING_SERVICE_ID` and `STAGING_BASE_URL`; the three
`SECRETARY_*` values above are scoped to `staging`. The settings review did not
reveal secret values. GitHub placement is verified, but the permission scope
inside either Render API key is not visible from the encrypted GitHub entry.

## Repository history

Fetched remote refs on November 8 and scanned objects reachable from the
available refs: `origin/main` was `10df92eb7d78229c8e4f93b10fc718f7752827f4`,
with 160 refs, 3,998 reachable objects, and 1,354 blobs. A bounded pattern
scan found no recognized GitHub, Google API, AWS access-key, or Slack token
shapes. It found no historical `.env` (other than the intentional
`.env.example`) or private model/dataset path. The private-key header marker
appears in historical versions of `scripts/tests/test_secretary.py`, where it
is used by a redaction test; the scan found no key-like payload in that fixture.

Commit author/committer metadata contains personal-provider email identities:
three distinct identities by common-provider-domain heuristic on `origin/main`
and four across all fetched refs. Addresses are intentionally omitted. This
confirms the previously reported personal-email finding. The owner disposition
on November 7 was to preserve existing public attribution and not rewrite or
force-push repository history. That is the accepted project disposition; it
does not remove the privacy finding, and this repository cannot claim clean
history or no personal email identities. This bounded pattern scan is not a
guarantee that all credential formats are absent.

## Chrome file-URL permission

The issue's latest recorded Chrome state is **Allow access to file URLs: ON**.
That state was observed during the November 1 installed-extension check in
Chrome 156.0.8078.79 and carried forward in the November 8 issue update. This
close-out did not re-open Chrome's security-permission page or change the
setting. The ON state is documented, not freshly re-verified in this pass.

## Disposition

The local example and GitHub/Render secret placement review are documented.
The personal-email history finding remains accepted by the owner without a
history rewrite. The Chrome file-URL state remains ON. No hosted secret values,
service configuration, deployment, database, or browser permission were
changed. The owner's November 7 disposition is recorded; reviewer acceptance
and confirmation of the effective external Render key scopes remain open, so
issue #37 stays open.

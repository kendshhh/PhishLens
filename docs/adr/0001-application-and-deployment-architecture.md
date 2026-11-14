# ADR-0001: PhishLens application and deployment architecture

- Status: Implemented; team/instructor sign-off is not evidenced here
- Date: 2026-11-14
- Decision owner: Kendra, DevOps Engineer
- Scope: Sprint 1 architecture and delivery shape

## Context

PhishLens needs a browser interface, backend-owned persistence, relational
storage, AI behavior, and an automated path from reviewed code to a live service.
The course guide expects an architecture choice and diagram, an API/database
boundary, separate environments, and a deployed walking skeleton. The repository
contains a Chrome extension, a FastAPI backend, PostgreSQL migrations, Neon and
Render configuration references, and GitHub Actions delivery workflows.

## Decision

Use a browser extension with local primary inference and one modular FastAPI
service for API operations, server-side provider adapters, and database access.
Store saved analyses in PostgreSQL on Neon. Keep browser code away from direct
database connections and paid-provider credentials. Use GitHub Actions for
pull-request and main checks, protected review before merging, Render for the
backend, and a separate protected exact-SHA workflow for staging verification.

This records the implemented direction. It does not approve a particular hosted
LLM, certify model quality, or claim that Render currently connects to the
intended Neon branch. Those require separate owner and live-environment evidence.

## Alternatives considered

1. **Browser connects directly to PostgreSQL or a model provider.** Rejected:
   it would expose credentials and bypass the API's persistence and validation
   boundary.
2. **Split the API, database, and inference into separately deployed services.**
   Rejected for the current course project: it adds deployment and network
   boundaries without a demonstrated scaling need.
3. **One FastAPI service with a modular browser extension.** Selected: it keeps
   persistence and server-side provider access behind one API while allowing
   the current extension workflow to run local inference.

## Consequences

- Pull requests can validate code without paid provider calls or production
  data.
- Local inference avoids sending scanned email text to a hosted model in the
  current extension workflow.
- The API/database boundary still needs exact-SHA UI-to-API-to-database
  acceptance, including changed-record reads and cleanup.
- Staging and production must use separately verified Neon branches and least-
  privilege database roles. The recorded database name is not a branch identity.
- A server-side hosted provider needs owner-approved provider/model settings,
  provider-side quota or shared durable spend control, and a bounded smoke before
  enablement.
- One backend deployment is operationally simple but still requires a reliable
  post-deploy smoke, recovery targets, and a verified restore procedure.

## Follow-up

See the [Sprint 1–3 DevOps closeout](../devops/kendra-sprint-1-3-status-2026-11-14.md)
for the current acceptance evidence and unresolved decisions.

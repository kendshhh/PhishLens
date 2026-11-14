# PhishLens architecture and environment map

This describes the repository's current implementation as of 2026-11-14. It is
not proof that every hosted service is running this revision. See the
[deployment and acceptance status](devops/kendra-sprint-1-3-status-2026-11-14.md)
for the latest verified limits.

## System boundary

```mermaid
flowchart LR
  subgraph Browser[Chrome browser]
    UI[PhishLens extension UI]
    LOCAL[Local TF-IDF and Llama review path]
    UI --> LOCAL
  end
  UI -->|Explicit saved-report and history requests| API[FastAPI API on Render production]
  API -->|SQL through app role| DB[(Neon production branch)]
  API --> ADAPTER[Server-side provider adapters]
  CI[GitHub Actions PR and main checks] -->|Checked main deploy| API
  STAGE[Protected exact-SHA staging workflow] --> STAGEAPI[FastAPI API on Render staging]
  STAGEAPI --> STAGEDB[(Neon staging branch)]
```

The extension runs its primary review locally. It does not connect directly to
PostgreSQL or send a request to a paid provider. Saving or opening shared report
history is an explicit API operation. The API owns persistence and validates or
recomputes the server-owned classification fields. External provider adapters
remain on the server side; the local extension workflow does not silently fall
back to a hosted model.

The backend is one FastAPI service, not a set of independently deployed
microservices. Neon hosts PostgreSQL. GitHub Actions runs pull-request checks and
main checks; Render auto-deploys checked `main`. The staging workflow deploys and
checks an exact candidate SHA under the protected `staging` environment.

## Environment map

| Environment | App / delivery | Database target | Status and boundary |
| --- | --- | --- | --- |
| Local development | Developer checkout; `.env` is ignored | Dedicated local/development target | `.env.example` documents app configuration without real values. Do not use hosted staging or production credentials locally. |
| Staging | Render staging service; GitHub `staging` environment gates hosted workflow | Neon `pr-58-staging` branch is the documented target | The Render-to-Neon mapping must be checked against the current masked service configuration before hosted writes. Historical `/ready` success alone does not establish branch identity. |
| Production | Render API; checked `main` auto-deploy | Neon `production` branch; production database name is `phishlens_dev` in the current read-only inventory | The live Render `DATABASE_URL` mapping was not freshly compared with Neon during this closeout. Verify target before writes or promotion. |

The database name `phishlens_dev` is used on more than one branch. A database
name or healthy readiness response does not uniquely identify a Neon branch.
Keep the target mapping in the host configuration and validate its branch/host
using an authorized read-only check before running a write workflow.

## Delivery path

```mermaid
flowchart LR
  BR[Task branch] --> PR[Pull request]
  PR --> CHECKS[Required CI and dependency checks]
  CHECKS --> REVIEW[Required teammate approval]
  REVIEW --> MAIN[main]
  MAIN --> MAINCI[Main CI]
  MAINCI --> DEPLOY[Render auto-deploy]
  DEPLOY --> MANUAL[Current exact-SHA observer / smoke]
```

There is no verified production deployment-ended event or owner-approved
deployment hook for an automatic changed-feature smoke. The last-mile smoke is
therefore tracked separately and is not drawn as an automatic stage. See
[PIPELINE.md](../PIPELINE.md) and the Sprint 1–3 closeout.

## Architecture decision

The recorded decision is [ADR-0001](adr/0001-application-and-deployment-architecture.md).
It records the current implementation choice; it does not assert team or
instructor sign-off that is absent from the source record.

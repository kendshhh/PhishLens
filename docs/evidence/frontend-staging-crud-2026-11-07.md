# Live staging frontend CRUD — November 7, 2026

**Result: passed; synthetic record cleanup confirmed.**

The user explicitly authorized a real staging CRUD test. The local staging
development extension ran in disposable Chromium against the real hosted API.
No production endpoint, deployment configuration, migration, or unrelated record
was changed. This is connected frontend/API evidence, not release approval.

## Identified target and client

| Item | Observed value |
| --- | --- |
| Run time | November 7, 2026, 22:24–22:25 Asia/Manila (14:24–14:25 UTC) |
| API | `https://phishlens-staging.onrender.com` |
| `/version` environment | `staging` |
| Backend revision | `0fcc747725512df13ba8ae0900b6080591425928` |
| Frontend base commit | `9f5a1ff2b1c5a9624cb22f6ecf08f9e082ad9054`, with local uncommitted UI edits |
| Tested controller SHA-256 | `ecc12360b80db0d18fa180ff03472fb664a3d997197ba0e9b4637e02057632ee` |
| Browser | Playwright Chromium `156.0.8078.4` |
| Model identity | `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c` |
| Saved analysis mode/provider | `real` / `tfidf` |
| Local review status | `uncertain`; reported judge code `local_judge_failed` |
| Synthetic record ID | `506d5917-8a3d-4a73-a942-f0a2c76fe37b` |
| Final cleanup | DELETE confirmed, detail 404, absent from API list and reopened popup |

Before any write, the existing `verifyTarget` guard checked the approved staging
origin, exact backend SHA, environment and database readiness. Model capability
and identity matched the extension. Browser write interception checked identity
again and restricted POST to this run's unique synthetic subject/body and
PATCH/DELETE to its returned UUID. Only one POST was permitted in the passing
run. Other requests used redirects disabled.

The repository runbook identifies the isolated staging database as Neon
`pr-58-staging/phishlens_dev`. Private hosted connection settings and current
runtime grants were not independently audited in this test; no new least-privilege
or production-isolation audit result is asserted.

## Expected and observed journey

| Step | Observed result |
| --- | --- |
| Analyze synthetic pasted text locally | Original text retained; uncertain assessment shown |
| Save with explicit consent | POST `/api/analyses` returned 201; repeat save disabled |
| Read own detail and list through fresh client | Returned ID, subject, body and assessment matched |
| Close and reopen popup | Saved marker and report detail restored |
| Edit notes and optional opinion | PATCH returned 200; notes and feedback matched |
| Close/reopen and read again | Edited values persisted; assessment/provenance unchanged |
| Delete through the confirmation UI | DELETE returned 204 |
| Verify deletion independently | Detail returned 404 and list omitted the ID |
| Close/reopen popup and search unique title | No matching report remained |

The passing run used the frontend's actual API client and original local-review
payload. No response fixtures or mocked live API responses were used. The backend
replayed its TF-IDF checks when saving; this does not establish successful full
local-LLM review or AI accuracy. Native right-click interaction, backend redeploy
persistence, authentication/user isolation and production acceptance remain separate.

## Earlier attempt

The first attempt created and reread synthetic record
`7a2f3c9b-d87d-4dbd-abce-5e38660c0501`. Its test asserted the reopened heading
before the asynchronous detail fetch completed. The harness wait was corrected;
that first record was confirmed deleted before the passing run. It is not
reported as a frontend failure or a successful complete CRUD run.

## Local evidence

Passing run artifacts are under
`output/live-staging-crud-56780622-a222-4bbf-8fc7-2a8cd878acc7/`:

- `result.json`: step timestamps, write methods/paths, identity and cleanup result.
- `01-created-report.png`, `02-reopened-edit.png`,
  `03-deleted-after-reopen.png`: screenshots limited to the synthetic test report.

The earlier attempt's journal is under
`output/live-staging-crud-2daca13c-e403-4fb4-85e7-dd08c9bbb445/`.
These output artifacts are local and ignored by Git. The journal retains the
synthetic request's idempotency information for recovery and has not been posted
to a PR. No human browser sign-off, current-head CI result or merge is claimed.

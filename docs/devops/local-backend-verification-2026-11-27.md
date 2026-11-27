# Local backend verification for the November 30 demo

Results recorded November 27, 2026, Manila. The browser and database checks used
synthetic data on the rehearsal Mac. The course's production walkthrough
requirement needs its own release and verification evidence.

## Approved local demo candidate

| Pin | Value |
| --- | --- |
| Application commit | `6056419bae22507a4dd922feb19185e5d7c97d9a` |
| Chrome ZIP SHA-256 | `e6eb1f9cb0872ba9dec773ebe1f852bf1eec776f958b3ea26533ca8735992930` |
| Model | `word_plus_char_wb_context_v1` |
| Model SHA-256 | `adace5ad3cfb281a15b7bc85774ef158126800dc3f78c942f46547dfde33dc27` |

- The approved ZIP ran in an isolated Chrome profile with synthetic
  authentication, the pinned FastAPI backend, and disposable local PostgreSQL.
  Sign-up, fresh sign-in, all three on-device verdicts, explicit save, reopen
  after refresh, persistent note edits, account isolation, and delete passed.
  Scanning alone created zero reports. The database contained zero reports
  after cleanup and before shutdown.
- The pinned backend passed 54 focused tests. PostgreSQL reached Alembic head
  `0005_ai_request_quota`. Its catalog confirmed the report owner foreign key
  with `ON DELETE CASCADE`. The failure drill returned
  `503 analysis_unavailable` when the provider configuration was missing.
  Blank input returned `422`.
- The [schema guide](../schema.md) explains the one-to-many relationship and
  the separation between account ownership and quota storage. The fresh local
  schema had RLS disabled. Report ownership checks run in the API.

## Guardrail evidence

The local review uses the browser's judge, while the backend validates
submitted review evidence and replays the classifier checks before persistence.
The pinned demo source includes input limits, redacted provider errors, and
the quota table migration. It also includes Gemini per-request token and cost
bounds for that provider.

Separately, the `main` snapshot at
`88156d479d19eb0b8018ab76aa3170eb60079765` passed 53 focused quota and provider
tests using fixtures. That snapshot also has shared Gemini per-IP and per-user
request quotas, a daily spend reservation, and a structured threshold event.
Hosted quota configuration, alert delivery, and a team-approved service-level
objective still need evidence.

## Hosted status

The hosted rehearsal for the pinned #293 ZIP was deferred. Hosted sign-up,
sign-in, and saved-report CRUD remained unverified for this build. A future
hosted check needs the approved staging window, protected deployment, matching
application and model pins, and synthetic report and account cleanup.
Production promotion and holdout scoring remained on hold.

[Candidate PR](https://github.com/kendshhh/PhishLens/pull/293)

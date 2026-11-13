# Backend Auth acceptance and cleanup procedure

Preparation only. This document and its examples are not authorization to run
anything against staging. They do not select a deployment or change Auth config.
The two-account Auth run is separate from #48's one-report TF-IDF lifecycle.

Local verification during preparation: the helper guard and simulated-flow
tests, extension regression suite, lint and JavaScript syntax checks passed,
and the gated SQL regression passed on disposable localhost PostgreSQL.
No live Neon, installed-Chrome, provider, or hosted acceptance is claimed.
The reproducible SQL test requires a migrated disposable loopback
`phishlens_dev` and explicit opt-in, for example in a POSIX shell:

```sh
DATABASE_URL=postgresql+psycopg://127.0.0.1:55496/phishlens_dev RUN_AUTH_CLEANUP_TESTS=1 python -m pytest backend/tests/test_auth_acceptance_cleanup.py -q -p no:cacheprovider
```

On PowerShell set those two environment variables with `$env:NAME='value'`, then
run the same `python -m pytest ...` command. Never point this test at a hosted
database. It creates and deletes only its own uniquely identified local fixtures.

## Freeze the private run record

Copy `docs/auth-acceptance-plan.example.json` outside the repository. Complete
that private copy with the final operator-approved values; never fill the tracked
template with identities or credentials. Use Node 20+ for the HTTP helper and
psql for the separately authorized mapping cleanup. Both work on macOS/Windows.

Generate one run UUID (`node -e "console.log(crypto.randomUUID())"`) and retain it.
Record the full backend SHA, package source SHA and ZIP hash, installed extension
ID, exact trusted origin, Chrome version, operator names, UTC+08:00 test window,
actual authorization reference, credential-rotation confirmation and baseline
evidence. Do not infer a matching package merely from similar names or timestamps.
Set `window_start` and `window_end` to the approved ISO timestamps with `+08:00`.
The helper blocks execution outside that window. Cleanup that needs extra time
requires an explicit extension of its approval; do not silently extend the plan.

The proposed target is shared staging, not a PR-specific branch:

| Component | Proposed identity; reverify before approval |
| --- | --- |
| Backend | `https://phishlens-staging.onrender.com` |
| Neon project | `patient-bird-25428852` |
| Shared branch | `br-delicate-paper-b381z98i` (`pr-58-staging`) |
| Application database | `phishlens_dev` |
| Auth database | `neondb` |
| Auth base URL | `https://ep-soft-fog-b3orfa8a.neonauth.c-4.ap-southeast-1.aws.neon.tech/neondb/auth` |
| Expected model | TF-IDF SHA in the example plan; reverify `/model-info` |

Kendra must verify the Render credential hostname actually identifies that
branch/database, separately from `/ready`. Record exact runtime auth mode,
issuer/audience/JWKS, migration head, grants, deployment/config operator, Auth
administrator, pre-run SHA/config/trusted-origin state and rollback procedure.
Pause other staging testers. Deployment/startup runs migrations and seeding;
include those effects in any deployment authorization and compare seed/migration
baselines afterward. A subject-reconciling seeder may update an existing row.

The helper validates public SHA/readiness/model/auth-denial checks; it cannot
prove the Neon mapping, inspect Render variables or verify rotation. The plan's
confirmation references record the operator's prior checks, not automated proof.

## Identity and write limits

Use exactly the two approved disposable Auth accounts and private inboxes.
Record each immutable Auth subject and its internal application-user UUID in the
private plan. Obtain fresh JWTs via the approved client/session procedure into
private token files (not command-line arguments, source files or screenshots).
The helper checks the token's subject only to prevent choosing the wrong account;
the backend remains responsible for signature/issuer/audience/expiry validation.

Authenticated GETs can create application mappings on first access. Approval
must either include those two mapping inserts (`allow_mapping_creation`) or
confirm both exact mappings already exist (`application_mappings_preverified`).
Never claim mappings by matching email. The live run also creates provider OTP
and session records; approval and Auth-admin cleanup must cover them.

Current proposed bound: **two Auth accounts, two reports total, one per owner**.
Both accounts use the same run-specific idempotency key. Permit one identical A
replay, one changed-payload A conflict, and one cross-account read. PATCH is off
by default: enable `include_updates` only if the final authorization includes one
notes/feedback update per report. One optional OTP resend is a client/admin
operation, outside the helper. No forced timeout or interrupted commit is included.

## Dry-run and per-step execution

With the private plan filled in, this prints a request and performs **no I/O to
the target**, token read, database operation or evidence write:

```sh
node scripts/auth_acceptance_step.mjs /absolute/private/auth-plan.json create-a
```

Only after specific approval, adding **both** flags executes that one step:

```sh
node scripts/auth_acceptance_step.mjs /absolute/private/auth-plan.json create-a --execute --allow-writes
```

Use an absolute private `evidence_directory` outside the repository. The helper
records the request/key before its account request, then a private JSON receipt
with the response. It prints only a short result. Protect the directory with OS
permissions (mode 0700/0600 is requested on POSIX; use a private ACL on Windows).
Do not share raw receipts: an isolation failure could expose unexpected content.

Read each receipt before proceeding. After each successful initial create,
copy its exact `response.body.id` into that owner's `report_id` in the private
plan. Record its internal user UUID through the authorized mapping preview; the
API intentionally does not accept or expose browser-supplied ownership.

Each step has a unique receipt and cannot be executed again in the same evidence
directory. Do not erase receipts/change run IDs to bypass that guard. There are
no automatic HTTP retries. Re-read token files between steps if an approved
session renewal supplies a replacement token for the same subject.

| Order / helper step | Request | Expected result |
| --- | --- | --- |
| Every execution, before any token use | GET `/version`, `/ready`, `/model-info`; anonymous GET `/api/analyses` | SHA/environment, readiness and model match; anonymous list **401** |
| `list-a-before`, `list-b-before` | Authenticated GET `/api/analyses` | **200**, empty histories for these new accounts; may create mappings |
| `create-a` | POST `/api/analyses`, synthetic A subject/body, run key and model header | **201**, record A; TF-IDF model provenance matches |
| `read-a`, `list-a` | GET A detail/history as A | **200**, A's record only; reread subject/body/prediction/provenance match create |
| `replay-a`, `list-a-replay` | Same POST body and key as A; reread history | **201**, same ID; **200**, one record; do not create a new key |
| `conflict-a`, `list-a-conflict` | Same key, changed body; reread history | **409** `idempotency_conflict`; **200**, no extra report |
| `create-b`, `read-b`, `list-b` | B initial POST uses the same key; GET B detail/history | **201/200**, different ID; B sees only B's report |
| `cross-read`, `read-a-after-cross` | B's token, GET A's report; A's token reread | **404**, then **200**; A's report remains readable by A |
| Optional `patch-a`, `patch-b`, `read-a-after-patch`, `read-b-after-patch` | PATCH own report with synthetic notes/feedback, then reread | **200**; compare prediction/body/provenance/ID unchanged |
| `delete-a`, `delete-b` | DELETE each report as its owner | **204** |
| `missing-a`, `missing-b` | GET deleted detail as owner | **404** |
| `list-a-after`, `list-b-after` | GET each owner's history | **200**, empty |

The helper validates the status, model provenance on create/replay, same/different
IDs, expected history IDs, conflict code and basic read/PATCH identity. The
operator compares the private before/after fields and records pass/fail. Do not
repeat a blocked helper step by deleting its receipt. Extra requests must fit
the agreed scope. Signup, real email/OTP, browser cookie/session restoration, renewal,
expiry, sign-out and UI account switching remain Leyan's installed-Chrome checks.

The broader checklist also expects anonymous/expired denial on all five CRUD
operations, unverified-account denial (403 where a JWT exists), cross-user
PATCH/DELETE denial, and demo separation. Those negative requests are **not**
implicitly part of this smaller approved two-report scope. Agree on their exact
requests separately, using only this run's recorded IDs; never test destructive
denial against seed or unrelated rows. CI results are not live passes for omitted
cases. Keep omitted live criteria explicitly pending.

## Stop and reconcile

Stop on any mismatched target/SHA/model/origin, wrong subject, non-401 anonymous
list, unexpected status/content, wrong report visibility, existing history,
missing/changed mapping, token expiry, another deployment/tester or incomplete
receipt. Do not change runtime mode, create extra accounts or retry a POST blindly.
If a create acknowledgement is lost, the private receipt retains the exact body
and key. Mark the result uncertain and have the operator inspect database state
by the recorded subject/key. Reconcile the committed ID and record it before
authorizing any replay or cleanup. Do not issue a new key. Do not rerun the full
scenario. No automatic cleanup on failure is attempted.

## Cleanup: report owners, Auth admin, then application operator

1. Under each owner, delete only this run's recorded report IDs. Require 204,
   detail 404 and absence from history. Resolve any uncertain create first.
2. Sign out/stop both clients and all acceptance requests. The named Auth admin
   revokes sessions and removes only the two approved synthetic Auth accounts
   through the supported administrative flow, recording provider cleanup results.
   Do not delete provider tables ad hoc. An issued JWT may remain valid until its
   expiry; session revocation alone is not proof of immediate backend rejection.
   Keep clients stopped and account for outstanding token expiry before final
   mapping verification so old tokens cannot recreate mappings.
3. Record the exact two subject-to-UUID mappings privately. Use an approved
   direct staging connection for the SQL scripts, whose read-only/default guards
   do not independently establish Neon branch identity. A private libpq service
   file can supply connection credentials without putting them in shell history.
   Have Kendra verify its hostname/branch/database and operator privileges first.
   SQL guards require the previously identified direct staging hostname
   `ep-soft-fog-b3orfa8a.c-4.ap-southeast-1.aws.neon.tech` and `phishlens_dev`;
   a hostname change requires review, not bypassing the guard. Loopback is
   accepted only with `allow_disposable=true` for local tests. A hostname guard
   does not replace Kendra's live branch-mapping verification.
4. Create a private psql variables file with only the following values:

```text
\set account_a_subject 'CONFIRMED_A_SUBJECT'
\set account_a_user_id 'CONFIRMED_A_INTERNAL_UUID'
\set account_b_subject 'CONFIRMED_B_SUBJECT'
\set account_b_user_id 'CONFIRMED_B_INTERNAL_UUID'
```

Run the **read-only preview**, saving its output privately:

```sh
psql "service=phishlens_staging_cleanup" -X --file=/absolute/private/auth-identities.psql --file=scripts/auth_cleanup_preview.sql
```

Expect two exact mappings, neither the demo identity, and zero remaining report
rows. If an account still has a report, inspect its ID; do not use cascade deletion
to hide an unknown report or delete anything outside this run.

5. Only after separate cleanup authorization and a successful preview, execute:

```sh
psql "service=phishlens_staging_cleanup" -X --set=authorize_cleanup=true --file=/absolute/private/auth-identities.psql --file=scripts/auth_cleanup_apply.sql
```

The apply transaction locks both exact subject/UUID mappings, requires two
distinct non-demo users and zero dependent reports, then deletes only those two
users. A mismatch, missing mapping, lock timeout or remaining report aborts the
transaction. It commits on success; the flag records operator intent and is not
permission by itself. No schema/migration/seed changes are made by these scripts.

6. Repeat the read-only preview: both `exact_mapping_found` values must be false.
   Confirm the Auth-admin results and unchanged seed baseline. Do not perform
   more authenticated API probes after deleting mappings: they can recreate them.
   Record any unresolved ID; cleanup is incomplete until all are reconciled.

## Evidence and acceptance

Keep the private plan, request receipts, exact subjects/UUIDs/report IDs/keys,
token expiry times, mapping previews, actual operators/times and cleanup results
outside Git. Share only redacted alias/method/status/pass-fail summaries,
source/model/package identities and evidence references. Never share token
files, OTPs, cookies, passwords, DSNs, raw HAR, email addresses or raw bodies.

Use a summary row per step: `time | operator | account alias | request/check |
expected | observed | pass/fail | private evidence reference | cleanup status`.
Copy `docs/auth-acceptance-evidence.example.csv` for that redacted summary; keep
private receipts and account identities separate from anything shared on GitHub.
Wilberr reviews backend evidence; Leyan supplies the Chrome results. Trixia records
only checks actually executed on the pinned target and lists omissions/failures.
Rollback configuration/deployment/trusted-origin changes needs its named operator
and agreed authorization. No automatic deploy, migration downgrade, branch reset,
seed repair or bulk deletion is part of this procedure.

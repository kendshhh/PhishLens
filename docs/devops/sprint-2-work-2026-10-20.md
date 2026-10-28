# Kendra's Sprint 2 work — October 20, 2026

Assigned open issues verified through GitHub: #36–#41. Code baseline is current
main `c350131f51340bd01ba9f8719a40c44fb8838d4a`; the user's original checkout is
older and has unfinished changes. Implementation is isolated in
`tmp/sprint2-devops/` and branch `ci/38-backend-evidence-gate`.

## Work order and actual status

| Issue | Work now | Integration/completion dependency |
|---|---|---|
| #36 carryover/contract | Sprint goal, ownership and issue mapping exist in docs/sprint-2.md; interface audit below | Owners acknowledge actual API/client/AI choices; consultation time and scope acceptance remain unconfirmed |
| #38 CI | Draft PR #52 adds disposable-target preflight, mandatory passing DB test IDs, JUnit/JSON evidence and regression tests | GitHub PostgreSQL execution, reviewed #42/#43 CRUD tests, remote failure/repair and teammate review |
| #37 environment/package | Current-main validator and package creation rerun successfully; browser evidence retained separately | Private staging/production DB mapping, scoped-secret/history audit and full runtime/state evidence remain open |
| #39 delivery | Existing exact-main automatic production evidence retained | Backend CRUD merge and approved demo-target persistent CRUD verification; no write performed |
| #40 metrics/recovery | Retain existing metrics with their measurement definitions and historical recovery limits | Equivalent before/after run samples; no optimization gain claimed |
| #41 consultation | Requirements mapping, gap inventory and actual browser evidence available | Actual standups/retro, integrated demo, whole-team rehearsal and instructor feedback |

## Goal, roles and carryover (#36)

Sprint goal: persistent create/list/detail/update notes-feedback/delete through
the extension and PostgreSQL, actual database API tests in CI, and reviewed-main
automatic deployment. Consultation target is October 22, time unconfirmed; this is
the team's planning date. Kendra's product-owner duty remains proposed.

Owners: Kendra delivery/DevOps; Trixia backend/schema (#42/#43); Leyan client/HTTP
acceptance (#44/#45); Andrei UI/browser (#46/#47); Wilberr AI contracts/evidence
(#48/#49). Existing schema/history/AI adapter/CI/staging/package work is reused.
Fresh production-package rendering/reopen/reload was user-confirmed in Chrome
155.0.8059.85, extension 0.1.0, production `/version` c350131. Other browser states,
changed-record verification and requested contract reviews remain carryover.

## Shared interface audit: implemented versus proposed

| Boundary | Current main | Sprint 2 proposal / integration decision needed |
|---|---|---|
| Saved history | GET /api/analyses returns {items: [...]} for the server-selected synthetic demo account | Preserve envelope and trusted server ownership; add persistent CRUD under /api/analyses |
| Analysis | POST /analyses accepts text up to 30,000 chars; subject/sender up to 320; returns assessment without saving | New saved-create takes subject/body and returns 201 detail; do not silently replace the existing endpoint contract |
| Validation/errors | Current analysis has controlled failure handling; PR #50 introduces error.message responses | Proposed CRUD uses 422 invalid input and controlled 503 detail; client must explicitly support each actual error envelope |
| Verdicts | AI supports legitimate/spam/phishing; stored history uses phishing/legitimate or null | Decide how spam is persisted/serialized; PR #35/#51 client validation rejects spam; do not silently discard it |
| Provenance | Live analysis mode is mock/gemini/local with explanation_source and optional metadata | Proposed stored analysis_mode mock/real plus legacy null/unknown requires migration and an explicit adapter mapping |
| Input limits | Existing live-analysis limits above | Proposed saved CRUD subject 1–250/body 20,000/notes 2,000 are team defaults; backend owner records adopted values |
| Client methods | Existing getAnalyses plus unmerged #51 five-method client | list/get/create/update/delete; mocked/in-memory HTTP verification does not prove real PostgreSQL API integration |

Proposed CRUD example: POST /api/analyses with
`{"subject":"Synthetic review","body":"Synthetic test email."}` returns 201
with a UUID detail record. PATCH its ID with `{"notes":"Reviewed"}` returns 200;
omitted fields remain unchanged. DELETE returns 204 without JSON; later detail is
404. Empty PATCH, client-owned verdict/user_id fields and invalid values must fail.
These are proposed acceptance examples, not claims of deployed endpoints.

Top integration risk: independently developed API, client and AI shapes disagree,
especially spam labels, provenance and errors. Mitigation: Trixia records actual
serializer/schema examples, Leyan verifies against that real HTTP API, Andrei uses
that same client, and Kendra registers the resulting real database tests in CI.
Owner acknowledgement is pending; unrelated work can proceed.

## Environment and evidence boundary (#37/#39)

Local/CI uses explicit localhost disposable PostgreSQL; no cloud fallback.
Staging: https://phishlens-staging.onrender.com, protected `staging` environment,
`RENDER_STAGING_API_KEY` secret and `STAGING_BASE_URL` /
`RENDER_STAGING_SERVICE_ID` variables. Runtime `DATABASE_URL` must target the
privately verified development branch. Production:
https://phishlens-api-ocvt.onrender.com, runtime `DATABASE_URL`, automatic main
deployment after checks. Distinct URLs do not prove distinct database branches.
No credential values, real inbox content or model weights are added here.

## Verification performed

- All 50 deployment-script tests passed, including five new CI gate tests.
- Ruff passed for scripts/ci_backend.py and scripts/tests/test_ci_backend.py.
- Backend: 70 passed, two database tests skipped locally because no PostgreSQL
  server was provisioned. Initial Windows temp access error resolved on permitted rerun.
- Current-main extension asset validation and package creation passed; root
  manifest and test-file exclusion checked. This is separate from installed Chrome.
- Remote CI and review status are recorded in [PR #52](https://github.com/kendshhh/PhishLens/pull/52).

Initial remote gate verification: [run 39420500056](https://github.com/kendshhh/PhishLens/actions/runs/39420500056),
PR head `8ef5e75bf580ca775e922f6b25952c7bce9591c5`, Backend checks passed:
72 tests, zero skipped, both required real PostgreSQL tests passed. Artifact
`Backend-Test-Evidence` ID 12262598646 was published. Its `commit` identifies the
generated tested merge revision; the follow-up adds explicit source-head metadata.
Intentional draft-only missing-test drill
[39420764116](https://github.com/kendshhh/PhishLens/actions/runs/39420764116)
failed as intended: all 72 backend tests passed, but the new evidence gate rejected
the nonexistent required test and exited 1. Dependent integration/hosted jobs were
skipped. Repair removes the drill requirement; latest-head checks remain required.

## Consultation and remaining sprints (#41)

docs/sprint-2.md maps API CRUD, related tables, UI/client CRUD, API tests in CI,
environment separation and automatic deployment to owners. It also retains
process/metrics requirements. Sprint 3 retains real AI integration/capacity and
held-out evaluation; Sprint 4 retains hardening, complete docs, release/tag,
changelog, public demonstration, rollback and metrics trends. Do not convert
planning or administrative closure into verified instructor acceptance.

Actual standups, retrospective and rehearsal have not occurred in this work
record. Preserve actual done/next/blocked updates when supplied; do not generate
team feedback. No issue is closed by this independent implementation.

# DevOps acceptance — October 21, 2026

Scope: verified Week 2 independent-work playbook, Kendra page 3 and individual
DevOps criteria. Final-project release/AI-evaluation work remains on the later
sprint backlog. Component readiness, integration and delivered acceptance are
different states; no whole issue is closed by this record.

| Responsibility | Implemented / retained evidence | Remaining acceptance |
|---|---|---|
| #36 priorities and shared interfaces | Sprint/ownership map and actual-versus-proposed contract audit | Component owners acknowledge adopted contracts; no invented agreement |
| #37 package/environment | Strict production hosts, source/tested SHA and file/ZIP evidence in #55; follow-up verifier before artifact upload | Latest-head CI, installed Chrome; private role/secret scope and complete config audit |
| #38 disposable database CI | #52 merged; explicit localhost target, migrations/repeated seed, mandatory real DB test evidence | Register actual CRUD test IDs once reviewed backend tests land |
| #39 automatic delivery | Existing main 149808e → CI 39449001340 → observer 39449283551 → Render/live identity record in #55 | New reviewed merge and current live identity; persistent CRUD on confirmed synthetic demo target after backend/UI integration |
| #40 measurement/recovery | Raw n=2 before/after cache observations, one 184.294784-second delivery sample, historical rollback and schema-aware recovery procedure | No established whole-job speedup; meaningful comparable optimization remains open; comprehensive deploy/recovery measurements unknown |
| #41 consultation/process | Consultation agenda, evidence and owner map | Actual standups/retro/rehearsal and instructor feedback must come from participants |

## Follow-up implementation

The package verifier requires full source/tested revisions, clean known inputs,
the exact approved runtime inventory, ZIP/per-file hashes, Manifest V3/version,
production-only host permissions and no optional host grants. The sidecar cannot
expand the inventory. Invalid ZIPs fail cleanly. Evidence is unsigned; retrieve
the pair from the trusted Actions run. It does not establish Chrome acceptance.

The workflow addition runs after package creation and before upload. Existing
test discovery exercises its 15 regressions without changing required check
names, deployment settings or approvals. Before this follow-up, all three
automatic jobs passed for #55 head 18c60d3; Hosted staging remained pending.
Those results cannot certify the new follow-up commit.

Local validation: 65 tests passed across the original local deployment-script
suite and 15 new verifier tests; changed-file Ruff passed. Local checkout is older
than #55 and has unrelated work, so this count is not the remote suite count.
The initial Windows temporary-directory permission failures were resolved by
setting Python's tempfile.tempdir to the permitted project tmp directory; no
application/test assertions were relaxed. Local Git status access was denied.
The follow-up builds on #55's remote head, preserving its existing changes.

## Gates and next owners

1. GitHub CI must pass on the new head. The authorized staging environment
   reviewer handles approval; retain shared-service serialization.
2. Kendra/Andrei verify the current exact staging SHA and matching package in
   installed Chrome. Record browser version, actions and expected/actual output.
3. Obtain formal teammate review; review requests and bot recommendations do not
   constitute approval. No merge is performed by this continuation.
4. Main-protection API returned HTTP 403 (integration access denied). The owner
   verifies enforced checks/review/settings through the repository settings UI;
   a readable CI run is insufficient evidence of enforcement.
5. Trixia supplies reviewed persistent CRUD/schema tests; Leyan/Andrei supply real
   client/UI integration. Kendra wires their actual tests and delivery smoke.
   Keep routine provider calls mocked and verify the target before hosted writes.
6. The private environment owner verifies Neon branch identity, least privilege
   and secret scope without copying connection values into evidence.

## Later-sprint DevOps backlog

- AI evaluation on prompt/model/preprocessing changes with Wilberr; guarded,
  capped real smoke appropriate to the selected provider/local model. Ordinary
  deployment checks must remain independent of a provider outage.
- Comparable improvements and weekly metrics with sample sizes, queue/approval
  time distinguished from execution, actual failures and recovery evidence.
- Reviewed release/tag/changelog and known-good schema-compatible recovery;
  whole-team rehearsal of the commit-to-production path and release demonstration.

The DevOps implementation can be independently reviewable while these external
gates remain open. Do not label all DevOps responsibilities delivered until the
corresponding acceptance evidence exists.

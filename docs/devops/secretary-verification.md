# Secretary verification and rollout log

## Local checks actually performed

Final offline suite: **36 tests passed**, comprising 31 secretary tests and
five existing deployment-guard tests. Backend suite: **70 passed, 2 skipped**;
the skips require isolated PostgreSQL. An initial sandbox run had a Windows
temporary-directory permission error; the complete rerun outside that sandbox
passed. Extension suite: **18 passed**. Configured extension lint and Ruff on
secretary/backend changed code passed. No provider credentials or live AI calls
were used by these tests.

`python -m scripts.secretary.demo` creates the example report and actual demo ZIP.
The ZIP is made from local source with a staging banner and zero SHA; it has not
been deployed and must not be presented as acceptance evidence. Final check counts
may grow as regression coverage is added; use the PR's latest run for acceptance.

| Required scenario | Evidence actually exercised | Live acceptance still needed |
|---|---|---|
| Passing PR | Pure policy says ready for human review, never approval | Bot comment and full CI on installed workflow |
| Failed check | Failure/cancelled/skipped/timeout produce changes recommended | Intentional synthetic CI failure/repaired rerun |
| Pending or missing | Explicit waiting | Running UI transitions and missing-required-check case |
| Draft | Blocked; preview not approved | Open draft then mark ready |
| New commit | Old preview rejected; stale report not posted | Push correction and inspect replaced report/build SHA |
| CI rerun | Latest attempt is selected | Rerun on GitHub and inspect current evidence |
| Duplicate events | No new comment/AI call for same fingerprint | Event delivery on installed bot |
| Agent/provider failure | Provider failure gives unavailable; report API boundary has failure fallback | Revoke test key/access safely; verify ordinary CI remains usable |
| Invalid AI JSON | Invalid objects/types/oversized summary rejected | Optional provider integration, if enabled |
| Oversized/binary diff | Coverage gap and blocked recommendation | Real large test PR without private data |
| Fork PR | Explicit action required, no preview authorization | Fork CI permission behavior and trusted-branch handoff |
| Preview failure | Failed preview blocks recommendation; controller fails check | Controlled invalid staging start on disposable data |
| Shared staging conflict | Newer SHA invalidates report and old staging check | Two PRs queue; confirm serialized runs and re-test request |
| Production failure | Deduplicated failed-deploy metric; incident boundary implemented | Controlled drill approved by human; do not break production casually |
| Database isolation | Wrong production host/service rejected | Private Neon host/role and Render env inspection |
| Extension package | Real local assets have SHA/banner/staging-only permission and valid ZIP | Install freshly generated CI artifact in Chrome |

An offline state-machine test is not a real deployment. There are no fabricated
screenshots, automatic approvals, or production rollback claims in this log.

## Rollout acceptance checklist — owner records links

- [ ] Review source and trust boundaries with a teammate.
- [ ] Create protected `staging` and `production-observer` environments.
- [ ] Move/rotate the repository deployment secret into staging; remove the old repository secret.
- [ ] Privately verify the `pr-58-staging` Neon host, staging-only role, and mock-only staging config.
- [ ] Let the trusted legacy bootstrap run verify the pilot PR before merge; retain existing protection.
- [ ] Human approval and authorized merge install trusted workflows on main.
- [ ] Set preview enabled and run the first exact-SHA test PR.
- [ ] Confirm one bot-owned report and no duplicated comment after a rerun.
- [ ] Open `/version` and the fresh artifact; perform and record manual Chrome tests.
- [ ] Owner requires `Secretary staging` after its first observed check, alongside existing checks.
- [ ] Set repository variable `SECRETARY_REPLACES_LEGACY_STAGING=true` only after the new check is required and proven.
- [ ] Retire the legacy bootstrap job in a separate reviewed PR; no direct protection bypass.
- [ ] Verify main auto-deploy and the exact merged SHA in Render.
- [ ] After Render shows that SHA live, manually run **Production evidence** from
  GitHub Actions on `main`; retain the artifact and confirm `/version`, `/health`
  and `/ready` match the live deployment.
- [ ] Download metrics before artifact expiry, record the reporting period and sources.
- [ ] Perform an authorized rollback drill later, checking database compatibility first.

The production observer is deliberately `workflow_dispatch`-only. A `workflow_run`
trigger would create a separate GitHub check on the same main commit while the
observer waits for Render to deploy it. With Render set to **After CI Checks Pass**,
that check can prevent the deployment it is waiting to verify. Run the observer only
after the expected commit is live; it is evidence collection, not a deployment gate.

## Consultation demonstration (about 3 minutes of DevOps segment)

1. **Before the meeting:** wake the free staging and production services; open the
   PR, Actions, staging `/docs` and `/version`, Chrome test profile, metrics and
   [pipeline guide](../../PIPELINE.md). Use synthetic data only. Preserve a known
   passing artifact and run link in case cold starts take longer than the segment.
2. **Teammate PR:** Andrei opens a small UI PR linked to an issue with acceptance
   criteria. Show CI waiting/running and the bot's waiting report. Narrate that
   lint/tests are ordinary tools, not AI opinions.
3. **Preview:** after CI and deployment trust approval, show Secretary preview,
   deployed SHA, green smoke, artifact and report. Explain shared staging and why
   the SHA must match. Do not call the API `/docs` page a browser-extension preview.
4. **Manual test:** Kendra loads the artifact and tests the changed behavior in
   Chrome; compare a separately labeled production build with the same data and
   viewport. Add the manual test record. It is separate from formal approval.
5. **Correction:** demonstrate a synthetic failure in a disposable PR, a teammate
   correction, new head SHA, fresh checks and updated report. The old evidence
   must not count. Show the offline adverse-scenario tests if live timing is tight,
   and clearly identify them as offline rather than pretending a live event ran.
6. **Human review:** a teammate reviews; when Kendra is the author, someone else
   approves. An authorized human merges after required checks. The bot cannot merge.
7. **Production:** main CI passes, existing Render automation deploys, observer
   verifies exact SHA/health/readiness and uploads metrics. If it fails, show the
   incident draft and discuss recovery; human controls rollback.
8. **Explain a decision:** one shared service keeps costs/operations small, but
   only one PR can occupy it; serialization and invalidation protect evidence.
   Explain one real unresolved risk rather than claiming everything is finished.

## Metrics definitions and retention

The observer samples CI workflows created during the preceding 28 days, paginated
up to 1,000 runs; hitting the cap fails collection visibly. It counts each workflow
ID once using its latest attempt, so success is a **latest-outcome rate**, not a
measure of every rerun failure. Cancelled, pending and other conclusions are
separate. Success rate = successes / (successes + failures) × 100; failures include
failed/timed-out/action-required outcomes. Retain attempted-run data separately if
you need flakiness or first-attempt rate.

PR and main durations are separate: latest attempt's last completed job time
minus workflow creation time, including queue time. Reruns therefore include the
wait until rerun; do not compare them to older job-only averages without noting
the method. Missing timestamps mean no duration sample. This is CI workflow
duration, **not full PR-to-preview lead time**.

Render observations cover at most the latest 100 production deployments and are
filtered to the period. Deployment IDs deduplicate records. Current live and
failed states are reported separately; Render's later `deactivated` records are
not assumed to prove historical success. The live count is a bounded lower bound,
not a complete lifetime deployment count. Merge-to-Render-live uses matching
merge SHA and finishedAt, with a separate application verifiedAt. If a matching
merge timestamp is absent, lead time is not available. Recovery time remains
not available until actual failure/restoration timestamps are supplied.

Download `Veriqo-Production-Evidence/metrics.json` and add its sources to the
existing [metrics log](metrics.md) each consultation. Do not average averages
without sample counts. The observer uploads artifacts and never pushes metrics
commits. Compare like-for-like runs before adding a claimed improvement to
[optimizations.md](optimizations.md).

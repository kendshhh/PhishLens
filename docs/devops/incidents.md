# Deployment incidents and recovery drills

## Secretary incident draft policy

No customer-impacting production incident is confirmed by the available
records. The November 14 production AI acceptance failure is tracked below as an
unresolved functional-availability finding; it is not yet attributed to a
change or assigned customer impact. Planned recovery drills are recorded
separately. A production observer failure emits an incident draft with the
confirmed observation, unknown impact/root cause/recovery time, and bounded
log-signature counts if accessible. Raw logs are not retained because they may
contain credentials or user content. Copy a reviewed draft here after recording
actual timestamps, affected SHA, service/deployment links, mitigation, verified
restoration, and follow-up owner. Do not treat a guessed cause or successful
rollback trigger as verified recovery.

## 2026-11-14 onward: production AI feature-acceptance gap

Production AI analysis failed acceptance across multiple deployed revisions.
The available records confirm a persistent feature gap, but not its onset,
customer impact, or cause. Process health and database readiness remained green.

- On November 14, production deploy `dep-dbs72nu8bjmc73e6ubd0` served SHA
  `623ede53ed52df49132452337a4bf2554e30c514`; its live identity was verified at
  14:37 UTC. `/version`, `/health`, and `/ready` passed, while `/model-info`
  reported `provider_mode=unavailable` and `accepts_tfidf_reports=false`.
- Exact-SHA smoke records report the same provider-preflight failure across
  revisions `2c293f3`, `591a2be`, `76551f6`, and `623ede5`; the exact-SHA
  [run 43605938419](https://github.com/kendshhh/PhishLens/actions/runs/43605938419)
  matches `623ede5`. The November 15 smoke on `205ec26` also failed this check
  in [run 43610307606](https://github.com/kendshhh/PhishLens/actions/runs/43610307606).
  The recorded smokes sent zero analyses, made zero paid provider calls, and
  made zero database writes.
- On November 20, the owner set `AI_ANALYSIS_ENABLED=false`; the matching-SHA
  configuration deploy `dep-dc04t5dg1s2s73e5pc00` completed. This was an
  intentional safety kill switch, not a successful restoration of AI behavior.
  Later November 21 and 23 observations reported analysis disabled.
- The first documented failed production smoke is dated November 14; actual
  failure onset, customer impact, root cause (deployment versus provider or
  configuration), and verified enabled-feature restoration time are unknown.
- DORA treatment: record one unresolved production feature-availability gap
  seen across several SHA checks, not one failed change per smoke. Do not count
  a deployment failure or claim zero CFR until change attribution and the
  production release denominator are reconciled. No complete time-to-restore
  interval is available.

See [release-smoke evidence](production-deploy-smoke.md), [reliability
acceptance](reliability-acceptance-2026-11-14.md), [November 20 release
record](release-record-2026-11-20.md), and the [rolling DORA
reconciliation](metrics.md#dora-measures-refreshed-rolling-window--2026-11-23).

## 2026-10-14: restoration timeout during rollback drill

This was a planned rollback drill. The subsequent restoration failure was real;
no customer outage was established by the available evidence.

- Starting commit: `8a8634e`.
- Rollback target: `717334d`; successful in 35.7 seconds (dashboard evidence).
- Restoration target: `8a8634e`.
- First restoration: failed with internal health-check/port-scan timeout.
- Build installed dependencies successfully. Uvicorn reported startup complete
  and listening on `0.0.0.0:10000`, then shut down gracefully.
- General service logs returned HTTP 200, but could refer to the old instance.
- Controlled retry of the same commit was reported Live; public health succeeded.
- Exact restoration duration and deployed-version screenshot remain to be linked.
- Root cause: not established. A successful retry is not a diagnosed fix.
- Dashboard rollback disabled automatic deployment. The user subsequently
  confirmed restoring `After CI Checks Pass`; later automatic deployments were observed.

### Lessons and follow-up

1. Inspect the failed deployment's logs, rather than treating old-instance health
   responses as proof the replacement started.
2. Verify the Live commit as well as the public endpoint after recovery.
3. Record trigger type: restoration was manual, later delivery was automatic.
4. Recheck Auto-Deploy after rollback or deployment of a specific commit.
5. Capture start/end times for the next drill. Do not invent outage recovery time.

## CI failures (not production incidents)

- Runs `38430884810` and `38431478884`: deliberate health-test expectation failures.
- Run `38502680418`: database PR lint failure; repaired before merge.
- These failures remain in the overall CI success rate and are identified separately.
- Sources and exact job timestamps: [CI run evidence](ci-run-evidence.csv).

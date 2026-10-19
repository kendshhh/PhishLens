# Deployment incidents and recovery drills

## Secretary incident draft policy

No new live incident or recovery drill is claimed by the pilot. A production
observer failure emits an incident draft with the confirmed observation, unknown
impact/root cause/recovery time, and bounded log-signature counts if accessible.
Raw logs are not retained because they may contain credentials or user content.
Copy a reviewed draft here after recording actual timestamps, affected SHA,
service/deployment links, mitigation, verified restoration, and follow-up owner.
Do not treat a guessed cause or successful rollback trigger as verified recovery.

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

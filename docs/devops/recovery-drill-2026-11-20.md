# Neon snapshot and isolated restore drill — 2026-11-20

## Scope and safety

This drill tested recovery of the Neon production branch into a separate
branch. It did not restore over, rename, or finalize the production branch; no
SQL writes were run. Validation queried catalog metadata and aggregate counts
only. No user IDs, email addresses, report subjects, report bodies, credentials,
or connection strings were read into the evidence.

The owner approved objectives of **RTO ≤30 minutes** and **RPO ≤1 hour** on
November 20. Approval sets targets; it does not prove that they are met.

## Snapshot and restore identity

| Item | Recorded value |
|---|---|
| Neon project | `patient-bird-25428852` (`phishlens`, AWS `ap-southeast-1`) |
| Source | `production`, branch `br-orange-sky-b3zzzyqc`, database `phishlens_dev` |
| Snapshot | `snap-shiny-wind-b3ej0mzg`, `release-readiness-recovery-2026-11-20`; manual, created `2026-11-20 13:09:58 UTC` |
| Snapshot expiry | `2026-11-27 13:09:58 UTC` |
| Restored branch | `release-readiness-restore-drill-20261120`, `br-round-feather-b3r2z90t` |
| Restore safety | `finalize=false`; restored branch became `ready` at `2026-11-20 13:10:09 UTC`; production remained the default branch and `ready` |
| Restored-branch expiry | `2026-11-27 13:09:58 UTC` |

Neon branch metadata reports the restored branch's `parent_timestamp` as
`2026-11-20 12:21:32 UTC` (48 minutes 26 seconds before the manual snapshot's
creation timestamp). The snapshot listing did not return an explicit target
timestamp or LSN. Because the provider's timestamp semantics for this snapshot
are not independently established, this delta is recorded but is **not counted
as a measured RPO**.

## Integrity results

The read-only check was run on the production branch and restored branch in
`phishlens_dev`. The same results were returned for each:

- Schema revision: `0004_neon_auth_subject`.
- Aggregate rows: 1 user, 1 saved report and 1 distinct report owner.
- Orphaned saved-report owners: 0.
- `analyzed_emails.user_id` is non-null and has a foreign key to `users.id` with
  `ON DELETE CASCADE`.
- The restored branch reported the same tables, columns, constraints and
  indexes for `users` and `analyzed_emails` as the restored production schema.

The saved-report contents and owner identifiers were not queried. This is a
small-data structural and aggregate-integrity check, not a representative
large-volume restore test.

## Timing and objective limits

The restore request started at `13:10:08 UTC`; Neon reported the new branch
ready at `13:10:09 UTC`. That one-second provider restore-to-ready observation
is for this small dataset only. It excludes incident detection, human approval,
application configuration, traffic cutover, authenticated extension checks,
and post-recovery monitoring, so it does **not** establish the 30-minute
service RTO. The exact recovered point is not established well enough to
measure data loss against an incident, so the one-hour RPO is also **not
verified**.

## Backup and protection limits

The project is on Neon `free_v3`. The production branch protection update was
rejected because this plan allows zero protected branches. The branch remains
unprotected. No automatic snapshot schedule was set: Neon documents scheduled
snapshots as a paid-plan feature. No subscription or billing change was made.
The project retains six hours of point-in-time history; that window is not a
substitute for a tested schedule, alert, and recovery procedure.

One manual snapshot was created and has a seven-day expiry. Neon documents
snapshot storage at `$0.09/GB-month`; manual snapshots are billed as full
snapshots. The logical database size does not establish the billable snapshot
size. See [Neon Backup & restore](https://neon.com/docs/guides/backup-restore)
and [Update backup schedule](https://neon.com/docs/reference/api/snapshots/set-snapshot-schedule).

## Remaining recovery evidence

- Enable production branch protection and a recurring snapshot policy after the
  owner selects an eligible Neon plan or an equivalent provider-supported
  control.
- Confirm the exact live service-to-branch/database/role mapping and least-
  privilege grants without exposing secret values.
- Rehearse application rollback to a schema/config-compatible SHA in staging;
  record exact target and current-settings compatibility.
- Repeat data recovery under a representative workload and measure end-to-end
  RTO and recoverable-point age against the approved targets.
- Assign the primary/backup recovery responders and test alert-to-recovery
  escalation.

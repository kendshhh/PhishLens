# Reliability and restore evidence — 2026-11-14

## Current service identity

Production Render service `phishlens-api` is configured to deploy from `main`
after checks pass. At the latest read-only verification it served commit
`76551f68ff7dc02971cf127fa82f1f35e79cc2ab`; `/health` and `/ready` both
returned HTTP 200. Readiness confirms database connectivity only. The app did
not expose enough information to prove which Neon branch it reached.

The production `/model-info` endpoint returned `provider_mode=unavailable`.
The new exact-SHA smoke was run against `76551f…`; it stopped at this
pre-inference check and made zero analysis/provider requests and zero database
writes. This is a production AI feature failure even though process health and
database readiness are green. The public endpoint does not disclose whether the
cause is a missing/invalid mode or provider configuration; the Render owner
must inspect production configuration and restore a known-good mode before a
release can claim AI behavior acceptance. Do not paste provider credentials
into this repo or a GitHub workflow.

The production Render connection uses Neon endpoint
`ep-dawn-band-b37l1bil.c-4.ap-southeast-1.aws.neon.tech`. After the restore
rehearsal, that endpoint is attached to Neon branch
`br-orange-sky-b3zzzyqc`, currently named `production` and set as the project
default. This branch was created from a manual snapshot. The former production
branch ID `br-purple-dawn-b3a5kzqz` is now named
`devops-original-production-before-restore-20261114` and is not the default.

## Restore rehearsal record

Before the rehearsal, Neon reported six hours of point-in-time history
retention; the production and staging snapshot schedules were empty and the
snapshot list contained no scheduled backup. A manual snapshot of the
production root was created as `snap-nameless-math-b3i4bw19` at
`2026-11-14T02:55:50Z` (`devops-production-restore-test-20261114`). It is set to
expire at `2026-11-15T03:00:00Z`.

The restore created branch `br-orange-sky-b3zzzyqc` and it became ready at
`2026-11-14T02:56:00Z`, about ten seconds after the snapshot timestamp. I set
`finalize=true`; this was wrong for an isolated rehearsal and promoted the
restored branch to the production name/default, changing branch identity. The
original branch was renamed and remains present. The Render production
endpoint stayed attached to
the endpoint ID `ep-dawn-band-b37l1bil`; production `/version`, `/health`, and
`/ready` subsequently returned the expected production identity and HTTP 200.
The two branches showed the same database name, migration revision, and row
counts for `users` and `analyzed_emails` when compared. A later read-only
comparison found one user and one analyzed email on each branch, the same latest
analysis timestamp, and matching whole-row content digests for every public
base table (`users`, `analyzed_emails`, and `alembic_version`). No data
divergence was detected at comparison time. No application data was written by
the rehearsal or its checks.

This was **not a clean, low-risk restore acceptance**: it changed Neon branch
topology/default state, and an original branch with children could not be
expired. The roughly ten-second value is branch provisioning time, not measured
end-to-end recovery time. No outage duration was measured. The safe production
restore procedure still needs a rehearsal that keeps the intended branch and
endpoint stable, explicit verification of the restored data, and a tested
rollback path. Do not repeat `finalize=true` against a production snapshot
without an explicit target-branch restore plan.

## SLI/SLO and recovery targets

No team-approved SLI/SLO or RPO/RTO target was found in the repo or the current
evidence. These are proposed for owner/team review, not approved commitments:

| Measure | Proposed definition | Proposed target | Evidence/status |
|---|---|---|---|
| API availability SLI | One-minute synthetic probe passes only when `/health` and `/ready` both return the expected HTTP 200 contracts | At least 99.5% successful probes in a rolling 30-day window | The probe and retained time series are not yet configured; `/ready` alone does not prove correct database identity |
| Feature SLI | Fixed synthetic analysis returns the expected TF-IDF classification and risk level, with the pinned model SHA | At least 99% passing samples in a rolling 30-day window | The two-case deploy smoke is implemented locally but not yet deployed; current staging CRUD acceptance is a single run |
| RPO | Maximum age of a recoverable database point | 1 hour proposed | Not measured; six-hour history retention and no verified backup schedule do not prove a one-hour RPO |
| RTO | Time from declared database incident to production feature recovery | 4 hours proposed | Not measured; the restore rehearsal changed branch topology and did not measure user-facing outage/recovery |

The owner/team must approve or replace these definitions and targets. An
actual backup schedule, restore runbook, and repeatable restore test are release
requirements before representing the database recovery objective as satisfied.

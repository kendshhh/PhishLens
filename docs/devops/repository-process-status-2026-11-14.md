# Repository visibility and process evidence — 2026-11-14

## Visibility

GitHub's repository API reports `kendshhh/PhishLens` as public. The owner has
confirmed that public visibility is intended. This current status supersedes
conflicting November 8 and November 13 notes that describe private visibility
as intended or unresolved. Those documents remain historical records; they
must not be treated as the current repository setting.

## Security scan and dependency merge policy

Gitleaks v8.30.1 scanned all refs and full history (499 commits) and found no
leaks. The initial changed-source scan covered 33 files and passed after
sanitizing the CI timing export. Its first pass flagged 70 generic-key patterns
in that export, which contained run/branch/SHA metadata rather than credentials.
I removed those identifiers and retained per-run event, result, timestamp, and
duration so sample counts and timing calculations remain auditable. Files
changed after that initial scan were rescanned individually before their pushes;
those scans also found no leaks. Reports were stored outside the repository.
The November 14 Sprint 1–3 closeout, architecture records, process-status update,
and README status were scanned with Gitleaks v8.30.1; the changed-source scan
found no leaks.

PR #197 merged as `76551f68ff7dc02971cf127fa82f1f35e79cc2ab` on November 14.
The active `main` ruleset `26782191` requires both `Dependency security` and
`Dependency graph review (GitHub Advanced Security)`, along with the existing
application and staging checks. The deterministic AI evaluation changes are in
open PR #196 and are not yet a required `main` check.

A current GitHub Dependabot API query still reports 12 open high `pyasn1`
alerts (four advisories across three requirements manifests) and three open
medium `opentelemetry-api` alerts. The three default-branch requirements
lockfiles pin `pyasn1==0.6.5`, the first patched version. Treat the open alerts
as unresolved until GitHub's dependency graph/alert state is reconciled; do not
dismiss them just because the files contain a patched pin. See
[dependency-audits.md](dependency-audits.md) and the [Sprint 1–3 DevOps
closeout](kendra-sprint-1-3-status-2026-11-14.md).

## Participant-sourced course records

The current checkout contains no participant-sourced evidence for the latest
standups, retrospective, or consultation. No attendee statements, dates,
decisions, or instructor feedback are inferred or fabricated here. The closeout
is incomplete until participants provide source notes with:

- date/time and attendees;
- what was completed, planned next, and blocked at each standup;
- retrospective observations and agreed actions;
- consultation date, instructor/consultant, questions asked, decisions, and
  follow-up;
- source evidence such as meeting notes, links, or instructor feedback.

The repo can preserve provided records, but it cannot supply participant
evidence by reconstructing events after the fact.

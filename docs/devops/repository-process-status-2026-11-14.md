# Repository visibility and process evidence — 2026-11-14

## Visibility

GitHub's repository API reports `kendshhh/PhishLens` as public. The owner has
confirmed that public visibility is intended. This current status supersedes
conflicting November 8 and November 13 notes that describe private visibility
as intended or unresolved. Those documents remain historical records; they
must not be treated as the current repository setting.

## Security scan and dependency merge policy

Gitleaks v8.30.1 scanned all refs and full history (499 commits) and found no
leaks. A separate scan of all 33 changed source files also found no leaks. Its
first pass flagged 70 generic-key patterns in the raw CI timing export; the
export contained run/branch/SHA metadata rather than credentials. I removed
those identifiers and retained per-run event, result, timestamp, and duration
so the sample counts and timing calculations remain auditable. The sanitized
changed-file scan passed. Reports were stored outside the repository.

The workflow blocks high/critical npm findings, high/critical GitHub
dependency-graph findings, and any reported vulnerability in the pinned Python
dependency audit. The active `main` ruleset `26782191` now requires both
`Dependency security` and `Dependency graph review (GitHub Advanced Security)`;
GitHub's API confirmed the updated contexts. The new deterministic AI
evaluation runs and passes on AI-changing PRs (including PR #196), but its
workflow is still under review and the evaluation check is not yet required by
the `main` ruleset. GitHub currently reports 12 high Dependabot alerts on
default `main`: four `pyasn1` advisories repeated across three lockfiles. PR
#197 pins `pyasn1` to the first patched version, 0.6.5, in all three files and
its lockfile audit passes; those default-branch alerts remain open until the
PR is merged. See [dependency-audits.md](dependency-audits.md).

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

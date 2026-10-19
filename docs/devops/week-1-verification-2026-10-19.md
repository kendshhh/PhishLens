# Week 1 verification follow-up - October 19, 2026

Scope: Kendra's K6 (meaningful CI), K7 (protection/deployment), K8 (evidence).
Times below are UTC unless explicitly labeled. Related: #9, #24, PR #34.

## Verified current state

Baseline main: `d6e5998e7e655607329386cead146e1f9a73ec3b`.
The older local Week 1 notes predate the merged popup fix and staging automation.

- The GitHub main branch API reports protection enabled with required
  Backend checks, Extension checks, Staging integration, and Hosted staging.
- The authenticated GitHub protection editor was read without changing it.
  It confirms one approval, stale approval dismissal, up-to-date branches,
  resolved conversations, and protection applying to administrators.
  Force pushes and deletions are disabled. No bypass was used.
- The merged popup uses the shared `getAnalyses` client and renders subject,
  prediction, risk, and confidence as text. This resolves the old response-shape
  source defect; it does not establish installed-Chrome acceptance.
- Main CI [39185832544](https://github.com/kendshhh/PhishLens/actions/runs/39185832544)
  passed Backend checks, Extension checks, and Staging integration. Hosted
  staging is intentionally skipped on main pushes.
- Production observer [39185962984](https://github.com/kendshhh/PhishLens/actions/runs/39185962984)
  completed successfully and published
  [Veriqo-Production-Evidence](https://github.com/kendshhh/PhishLens/actions/runs/39185962984/artifacts/12158006783).
  The downloaded metrics report verifies exact production SHA, health, and readiness.
  The retained [metrics JSON](evidence/week1-production-2026-10-19.json) records
  live deployment dep-dban778ae00c739v6hng, trigger new_commit, and matching SHA.
  Independent public requests also returned HTTP 200 from /version, /health,
  /ready, and /api/analyses; /version identified production at d6e5998 and
  history returned the synthetic account notice (phishing/high/0.93).

Source: [branch API](https://api.github.com/repos/kendshhh/PhishLens/branches/main)
and the saved main protection editor under repository Settings > Branches.

## Frontend failure and repair

[Intentional failing CI 39186096867](https://github.com/kendshhh/PhishLens/actions/runs/39186096867)
tested head `f80c27c3741fb52cd5c489ad269a6e496dd0e3c5`.
The Extension checks log reports:
`popup.js 45:7 'weekOneLintDrill' is assigned a value but never used no-unused-vars`.
ESLint exited 1; subsequent extension packaging steps did not run.
This was an isolated draft PR; the broken revision was not merged or deployed.

Repair commit `c4862a38f55975569048647d1e1da5139079141d` removes the
temporary variable and restores the original merged popup exactly.
The subsequent validator revision
`77e4f4c5464ec2be0b369ae5451a3e83e3e27208` passed Extension checks in
[39186157804](https://github.com/kendshhh/PhishLens/actions/runs/39186157804),
including lint, tests, validation, packaging, and artifact upload.
Later commits add regression coverage and this record; use the latest PR run
for final review. A repaired extension job is distinct from all final PR checks.

## Asset validation repair

Validation now parses actual popup script, link, and image references.
Missing files, external references, and paths escaping the package fail.
Current module-worker and required-file checks are preserved.
Four regression cases exercise valid, missing, external, and encoded-traversal
references through the real validator in a temporary synthetic package.
This covers direct HTML references, not a complete transitive JS/CSS dependency
graph or Chrome runtime permission behavior.

## Current measured main sample

One workflow, one attempt, one successful main sample; no average or optimization
gain is claimed. Workflow created 01:32:41; last job completed 01:34:19:
98 seconds including scheduling. Job execution:
Backend 49 seconds; Extension 7 seconds; Staging integration 44 seconds.
Hosted staging was skipped. Source: run 39185832544 and its jobs API.
These values must remain separate from the historical job-only averages.

## Remaining acceptance

- Load the latest appropriate CI package in Chrome and record version, source SHA,
  backend live SHA, rendered synthetic history, and runtime errors.
- Coordinate changed-record and persistence verification in the agreed demo
  environment; do not modify production or real user records for this drill.
- Collect actual teammate approval and required hosted checks before merge.
  This draft intentionally avoids deploying the failure drill to shared staging.
- Production metrics have been downloaded and retained before artifact expiry;
  complete historical recovery timing remains unavailable.
- Record real consultation feedback, standups, team retrospective, and instructor
  acceptance of the extension presentation arrangement. These cannot be
  reconstructed from code or CI.
- Keep #9 open until its full remaining acceptance is evidenced.

Initial restricted endpoint probes failed DNS resolution. The authorized network
retry succeeded for all four public routes; no public outage is inferred. Git operations could not access the repository root in
this sandbox, so the draft was created through the GitHub connector without
changing the user's local checkout.

## Regression verification

CI 39186216063 passed the four new validator cases within the 40-test scripts
suite, alongside the real isolated PostgreSQL/API/client smoke. Latest-head checks
remain the acceptance authority after documentation updates.

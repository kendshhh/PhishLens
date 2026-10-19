# Inspection and course evidence — October 19, 2026

Repository inspected: [kendshhh/PhishLens](https://github.com/kendshhh/PhishLens).
The request's repository placeholder was resolved from the existing Git remote.
Branch for implementation: `feat/devops-secretary`, based on main `dcdac37`.
The separate `fix/analysis-timeout` PR #32 is preserved; its shared-origin change
has not been silently merged into this branch. The preview packager supports its
shared configuration and the known older localhost constant on current main.

## Repository findings

| Area | Exists | Missing / improvement | Cannot verify here |
|---|---|---|---|
| Product | Chrome MV3 extension, HTML/CSS/JS, Python FastAPI API | Full CRUD and saved new AI assessments remain unfinished | End-user acceptance of current features |
| AI | Mock, Gemini, optional pinned local DistilBERT; backend schemas/service; synthetic eval cases; mock failure tests | Real-provider acceptance, quality/calibration, automatically triggered quality evaluations | Current Gemini quota/key and held-out model quality |
| Data | PostgreSQL/Neon, SQLAlchemy, Alembic, related models, migration/seed and relationship checks | Preview must verify actual host, not only `phishlens_dev` name | Private Neon branch/role configuration |
| Dependencies | Python runtime/dev/optional-AI `.in` and pinned `.txt`; npm package/lockfile | No standalone type checker; configured ESLint scope excludes root worker | Full historical credential scan; current vulnerability audit |
| CI | Backend/Extension checks, disposable PostgreSQL staging integration, legacy hosted staging | Trusted control plane, exact-head report, explicit stale-preview handling | New workflows have not run on GitHub |
| Hosting | Render staging and production, Singapore/free plans | Staging host checks and public `/version` needed | Runtime environment secret contents are intentionally not exposed |
| Production | Render `main`, `autoDeploy=yes`, `autoDeployTrigger=checksPass`, `/health` | Automated exact-version observer and evidence artifacts added | Branch protection enforcement through admin API |
| Staging | `phishlens-staging`, auto-deploy off, Python start script | Move deployment key to protected environment; constrained controller | Environment reviewers and isolated DB host need owner setup |
| GitHub | Task branches, PR template, issues #7/#8/#9/#20/#21/#23; PR #32 open | One secretary report, tailored manual checklist | Project board contents/permissions unavailable through connector |
| Rules | Rulesets collection returned empty | Independently verify classic branch protection | Classic protection API returned HTTP 403; empty rulesets is not proof of unprotected main |
| Docs | README, PIPELINE, schema/API/AI docs, metrics, optimization proposals, runbook, incident log | Some status paragraphs are historical; new guide distinguishes current evidence | Teammate understanding/coordination cannot be inferred from code |
| Config | `.gitignore`, `.env.example`, private config ignored | Add host guard example and exclude generated output | Real secret values were not printed or committed |

Development branches include `feat/ai-engine`, `ci/staging-validation`,
`feat/7-history-slice`, `feat/22-package-and-verify`, and `fix/analysis-timeout`.
They are evidence of repository structure, not claims that all work is merged.
No unrelated source changes were carried over from PR #32.

## Course source and access

Read [the course guide](https://csp221a.vercel.app/): overview, roles, seven product
requirements, four sprint descriptions, DevOps track, consultation/demo/individual
rubrics, hosting guidance and final deliverables. The web reader failed, so the
page was retrieved directly over HTTPS. Linked videos and their transcripts were
not reviewed. A linked project board was not available through the connector.
The guide permits stack choices; it does not require this bot, Gemini, Render,
per-PR hosting, a separate dashboard, or autonomous merging.

## Explicit requirements versus our choices

| Source expectation | Chosen implementation / evidence limit |
|---|---|
| R1 persistent create/read/update/delete | Secretary maps affected paths; it does not implement or certify missing product CRUD |
| R2 useful AI with backend processing | Existing validation/service is inspectable; mock tests do not prove real-model quality |
| R3 backend API | FastAPI, existing API tests, `/version` identity added |
| R4 frontend consumes real backend data | History smoke plus downloadable staging extension; Chrome still manual |
| R5 at least two meaningful related entities | Existing schema/seed relationship tests in disposable PostgreSQL; do not mark met from table count alone |
| R6 separate environment config and secrets | Protected staging environment, host allowlist, secret stores; owner must finish setup |
| R7 invalid-input and AI-failure behavior | Existing mocked API/provider failure tests; report calls for changed-feature review |
| PR checks and automatic main delivery | Preserve existing CI and Render after-checks deployment; add observer |
| Quality gates and teammate review | Recommend existing checks plus `Secretary staging`, stale approval dismissal and current branch; owner verifies enforcement |
| Staging/previews encouraged | Reuse one isolated shared staging service with serialization and exact-SHA evidence |
| Record measurements and optimization | Artifact-based metrics with sources; no unmeasured gain claimed |
| Release/rollback proof | Existing runbook retained; no new rollback drill or release is fabricated |
| DevOps documentation/evidence | Guide, diagram, logs, example report, verification matrix and demo script added |

Sprint interpretation: foundation and deployed walking skeleton in Sprint 1;
working persistent CRUD in Sprint 2; meaningful processed AI, evaluation and mocked
provider tests in Sprint 3; hardening, measured optimization, release and rollback
evidence in Sprint 4. The secretary supports that process; it does not substitute
for the product increments or the team's standups/retrospectives.

## Individual DevOps rubric checklist

These are evidence tasks, not an awarded grade. Weights are from the course guide.

| Criterion | Weight | Pilot contribution | Still needed |
|---|---:|---|---|
| Pipeline design/coverage | 15 | Defined CI → preview → review → production observer; justified stages | GitHub/cloud rollout and end-to-end demonstration |
| Automation/quality gates | 10 | Existing CI/deploy preserved; separate trusted report and staging check | Verify and require new check without bypass; teammate approval |
| Measured optimization | 20 | Deduplication and bounded work implemented | Comparable before/after runs; no gain measured yet |
| Environments/secrets | 10 | Isolated-host guards, environment boundaries, staging banner | Owner config, key migration/rotation and DB inspection |
| AI-aware pipeline | 10 | Mock tests; no live inference in normal checks; bounded optional summary | Automatic quality evaluation on prompt changes and capped scheduled product-AI smoke |
| Release/rollback | 10 | Human rollback runbook preserved | Tagged release/changelog and verified drill |
| Reliability/incidents | 10 | Offline adverse scenarios; incident draft on observer failure | Real incident/restore evidence and flaky-test measurements |
| Metrics/docs/reporting | 10 | Metrics calculator, artifacts, operator guide and reporting | Weekly retained metrics and sources for each sprint |
| Live performance | 5 | Consultation walkthrough | Kendra explains and operates live pipeline herself |

The consultation rubric separately evaluates delivered sprint work, a deployed
increment, process, DevOps evidence and risk planning. Demo Day includes product
CRUD, meaningful AI, resilience, secrets, and a live deployment challenge. A bot
report or static screenshot cannot replace those demonstrations.

## Evidence design references

- [GitHub workflow events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows): trusted workflows use `workflow_run` to observe completed CI and reruns; no privileged PR checkout.
- [Render deploy lifecycle](https://render.com/docs/deploys) and [health checks](https://render.com/docs/health-checks): accepted deployment requests are followed to live and then independently checked.
- [Gemini structured output](https://ai.google.dev/gemini-api/docs/structured-output): optional JSON explanation is schema-validated and remains advisory.

The Render Markdown references could not be read by the web tool; their HTML
versions were read instead. Prices are linked in the operator guide rather than
copied as permanent promises.

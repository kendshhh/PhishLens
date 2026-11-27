# PhishLens final-check video flow

**Maximum duration:** 15:00<br>
**Format:** each presenter records their assigned screen/narration clips separately; an editor combines them in the order below<br>
**Recording rule:** show the real deployed system and real evidence from one traceable run. Do not combine unrelated CI or deployment runs as if they were one.

The complete combined script, with every role’s lines and screen actions, is in the [full team video script](full-team-video-script.md). Separate clip guidance is in the [team speaker scripts](team-video-speaker-scripts.md); Kendra’s extended DevOps click-by-click guide is in the [Kendra speaker guide](kendra-video-script-click-guide.md).

> Current evidence cutoff — November 21, 2026: release is **NO-GO**. Production
> analysis is disabled; staging requires Bearer authentication and hosted
> authenticated CRUD is open. The patched anonymous staging smoke passed
> locally. Render auto-deploy metadata conflicts with the latest production
> deploy trigger. Use the [current DevOps evidence index](devops/README.md),
> and do not present a numeric score or automatic-deployment pass without
> approved criteria and same-candidate proof.

## Readiness against the submission instructions

No completion percentage is approved: weights and scoring rules remain pending,
and several acceptance items are open. Do not state 90% or 100% complete until
the team/instructor approve the rubric and current candidate evidence passes.

| Submission requirement | What repository evidence says | What must be ready for the recording |
|---|---|---|
| Deployed frontend / website | The documented frontend is a Chrome extension. The repo does not document a hosted website frontend or its deployment dashboard. | Confirm with the instructor that the production-targeted installed extension qualifies. If the requirement means a browser-accessible website, the current frontend does not meet it; resolve this before recording. |
| Production feature and full CRUD | Saved reports/history and CRUD are implemented. Existing hosted CRUD evidence is historical and is not tied to the current candidate SHA. | Use an isolated, verified staging target and the matching deployed SHA. Demonstrate create, list/detail read, update, fresh reread, delete, and post-delete verification with synthetic data. Show the corresponding database row/query evidence. |
| Backend and database | Production currently reports `analysis_enabled=false` and `provider_mode=disabled`; staging reports TF-IDF. The Render-to-Neon connection mapping is not verified from readiness alone. | Refresh exact Render identity and `/model-info` checks. Privately verify Render-to-Neon branch/database/role mapping before any write. Do not show secrets. |
| AI feature | The primary review is local in Chrome: TF-IDF v12a, local Llama judge, then TF-IDF/KRR/LightGBM checks. Code validates the judge response and quote in the browser; the save API recomputes classifier fields and marks the LLM audit browser-reported. | Demonstrate an actual local-model result from the production-targeted package and explain this architecture accurately. Do not claim the backend runs or validates the local LLM. The backend provider mode must be rechecked if claiming backend AI works. |
| Tests and evaluation | Unit/API/CI coverage is configured. The documented 40-case development cohort reported 65% binary accuracy, 3/16 phishing recall (18.75%), and 6.25% legitimate false-positive rate. It is not held-out evidence or an approved release threshold. | Show current passing results for the candidate SHA, representative failure cases, and the evaluation input/expected/actual cases. Label the cohort as development-only and show the limitations. |
| DevOps end-to-end proof | Effective required checks are not verified. Render metadata reports auto-deploy off while the latest production deploy record says `new_commit`; no automatic deploy claim is accepted. | Resolve the Render discrepancy and effective GitHub check contract, then record one test-only change → PR checks → independent approval → merge → exact deployment → verification run. Use the same SHA throughout. |
| Rollback | The Nov 20 Neon drill restored to an isolated branch and checked schema/aggregate integrity; it did not measure service RTO/RPO or prove application rollback. | Show the drill record and limitations honestly. Do not say production rollback or recovery objectives have passed. |

**Go/no-go:** production analysis, hosted authenticated CRUD, instructor scope
confirmation, and the same-candidate release path remain open. Do not record a
release acceptance or numeric completion score until these gates and the
approved rubric are satisfied.

## Run of show (15 minutes maximum)

| Time | Lead | What to show and say |
|---|---|---|
| 0:00–0:40 | Kendra | Introduce PhishLens, its purpose, and the team. State a completion percentage only if the team/instructor have approved the scoring rule and current evidence supports it; otherwise state NO-GO and name the remaining work. |
| 0:40–3:10 | Andrei | Open the **deployed production-targeted frontend** (not localhost). If the instructor confirms the Chrome extension qualifies, show the installed package identity/API target, then scan a synthetic suspicious email. Show input, loading, result, evidence/observations, next action, and one validation or failure state. Do not promise a verdict before the model returns it. |
| 3:10–5:30 | Leyan / Trixia | Demonstrate real isolated staging CRUD using synthetic data: save/create with consent → list and detail/read → edit notes or feedback → reload and reread to prove persistence → delete → confirm absence/404. Show the matching database record/query before deletion and verify absence after deletion. Point out that scanning alone does not save text. |
| 5:30–6:35 | Trixia / Kendra | Show the Render backend service, current production deployment, status and a short recent log excerpt. Show Neon provider, verified staging branch/database, relevant tables and activity/query view. Show the frontend production delivery evidence available for the installed extension. Keep credentials and secret values hidden. |
| 6:35–8:40 | Wilberr | Explain and demonstrate the actual AI feature. Identify TF-IDF v12a, the local Llama judge, and the KRR/LightGBM reevaluation. Show the observed generated/advisory result and the exact supporting text. Explain that browser code validates the LLM JSON/quote and that the API recomputes classifier fields on save; do not imply a backend LLM call. Briefly state how invalid output, unavailable model/GPU, timeout, or disagreement becomes an error or **Uncertain** result. |
| 8:40–9:50 | Wilberr / Trixia | Show unit, API/integration and failure tests, the candidate SHA, CI run, and example evaluation cases with expected and actual outcomes. Show the documented 40-case figures only with the label “development cohort — not held out; threshold not approved.” |
| 9:50–14:30 | Kendra | Demonstrate the real DevOps change from start to finish, using the sequence below. Show actual repository rules, required checks, approval, CI history, Render deployment and production verification. Trim waiting time only; retain the identifiers and results from this same run. |
| 14:30–15:00 | Editor combines individual closing clips | Each member records a short contribution separately; Kendra records the final verified completion/status line. Close without upgrading any unverified item to “complete.” |

## DevOps sequence to capture in the 9:50–14:30 segment

Prepare and rehearse this flow before recording so the video shows one continuous, traceable change:

1. Create a fresh branch from current `main` and add a harmless, meaningful test-only assertion that triggers the required workflows. Commit and push it.
2. Open the PR. Show the branch/head SHA and the automated run triggered by that PR. Keep the browser on this run while showing the configured checks, tests, and build/package stages.
3. Show the repository rules: protected `main`, one required teammate approval, and required status checks. Show the approval on this PR and that merge is unavailable until its required gates pass.
4. Merge the approved PR using the repository’s allowed merge method. Show the resulting `main` commit SHA.
5. Show Render’s automatically triggered production deploy for that merge. Keep its source SHA tied to the PR/merge SHA; show build logs, final deploy status, and recent runtime logs.
6. Open the production app/API and verify it is accessible and functional. Show `/version` or the equivalent release identity and a health/feature check. Do not substitute a manual deploy or an unrelated successful run.

If the run takes longer than the segment, speed up or trim waiting periods from the recording while retaining the same run, check results, approval, merge, deploy status, and source SHA. A manually triggered deployment does not satisfy the requirement. Coordinate the actual teammate review and any required protected-environment approval; do not simulate approval.

## Recording preflight

- Refresh production and staging status immediately before recording. The checked-in service observations are dated snapshots, not proof of current state.
- Resolve whether the installed Chrome extension satisfies the instruction to demonstrate a deployed website. The repo documents an extension frontend, not a hosted website frontend or website-hosting dashboard.
- Confirm the exact production extension package/revision, API target, local model assets, and WebGPU support. Warm the model before the take. Use synthetic email content and `.example` links only.
- Before staging CRUD, verify the exact Render-to-Neon target and candidate SHA. Use an isolated staging record and finish cleanup. Never write demo records to production.
- Prepare panes for the deployed app, Render, Neon, GitHub PR/run, and evidence. Hide credentials, private mail, secret fields, unrelated tabs, and notifications.
- Select the same PR and deploy run for every DevOps shot. Keep its branch, head SHA, merge SHA, deploy source, and final verification visible or legible in the edited video.
- Rehearse to 14:30 to leave room for transitions. The final export must be no longer than 15:00 and include clear screen capture and understandable audio.
- Record each speaker section as a separate clip and assemble them in the run-of-show order. Match the app revision and demo identifiers across clips; do not imply everyone was present in one live recording.

## Source references

- [Extension journey and current acceptance limits](extension-journey.md)
- [Architecture and environment map](architecture.md)
- [Live AI workflow, model path, and limitations](ai/live-workflow.md)
- [Current DevOps acceptance status (Nov 14 snapshot)](devops/kendra-sprint-1-3-status-2026-11-14.md)
- [Reliability and restore evidence (Nov 14 snapshot)](devops/reliability-acceptance-2026-11-14.md)
- [Pipeline requirements and status](../PIPELINE.md)

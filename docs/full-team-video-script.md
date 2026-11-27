# PhishLens full team video script

This is the single combined script for the final presentation. Each person records their own assigned clips separately; the editor assembles them in this order. Keep the finished video at or below **15:00**.

## Team roles

| Presenter | Assigned role | Main video section |
|---|---|---|
| Kendra | DevOps Engineer | Intro, live deployment identity, PR-to-production workflow, final status |
| Andrei | Frontend Developer | Chrome extension and user experience |
| Leyan | Fullstack Developer | Extension-to-API flow and saved-report CRUD |
| Trixia | Backend Developer | FastAPI, database schema, persistence, test evidence |
| Wilberr | AI Engineer | AI pipeline, failure handling, model evaluation |

## Important readiness note

Current status — November 21, 2026: release is **NO-GO**. Production serves
`811980c` with analysis disabled; staging serves `ba0b6c5` and protects saved
history with Neon Auth. The patched anonymous staging smoke passed locally, but
hosted authenticated CRUD and installed-extension acceptance remain open.
Render metadata says auto-deploy is off while the latest production deployment
record says `new_commit`; do not claim automatic deployment until that
discrepancy is reconciled. The effective required checks are not verified. The
current product scope is a Chrome extension, and instructor confirmation remains
pending. See the [current DevOps evidence index](devops/README.md) before
recording.

Do not fill in a completion percentage: weights and scoring rules are not
approved. Use the honest NO-GO status and describe the recording as a progress
review until the team/instructor approve a score and all required evidence is
complete.

## Final edit order

| Time in final video | Presenter | Clip filename | Content |
|---|---|---|---|
| 0:00–0:40 | Kendra | `01-kendra-intro.mp4` | Project, DevOps role, verified completion and remaining work |
| 0:40–3:10 | Andrei | `02-andrei-demo.mp4` | Deployed/approved frontend, synthetic email scan, states and result |
| 3:10–4:20 | Leyan | `03-leyan-crud.mp4` | Create/read/update/reread/delete in extension and API evidence |
| 4:20–6:15 | Trixia | `04-trixia-backend-db.mp4` | Render API, Neon schema, same synthetic record |
| 6:15–6:35 | Kendra | `05-kendra-service-sha.mp4` | Confirm current backend SHA and environment |
| 6:35–8:40 | Wilberr | `06-wilberr-ai.mp4` | Actual AI result, model flow, validation and failures |
| 8:40–9:15 | Wilberr | `07-wilberr-evaluation.mp4` | Evaluation cases and recorded measurements |
| 9:15–9:50 | Trixia | `08-trixia-tests.mp4` | Test suite, CI run and results |
| 9:50–14:30 | Kendra | `09-kendra-devops.mp4` | Rules → branch → PR → review → merge → automatic deploy → verify |
| 14:30–15:00 | All, recorded separately | `10-team-close.mp4` | Four-second contribution lines, then Kendra’s status close |

## Separate recording setup

- Record only the clips assigned to your role. No one needs to record in the same room or call.
- Use landscape, a readable screen scale, and consistent browser zoom. Begin each clip with two seconds of silence on the opening screen; leave two seconds at the end for editing.
- Record your own narration with the screen. Keep transitions optional; the editor can use a title card instead of a live handoff.
- Use synthetic email and report data only. Keep request bodies, secrets, real inboxes, and personal notifications out of frame.
- The editor may trim waiting and pauses. Do not combine unrelated CI runs or deployments. The DevOps clips must all identify the same PR, head SHA, workflow run, review, merge SHA, Render deploy, and verification.
- Refresh live status before recording. Repo status documents are dated snapshots.

---

## Scene 1 — introduction and completion

**Time:** 0:00–0:40<br>
**Speaker:** Kendra<br>
**Screen:** title card: “PhishLens — AI-assisted phishing email review”; then a one-line completion/evidence summary.

**Kendra says:**

> “Hi, I’m Kendra, the DevOps Engineer for PhishLens. PhishLens is a Chrome extension that reviews selected email text and surfaces suspicious wording. I coordinate our CI checks, protected release process, deployments, and operational evidence. Our team-verified completion is **[X%]**, measured against **[our agreed checklist]**. The remaining work is **[actual open items]**.”

If the team has not verified a percentage, Kendra says:

> “Our latest repository audit does not yet verify the required 90% completion level. We are still closing the deployment and acceptance gaps.”

## Scene 2 — frontend demo

**Time:** 0:40–3:10<br>
**Speaker:** Andrei<br>
**Screen:** approved deployed/production-targeted frontend with a synthetic email. If the instructor requires a hosted website and has not accepted the extension, stop and resolve that before final recording.

### Andrei’s screen actions

1. If package identity needs to be shown, open `chrome://extensions` → PhishLens → **Details**. Show the installed package version/identity and approved API target, then return to the synthetic email.
2. Select the complete synthetic email text.
3. Right-click → **Analyze selection with PhishLens**.
4. Keep the popup visible during loading. Show the selected-text preview.
5. Show the actual assessment, wording observations, next action, and any partial-check warning or **Uncertain** state.
6. Point to one exact phrase in the sample that supports a visible observation. Do not save yet; Leyan will show saving and CRUD.

**Andrei says:**

> “This message is synthetic. I select the full visible email and choose Analyze selection with PhishLens. The extension shows the input, waits for the local review, and then gives us an advisory result with the wording it relied on. The next action is to verify through a trusted channel; this result does not authenticate the sender.”

If the model is unavailable, Andrei shows the real **Uncertain**/unavailable state or a prepared recording from the same synthetic case. No cloud fallback and no rerunning until a preferred result appears.

## Scene 3 — frontend-to-backend and CRUD

**Time:** 3:10–4:20<br>
**Speaker:** Leyan<br>
**Screen:** verified isolated staging extension/package and DevTools Network, using one synthetic report.

### Leyan’s screen actions

1. On the result, enter an optional title, tick upload consent, and click **Save report**.
2. Show the saved confirmation/ID.
3. Open **Saved reports** → **Load / refresh history** → **View details** for the new record.
4. Click **Edit notes**, make one harmless note change, save it, close/reopen the popup, and reload history to prove the update persisted.
5. In DevTools Network, show only method/path/status for `POST /api/analyses`, `GET /api/analyses` or `/api/analyses/{id}`, and `PATCH /api/analyses/{id}`. Do not expose request bodies, auth tokens, or credentials.
6. Delete the report in the app; refresh history and show it is gone. Trixia will confirm the same ID is absent from Neon.

If popup DevTools is unreliable, rehearse it before recording; use `chrome://extensions` → PhishLens → **Details** → **Inspect views** → popup/service worker → DevTools **Network**. The API contract is in `docs/api-reference.md` as a fallback screen, but it does not replace the real app CRUD evidence.

**Leyan says:**

> “The scan stays local until I explicitly consent and choose Save report. The extension client sends the saved-report request to the API; it does not connect to Neon directly. Here we created the report, read it, changed the notes, reread after reopening, and deleted it. The Network panel shows the HTTP methods and statuses for this same synthetic record.”

Do not claim per-user authentication/isolation for shared demo history.

## Scene 4 — backend and database

**Time:** 4:20–6:15<br>
**Speaker:** Trixia<br>
**Screen:** current deployed API docs, Render service, and verified staging Neon branch.

### Trixia’s screen actions

1. Open the current deployed backend’s `/docs` page, using the service URL shown in Render. Do not use localhost.
2. Point to `POST /api/analyses`, `GET /api/analyses`, `GET /api/analyses/{id}`, `PATCH /api/analyses/{id}`, and `DELETE /api/analyses/{id}`.
3. In Render → PhishLens project → `phishlens-api` → **Logs**, show a short suitable runtime excerpt if available. Keep request bodies and user data hidden.
4. In Neon Console → PhishLens project → **Branches** → privately verified staging branch → `phishlens_dev`, show `users` and `analyzed_emails` and their relationship (`analyzed_emails.user_id` references `users.id`).
5. Use a read-only query to show the synthetic report ID from Leyan’s demo. Ask Leyan to delete it through the app; refresh the lookup and show zero matching rows. Never perform CRUD manually in SQL.

Example read-only query after confirming the database target:

```sql
SELECT id, user_id, subject, prediction, notes, created_at
FROM public.analyzed_emails
WHERE id = 'DEMO-REPORT-UUID'::uuid;
```

After app deletion, use the same predicate with `SELECT count(*)` and show zero. If the Render-to-Neon branch mapping is uncertain, do not inspect or write data.

**Trixia says (backend):**

> “The backend is FastAPI on Render. The client calls these saved-analysis routes over HTTPS. The server validates the request and owns persistence; the browser never receives database credentials. The request statuses Leyan showed came from these API routes.”

**Trixia says (database):**

> “This is the same synthetic report ID from the app, stored in the verified staging database. The report row is linked to its user through `user_id`. After the app deletes it, the database lookup returns no matching row.”

## Scene 5 — deployment identity

**Time:** 6:15–6:35<br>
**Speaker:** Kendra<br>
**Screen:** Render Deploys page and browser `/version` response for the current production backend.

**Kendra says:**

> “This is the backend deployment identity. `/version` confirms the commit and environment. I’ll show how a reviewed change reaches this live version in the DevOps walkthrough.”

## Scene 6 — AI workflow and failures

**Time:** 6:35–8:40<br>
**Speaker:** Wilberr<br>
**Screen:** actual result from Andrei’s synthetic scan, then `docs/ai/live-workflow.md` diagram.

### Wilberr’s screen actions

1. Point to the actual result and its visible exact-text observation.
2. Show the workflow diagram: TF-IDF v12a → local Llama judge → software validation → TF-IDF/KRR/LightGBM reevaluation.
3. Explain that browser code validates the constrained JSON and exact supporting quote. Agreement may produce a reviewed advisory result; disagreement, missing GPU/model, or failure may produce **Uncertain**.
4. Explain the boundary: scanning runs locally. When a report is saved, the LLM audit is browser-reported; the backend recomputes classifier fields. Do not imply the backend runs the local Llama model.
5. Show a prepared deterministic test for invalid output/unavailable/timeout/quota. Label it as a CI simulation, not a live provider outage.

**Wilberr says (AI workflow):**

> “The AI helps prioritize suspicious messages and explain which text triggered the review. TF-IDF makes an initial assessment, then a local Llama judge checks a quoted span. Code validates that output, including that the quote exists in the supplied text, and TF-IDF, KRR, and LightGBM are compared. If the components disagree or a required component fails, the product can show Uncertain. This is an advisory tool, not a guarantee.”

**Wilberr says (failure behavior):**

> “These failure examples are deterministic tests, not a live provider outage. The contract returns a safe error or Uncertain state and does not claim a successful verdict.”

## Scene 7 — AI evaluation

**Time:** 8:40–9:15<br>
**Speaker:** Wilberr<br>
**Screen:** evaluation summary tied to its source SHA; keep sample size and limitation visible.

**Wilberr says:**

> “This 40-case synthetic development cohort measured 65% binary accuracy, phishing recall of 3 out of 16, or 18.75%, and a 6.25% legitimate false-positive rate. It is a regression-development set, not held-out evaluation or an approved release threshold. We need more representative held-out evaluation before making quality claims.”

Do not omit the low phishing recall or call this production accuracy.

## Scene 8 — automated test evidence

**Time:** 9:15–9:50<br>
**Speaker:** Trixia<br>
**Screen:** GitHub Actions run for the candidate SHA, backend test summary/artifact, and selected failure test group.

### Trixia’s screen actions

1. Open GitHub → `kendshhh/PhishLens` → **Actions** → open the relevant PR run.
2. Show the PR/candidate SHA and passed backend, extension, API/database checks that actually ran.
3. Open the test summary/artifact. Point out passing/failing counts and one failure-path test group. Keep the AI evaluation result distinct from ordinary unit/API tests.

**Trixia says:**

> “The automated suite covers the backend API, extension client, input validation, database behavior, and failure contracts. These green checks belong to this commit. The AI regression job is a deterministic development check; a green CI result does not approve model quality.”

## Scene 9 — mandatory DevOps workflow

**Time:** 9:50–14:30<br>
**Speaker:** Kendra<br>
**Requirement:** real branch → PR-triggered checks → actual teammate approval → merge → automatic deployment → production verification. All visible identifiers must belong to this one change.

### 9:50–10:15 — repository rules

**Click:** GitHub → `kendshhh/PhishLens` → **Settings** → **Rules** → **Rulesets** → active `main` ruleset.

Show `main` as the target, active enforcement, one required review approval, and the required status checks. Do not edit the rules.

**Kendra says:**

> “This active ruleset protects `main`. It requires a teammate approval and the listed status checks. We’ll use those controls in this exact PR; I won’t bypass them.”

### 10:15–10:50 — create the harmless test change

Use GitHub’s web editor so the PR starts from remote `main` and does not collect unrelated local files.

1. Click **Code**, set branch selector to `main`, and create `codex/video-ci-demo-YYYYMMDD` from `main`.
2. Open `backend/tests/test_health.py` → pencil icon (**Edit this file**).
3. Add a meaningful test-only assertion after the health status assertion:

   ```python
   assert response.headers["content-type"].startswith("application/json")
   ```

4. Click **Commit changes** and commit to the new branch. Do not commit to `main`; don’t use an empty `assert True` test.

### 10:50–12:05 — PR and the triggered CI run

1. Click **Compare & pull request** or **Pull requests** → **New pull request**.
2. Set base to `main`, compare to the demo branch; confirm the diff is only the test assertion.
3. Create the PR. Record its number and head SHA.
4. Open **Checks** on the PR or **Actions** → **CI**. Select the run whose event is this PR and whose SHA matches the PR head.
5. Show the real status/logs for **Extension checks**, **Migration source preflight**, **Backend checks**, **Staging integration**, and any hosted-staging checks required by the active rules. Show tests/build/package evidence from this run.

**Kendra says:**

> “This PR changes only a test. Opening it triggered CI. This is run `[RUN ID]` for PR `[PR NUMBER]`, head `[SHORT SHA]`. These checks gate this change. The hosted staging gate uses a protected environment and must be approved when required.”

If a required check is skipped or waiting, resolve it before merging. Never substitute a different PR’s passing run.

### 12:05–12:40 — actual teammate approval and merge

1. On **Files changed**, show the test-only diff.
2. A teammate clicks **Review changes** → **Approve** → **Submit review**.
3. Show the approval and all required checks green.
4. Merge using an allowed repository method. Record the merge SHA.

**Kendra says:**

> “A teammate reviewed the exact diff. The required checks passed, so GitHub enabled merge. This merge commit is `[MERGE SHA]`.”

### 12:40–14:10 — automatic Render deploy and production verification

1. Open Render Dashboard → PhishLens project → `phishlens-api` → **Settings** and **Deploys**.
2. Compare the service auto-deploy setting with the latest deployment trigger. Current evidence says auto-deploy is off but the deploy record says `new_commit`; show the discrepancy and state that the trigger policy is not verified.
3. Show the latest live source SHA, deployment status and logs. Do not claim it proves a merge-to-production auto-deploy path.
4. In another tab, open production `/version`, `/health`, `/ready` and `/model-info`. Identify the current SHA, healthy status and intentionally disabled analysis state.
5. Verify the relevant production feature with a safe read-only action. Do not create a demo record in production.
6. If you run **Production deployment smoke**, label it a manual post-deploy verification. It is not the automatic deployment trigger.

**Kendra says:**

> “The current Render metadata says production auto-deploy is off, while this deployment record says `new_commit`. We have not reconciled those settings, so I cannot claim an automatic merge-to-production path. The live version and health/readiness checks show the deployed SHA, but they do not establish product acceptance.”

Do not record this section as an automatic-deployment success until the Render
setting/event discrepancy is resolved and one exact candidate proves the
CI-to-live path. A deploy event alone is not proof of the configured policy.

### 14:10–14:30 — metrics and rollback

Show `docs/devops/metrics.md` and `docs/devops/runbook.md`; say the evidence date.

**Kendra says:**

> “Our November 14 snapshot measured a 4.58-minute median PR workflow, a 1.18-minute median main workflow, and 3.42 minutes median merge-to-live across 64 matched SHAs. We have not proven an end-to-end speed improvement, and recovery time is unknown. The runbook describes restoring a verified last-known-good Render deploy and checking version and behavior. Our recent Neon restore rehearsal changed branch topology, so clean production restore acceptance is not proven.”

## Scene 10 — separate closing clips

**Time:** 14:30–15:00 total<br>
**Recording:** each person records their own line; the editor combines them in this order. Allow about four seconds each, then ten seconds for Kendra.

- **Andrei says:** “I built the extension interface and email review flow.”
- **Leyan says:** “I connected saved-report screens to the API client.”
- **Trixia says:** “I built the backend and database persistence path.”
- **Wilberr says:** “I integrated and evaluated the AI review workflow, with its limits recorded.”
- **Kendra says:** “I built the checks and deployment process, and we’ve shown the evidence currently verified.”

Then Kendra records the final status line:

> “Our verified completion is **[X%]**. We demonstrated **[items actually shown]**. Still open are **[actual gaps]**. Thank you.”

If the team cannot evidence 90%, do not claim it. The assignment says that does not qualify as the required final submission.

## Final editor checklist

- [ ] The clips are separate recordings, assembled in the order above.
- [ ] The final export is 15:00 or shorter, with clear capture and understandable audio.
- [ ] All role names and spoken lines match the assigned speakers.
- [ ] The installed frontend’s status is accurately described; no localhost demo is presented as deployed production.
- [ ] CRUD is performed in the app against verified staging with synthetic data; the same ID is shown in Neon and cleaned up.
- [ ] The PR, CI run, approval, merge, Render deploy, and verification all use one connected change/SHA chain.
- [ ] No unrelated run, deployment, request, or data is edited to look like one continuous event.
- [ ] AI evaluation limitations and current production status are stated accurately.
- [ ] Completion percentage is team-approved and evidence-backed; at least 90% before final submission.

## Reference documents

- [Main video flow](video-flow-15-min.md)
- [Role-specific scripts](team-video-speaker-scripts.md)
- [Kendra’s click-by-click DevOps guide](kendra-video-script-click-guide.md)
- [Extension journey](extension-journey.md)
- [Saved-analysis API reference](api-reference.md)
- [Live AI workflow](ai/live-workflow.md)
- [Current DevOps status](devops/kendra-sprint-1-3-status-2026-11-14.md)

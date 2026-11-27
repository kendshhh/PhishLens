# PhishLens separately recorded video segments

> Draft recording plan. Current release evidence is **NO-GO**; production
> analysis is disabled, staging authenticated CRUD is unverified, and Render's
> reported auto-deploy setting conflicts with the latest deploy trigger. Update
> the segment and show only refreshed evidence from the
> [DevOps evidence index](devops/README.md). Do not narrate a 90%/100% score or
> automatic deployment as passed without approved scoring and exact-run proof.

Each person records only their assigned segment(s). The editor combines the clips into one final video using the timestamps below. The finished video must be no longer than 15 minutes. The speakers are assigned from the roles in `README.md`: Andrei (frontend), Leyan (full stack), Trixia (backend), Wilberr (AI), and Kendra (DevOps). Use these lines and click paths with the [15-minute run of show](video-flow-15-min.md).

## Presenter order and handoffs

| Video time | Speaker | Segment |
|---|---|---|
| 0:00–0:40 | Kendra | Project introduction and completion status |
| 0:40–3:10 | Andrei | Deployed frontend and user flow |
| 3:10–4:20 | Leyan | Frontend-to-API CRUD actions |
| 4:20–5:30 | Trixia | Backend and database persistence |
| 5:30–6:15 | Trixia | Render API and Neon schema/record |
| 6:15–6:35 | Kendra | Deployment identity and service status |
| 6:35–8:40 | Wilberr | AI workflow, output and failure behavior |
| 8:40–9:15 | Wilberr | Evaluation cases and measured results |
| 9:15–9:50 | Trixia | Automated test evidence |
| 9:50–14:30 | Kendra | Rules, PR checks, approval, merge, automatic deploy, verification |
| 14:30–15:00 | Whole team | One-line contribution and final status |

For Kendra’s detailed DevOps click paths, use the [Kendra speaker guide](kendra-video-script-click-guide.md). No one needs to be on the same call or recording session. Coordinate the synthetic record, app/package revision, and PR/run/deployment identifiers in advance so the edited clips show one coherent project state.

## How to record the separate clips

1. Record in landscape, preferably 1920×1080, with the same display scaling and browser zoom across speakers. Keep the app text readable.
2. Capture your own screen and narration only for the segments assigned to you. Do not record other presenters or leave blank time for a live handoff.
3. Start each clip with two seconds on the screen you will present, then begin speaking. At the end, pause for two seconds before stopping. The editor can trim these handles and add a brief title/transition card.
4. Speak the transition line at the end of your segment only if it helps the edit; the editor can replace it with a title card. Avoid phrases like “as you just saw” if the previous speaker’s clip may be trimmed.
5. Use synthetic data and keep private tabs, notifications, tokens, API keys, database URLs, and request bodies off screen. If a secret value becomes visible, rerecord that clip.
6. Name clips in final order, for example `01-kendra-intro.mp4`, `02-andrei-demo.mp4`, `03-leyan-crud.mp4`, `04-trixia-backend-db.mp4`, `05-kendra-service-sha.mp4`, `06-wilberr-ai.mp4`, `07-wilberr-evaluation.mp4`, `08-trixia-tests.mp4`, `09-kendra-devops.mp4`, `10-team-close.mp4`.
7. Keep each clip within its segment budget. The editor should cut pauses and repeated setup, not evidence required to show a real request, check, approval, merge, deployment, or verification.
8. For the DevOps section, agree on one PR, head SHA, CI run, reviewer approval, merge SHA, Render deployment, and production verification first. Kendra can record the pieces at different times, but the finished edit must visibly connect those same identifiers.

The suggested display and audio format is an editing convention; the hard requirements are clear screen capture, understandable audio, and a combined video at or under 15:00.

## Before the whole team records

No completion score is approved. As of November 21, production analysis is
disabled; staging authenticated CRUD is not established; and instructor
confirmation that the Chrome extension satisfies the frontend requirement is
pending. See the [current DevOps evidence index](devops/README.md) before
recording. Do not claim 90% or 100% readiness without an approved rubric and
complete current evidence.

Refresh all live evidence on recording day. Use only synthetic email/report data. Never expose secrets or write a demonstration record to production. If an observed status is unavailable or uncertain, show and explain it honestly.

## Kendra — introduction and current status (0:00–0:40)

**Screen:** title slide, then the one-line completion/evidence summary. Leave dashboards closed until the app presenters finish.

**Kendra says:**

> “Hi, I’m Kendra, the DevOps Engineer for PhishLens. PhishLens is a Chrome extension that reviews selected email text and surfaces suspicious wording. I coordinate our CI checks, protected release process, deployments, and operational evidence. Our team-verified completion is **[X%]**, measured against **[the team’s agreed checklist]**. The remaining work is **[actual open items]**.”

The repo has no approved percentage. Until the team has evidence for one, use this accurate practice/status line instead:

**Kendra says (use this if no verified percentage is ready):**

> “Our current release decision is NO-GO. The scoring rule is not approved, and we are still closing deployment and acceptance gaps.”

Do not guess a percentage in the final video. This status line means the
release/acceptance gates remain open; it is not a percentage calculation.

**Optional transition, recorded by Kendra:** “Andrei will now show the user workflow.”

## Andrei — frontend user journey (0:40–3:10)

### Open and prepare

1. Open Chrome on the prepared synthetic email page. Do not show an inbox or real email.
2. If needed to identify the package before the take, open `chrome://extensions`, find PhishLens, and open **Details**. Show its version/identity and that it targets the approved API. Return to the synthetic email tab.
3. If the instructor has not confirmed that the installed extension satisfies the “deployed website” requirement, stop here and resolve that before the final recording. An unpacked local extension is not proof of a hosted website.

### Demonstrate the scan

1. Select the full visible synthetic email.
2. Right-click and choose **Analyze selection with PhishLens**.
3. Keep the popup visible through the loading state. Point out the selected text preview so the audience sees what was analyzed.
4. When the result appears, point to the assessment, up to three visible wording observations, the recommended next action, and any partial-review warning or uncertainty shown.
5. Explain one observation by matching it to the exact words in the sample. Do not claim that the result proves the sender, link, or attachment is safe.
6. Do not click **Save report** in this part; Leyan will demonstrate explicit saving and CRUD.

If the demo machine cannot load the model, show the actual **Uncertain** or unavailable state. Do not invoke a cloud fallback or repeat scans until a preferred result appears. Have a prepared recording from the same synthetic case as a timing fallback.

**Andrei says:**

> “This message is synthetic. I select the complete visible email and choose Analyze selection with PhishLens. The extension shows the input, waits for the local review, and then gives us an advisory result with the wording it relied on. The next action is to verify through a trusted channel; this result does not authenticate the sender.”

**Optional transition, recorded by Andrei:** “Leyan will now show what happens when a user chooses to save a report.”

## Leyan — frontend-to-backend CRUD (3:10–4:20)

### Set up the browser view

Use the already verified isolated staging extension/package and synthetic report. Open the extension popup, then its DevTools before recording if you plan to show Network traffic. Use only the report created for this demo.

To inspect an extension view, open `chrome://extensions` → find PhishLens → **Details** → under **Inspect views**, open the popup or service worker view that is available. In DevTools select **Network** and clear old entries. Rehearse this before recording; if DevTools makes the popup unreliable, show the matching API contract in `docs/api-reference.md` instead.

### Click the CRUD journey

1. Show the result and the optional title field.
2. Tick the upload-consent checkbox and click **Save report**. Point to the success confirmation and saved ID if visible.
3. Open **Saved reports** and click **Load / refresh history**. Open **View details** for the new synthetic record.
4. Click **Edit notes**, change one harmless note or allowed feedback value, and save it.
5. Close/reopen the popup, load history again, and show the updated value still present.
6. Open DevTools **Network** and show only method/path/status for the relevant request: `POST /api/analyses` (create), `GET /api/analyses` or `/api/analyses/{id}` (read), `PATCH /api/analyses/{id}` (update), `DELETE /api/analyses/{id}` (delete). Do not expose request bodies or credentials.
7. Delete the synthetic record in the app and confirm it disappears after history refresh.

The save is an explicit upload of the analyzed text; a normal local scan does not save it. The history uses a shared synthetic demo identity, so do not describe it as authenticated per-user isolation.

**Leyan says:**

> “The scan stays local until I explicitly consent and choose Save report. The extension client sends the saved-report request to the API; it does not connect to Neon directly. Here we created the report, read it, changed the notes, reread after reopening, and deleted it. The Network panel shows the HTTP methods and statuses for this same synthetic record.”

**Optional transition, recorded by Leyan:** “Trixia will verify the server and database side of those same actions.”

## Trixia — backend and database (4:20–6:15)

### Show the backend API (4:20–5:00)

1. Open the current deployed backend’s `/docs` page, using the service URL displayed in Render. Do not use localhost.
2. Point out the saved-analysis routes: `POST /api/analyses`, `GET /api/analyses`, `GET /api/analyses/{id}`, `PATCH /api/analyses/{id}`, and `DELETE /api/analyses/{id}`.
3. Open Render in a separate tab if needed: workspace/project → `phishlens-api` → **Logs**. Show an appropriate short runtime excerpt from the same demo period if available; do not show request payloads.
4. Explain that the backend validates input and persists reports; `/health` only confirms the process and `/ready` only confirms database connectivity. `/ready` does not identify the Neon branch.

**Trixia says (backend):**

> “The backend is FastAPI on Render. The client calls these saved-analysis routes over HTTPS. The server validates the request and owns persistence; the browser never receives database credentials. The request statuses we just showed came from these API routes.”

### Show Neon and the record (5:00–6:15)

1. Open Neon Console → PhishLens project → **Branches** → the privately verified staging branch → database `phishlens_dev`.
2. Show the tables `users` and `analyzed_emails`, and explain the foreign key `analyzed_emails.user_id` → `users.id`.
3. In the SQL Editor/table view, show the same synthetic row using its UUID. Use a read-only query; do not insert/update/delete through SQL.
4. Ask Leyan to delete the row through the app. Refresh the read-only lookup and show no matching row.

Example query (replace the UUID; run only after verifying the staging branch):

```sql
SELECT id, user_id, subject, prediction, notes, created_at
FROM public.analyzed_emails
WHERE id = 'DEMO-REPORT-UUID'::uuid;
```

After deletion, use the same predicate with `SELECT count(*)` to show zero rows. Keep the body/email text off screen.

**Trixia says (database):**

> “This is the same ID from the application, stored in the verified staging database. The report row is linked to its user through `user_id`. After the application deletes it, the database lookup returns no matching row.”

Only say this if the row was actually observed in the verified branch. If branch identity is uncertain, stop before viewing or writing data.

**Optional transition, recorded by Trixia:** “Kendra will show how a reviewed change reaches a live version.”

## Kendra — deployment identity (6:15–6:35)

Open Render → `phishlens-api` → **Deploys**, and point to the currently live source SHA. Open `/version` in the browser to confirm the exact SHA and environment.

**Kendra says:**

> “This is the backend deployment identity. `/version` confirms the commit and environment. I’ll show the protected change-to-deploy process later in the video.”

## Wilberr — AI workflow and result (6:35–8:40)

### Show the architecture and actual result

1. Return to Andrei’s observed result, or show the relevant flow from `docs/ai/live-workflow.md`.
2. Point to the first result’s visible evidence/quote. Avoid raw model hashes and internal scores unless the rubric asks; emphasize the plain-language result.
3. Explain the actual local model sequence: TF-IDF v12a preliminary assessment → local Llama judge checks a quoted span → software validates JSON, rubric/reason consistency, and quote → TF-IDF, KRR, and LightGBM are compared.
4. Explain the release rule: only agreement with supported evidence can yield a reviewed advisory result; disagreement, missing model, or a failure can produce **Uncertain**.
5. State the boundary: scans run locally. The LLM judge is browser-reported when a report is saved; the backend recomputes its classifier fields. Do not say the backend ran the local Llama model.
6. Mention that below-threshold does not prove authenticity and unanimity does not guarantee a message is safe.

**Wilberr says (AI workflow):**

> “The AI helps prioritize suspicious messages and explain which text triggered the review. TF-IDF makes an initial assessment, then a local Llama judge checks a quoted span. Code validates that output, including that the quote exists in the supplied text, and TF-IDF, KRR, and LightGBM are compared. If the components disagree or a required component fails, the product can show Uncertain. This is an advisory tool, not a guarantee.”

### Explain failure behavior

Do not deliberately break the production provider. Show a prepared deterministic CI case for invalid output, unavailable provider, timeout, or quota response from the backend test evidence. State whether it is a test simulation or a live observation.

**Wilberr says (failure behavior):**

> “These failure examples are deterministic tests, not a live provider outage. The contract returns a safe error or Uncertain state, retains the user’s input when retry is appropriate, and does not claim a successful verdict.”

## Wilberr — evaluation results (8:40–9:15)

**Screen:** open the AI evaluation summary/artifact tied to its source SHA. Keep the sample size and limitation next to the figures.

**Wilberr says (evaluation):**

> “This 40-case synthetic development cohort measured 65% binary accuracy, phishing recall of 3 out of 16, or 18.75%, and a 6.25% legitimate false-positive rate. It is a regression-development set, not held-out evaluation or an approved release threshold. It shows why we need more representative held-out evaluation before making quality claims.”

Do not omit the low phishing recall or present this result as production accuracy.

**Optional transition, recorded by Wilberr:** “Trixia will show how our tests exercise the software contracts and failures.”

## Trixia — tests and CI evidence (9:15–9:50)

1. Open GitHub → `kendshhh/PhishLens` → **Actions** → select the exact PR workflow run for the commit being discussed.
2. Show the candidate SHA and passed backend/extension/API jobs. Open the backend test summary/artifact and point to passing counts plus at least one failure-path test group.
3. If showing evaluation output, keep it clearly separate from ordinary unit/API checks and label the model cohort’s limitations.

**Trixia says (tests):**

> “The automated suite covers the backend API, extension client, validation, database behavior, and failure contracts. These green checks belong to this commit. The AI regression job is a deterministic development check; a green CI result does not approve the model’s quality.”

**Optional transition, recorded by Trixia:** “Kendra will now show the protected release path.”

## Separately recorded closing lines (14:30–15:00 total)

Each person records their own short closing clip. The editor places these clips back-to-back in this order, then ends on Kendra’s status line. Keep each contribution to about four seconds and Kendra’s final line to about ten seconds.

- **Andrei:** “I built the extension interface and the email review flow.”
- **Leyan:** “I connected the saved-report screens to the API client.”
- **Trixia:** “I built the backend and database persistence path.”
- **Wilberr:** “I integrated and evaluated the AI review workflow, with its limits recorded.”
- **Kendra:** “I built the checks and deployment process, and we’ve shown the evidence that is currently verified.”

**Kendra says (final status):**

> “Our verified completion is **[X%]**. We demonstrated **[items actually shown]**. The work still open is **[items actually open]**. Thank you.”

If the team cannot evidence 90%, do not claim it. The video may be useful as a progress review, but the assignment states that a qualifying final submission needs at least 90% completion.

## Source references

- [Extension journey](extension-journey.md)
- [Saved-analysis API reference](api-reference.md)
- [Architecture](architecture.md)
- [Live AI workflow](ai/live-workflow.md)
- [DevOps status](devops/kendra-sprint-1-3-status-2026-11-14.md)
- [Kendra’s DevOps click-by-click guide](kendra-video-script-click-guide.md)

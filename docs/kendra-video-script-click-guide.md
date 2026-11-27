# Kendra’s video script and click guide

This is the DevOps Engineer’s portion of the 15-minute PhishLens video. It follows the team roles in `README.md`. The timings match [the full video flow](video-flow-15-min.md).

> Current evidence cutoff: November 21, 2026. Release is **NO-GO**. Production
> analysis is disabled; staging requires Bearer authentication for saved
> reports; the patched anonymous smoke passed locally but authenticated hosted
> CRUD is still open. Render reports auto-deploy off while the latest production
> deploy record says `new_commit`. Do not present automatic deployment as
> verified until that conflict is resolved. See the
> [DevOps evidence index](devops/README.md).

## Before you record

Do not execute the merge/deployment demo while the release is NO-GO or required
checks, authenticated staging CRUD, and the Render deployment policy remain
unverified. Refresh the live evidence and get owner approval first.

The current checkout has uncommitted edits and nested worktree folders. Keep the video-demo change separate so you do not accidentally include unrelated files. The safest way for this small test-only change is GitHub’s web editor on a new branch.

There are submission and release gaps to resolve first:

1. The repo does not have approved weights/scoring rules or a team-approved completion percentage. Don’t guess a number or report 90%/100%.
2. The documented frontend is a Chrome extension; the repo does not document a hosted website frontend or frontend hosting dashboard. Ask whether the installed production-targeted extension qualifies. If the rubric strictly requires a website, the project needs that frontend before this can pass.

The current production `/model-info` says `analysis_enabled=false` and
`provider_mode=disabled`; the production observer has not been run for this
audit. The supplied staging smoke failure is explained by anonymous Neon Auth,
and current hosted authenticated CRUD is not established. Refresh the exact
candidate evidence before claiming AI or persistence works.

## Your speaking times

| Video time | Your part | Target |
|---|---|---:|
| 0:00–0:40 | Introduce the project, your role, completion, remaining work | 40 sec |
| 6:15–6:35 | Confirm the Render deployment identity | 20 sec |
| 9:50–14:30 | Show the real code-change-to-deployment workflow | 4 min 40 sec |
| 14:30–15:00 | Summarize verified status | 30 sec |

## Part 1 — opening and completion (0:00–0:40)

### What to have open

- A simple title slide: **PhishLens — AI-assisted phishing email review**.
- The team’s agreed completion checklist and percentage, with the evidence for each completed item.
- Avoid opening dashboards or private email before screen sharing begins.

### Kendra says

> “Hi, I’m Kendra, the DevOps Engineer for PhishLens. PhishLens is a Chrome extension that analyzes selected email text and explains suspicious wording. I’m responsible for our CI checks, protected release process, deployment, and operational evidence. Our team-verified completion is **[X%]**, based on **[briefly name the checklist or calculation]**. The remaining work is **[name only the real open items]**.”

Fill in `[X%]` only after the team has calculated and can defend it. Based on the repo evidence currently available, you should say:

> “Our latest repository audit does not yet verify the required 90% completion level. We are closing the current deployment and acceptance gaps before calling this final.”

That is an honest status update, but it also means the video is not yet ready to submit as a qualifying final check.

## Part 2 — confirm deployment identity (6:15–6:35)

Trixia leads the longer Render and Neon walkthrough in the [team script](team-video-speaker-scripts.md). For your 20-second contribution, open `/version` in the browser using the current production API URL shown by Render and confirm the SHA/environment match the deployment Trixia just showed.

**Kendra says:**

> “This is the backend deployment identity. `/version` confirms the commit and environment. I’ll show how a reviewed change reaches this live version in the DevOps walkthrough.”

Do not call the API dashboard the frontend hosting dashboard. The repo documents a Chrome extension frontend and no separate website-hosting dashboard. If the instructor strictly requires a hosted website, resolve that before recording.

## Part 3 — mandatory DevOps change to production (9:50–14:30)

The assignment requires a real new branch, a PR-triggered workflow, teammate approval, merge, automatic deployment, and production verification. Arrange the teammate review and protected staging approval before recording. Capture clips across the actual run if it takes hours, then trim waiting time in editing. Every clip must show identifiers from the *same* PR/run/deploy.

### A. Show the repository rules (about 25 seconds)

**Clicks:** GitHub → `kendshhh/PhishLens` → **Settings** → left sidebar **Rules** → **Rulesets** → open the active `main` ruleset. If Settings is hidden, open the repository-header dropdown first. GitHub’s documented path is Settings → Rulesets under “Code, planning, and automation.” [GitHub ruleset docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/managing-rulesets-for-a-repository).

Point to:

- Target branch: `main`.
- Active/enforced state.
- Required pull-request review: one approval.
- Required status checks (the live ruleset is authoritative; the repo snapshot says ten).
- No direct push/merge before those conditions pass.

**Kendra says:**

> “This active ruleset protects `main`. It requires a teammate approval and the listed status checks. We’ll use those controls in this exact PR; I won’t bypass them.”

Do not edit or disable the ruleset for the demo.

### B. Create the harmless test-only change (about 35 seconds)

Use the GitHub web editor so this demo branch starts from remote `main` and does not pick up local uncommitted work.

1. Click **Code** and make sure the branch selector says `main`.
2. Use the branch selector to create a new branch, for example `codex/video-ci-demo-20261116`, based on `main`.
3. Open `backend/tests/test_health.py`.
4. Click the pencil (**Edit this file**). Add one useful assertion to the existing `test_health` test, for example after the status assertion:

   ```python
   assert response.headers["content-type"].startswith("application/json")
   ```

5. Click **Commit changes**, enter a message such as `test: assert health response content type`, and commit to the new branch.

This adds no application behavior; it strengthens an existing endpoint test. Do not create an empty `assert True` test. Do not use “Commit directly to main.”

### C. Open the PR and show the triggered workflow (about 75 seconds, waiting time may be cut)

1. Click **Compare & pull request** (or **Pull requests** → **New pull request**).
2. Set **base** to `main` and **compare** to the demo branch. Check that the diff contains only the test assertion.
3. Use a title such as `test: strengthen health response assertion for CI demo`; create the PR.
4. On the PR page, note the PR number and head SHA. Click **Checks** or **Details** beside the checks summary.
5. Open **Actions** in the repository, select the `CI` workflow, then open the run whose event is this PR and whose SHA matches the PR head.
6. Show the job list/log summaries for **Extension checks**, **Migration source preflight**, **Backend checks**, **Staging integration**, and any hosted-staging jobs that the active rules require. Show the passing test/build evidence and package artifact if produced.

The checked-in CI workflow triggers on `pull_request` and on `push` to `main`. The workflow file is [`/.github/workflows/ci.yml`](https://github.com/kendshhh/PhishLens/blob/main/.github/workflows/ci.yml). If a required staging job is skipped or waiting for approval, obtain the configured approval or resolve the environment setup before merging. Do not splice in a passing result from another PR.

**Kendra says:**

> “This PR changed only a test. Opening it triggered the repository CI. We’re looking at run `[RUN ID]` for PR `[PR NUMBER]`, head `[SHORT SHA]`. These are the checks that gate this change; the hosted staging gate uses a protected environment and must be approved when required.”

If the workflow does not trigger, stop the recording and fix the trigger/configuration first.

### D. Get real teammate approval and merge (about 35 seconds)

1. On the PR, click **Files changed** and show the one-line test change.
2. Have a teammate open **Review changes** → **Approve** → **Submit review**. The reviewer must be an actual teammate; do not approve your own PR or stage a simulated approval.
3. Return to **Conversation** and show the approval and all required checks green.
4. Click the enabled merge control and use the merge method allowed by the repository. Confirm merge.
5. Record the resulting merge commit SHA.

**Kendra says:**

> “A teammate reviewed the exact diff. The required checks passed, so GitHub enabled merge. This merge commit is `[MERGE SHA]`.”

### E. Show Render’s deployment setting, event and live identity (about 90 seconds)

1. Open the Render Dashboard → PhishLens workspace/project → **`phishlens-api`** → **Settings** and **Deploys**.
2. Compare the auto-deploy setting and latest deployment trigger. Current evidence reports `off` and `new_commit`, respectively; state that the policy is unresolved.
3. Show the latest live source SHA, status and logs. Do not claim automatic deployment or a same-PR release based only on the trigger label.
4. In another tab, open `/version`, `/health`, `/ready` and `/model-info`. Identify the SHA, healthy status and intentionally disabled production analysis.
5. Reopen the actual production-targeted application and perform a safe read-only action or verify the relevant feature. Do not create a production demo record.
6. If you run **Production deployment smoke** after deploy, identify it as a manual post-deploy verification. The repository documents that it is manually dispatched; it is not the automatic deployment trigger.

**Kendra says:**

> “Render currently reports production auto-deploy off, while this deployment record reports a `new_commit` trigger. That discrepancy is unresolved, so I cannot claim the automatic path has passed. The live version, health, and readiness checks identify service state; they do not prove feature acceptance.”

Render’s Deploys page contains deploy history and per-deploy logs; **Settings** contains auto-deploy configuration; **Environment** contains runtime variables. [Render deploy docs](https://render.com/docs/deploys).

### F. One concise performance and rollback explanation (about 20 seconds)

Show `docs/devops/metrics.md` and `docs/devops/runbook.md` in GitHub. These are dated evidence; say the date and refresh the snapshot if recording later.

**Kendra says:**

> “Our November 14 28-day snapshot measured a 4.58-minute median PR workflow, a 1.18-minute median main workflow, and a 3.42-minute median merge-to-live time across 64 matched SHAs. The PR mean is much higher because protected staging waits can be long. We haven’t proven an end-to-end speed improvement, and recovery time is unknown. The runbook’s rollback is to select a verified last-known-good Render deploy, verify version and behavior, then check Auto-Deploy. The recent Neon restore rehearsal changed branch topology, so we do not claim clean production restore acceptance.”

If the 4:40 segment is over time, cut explanatory pauses—not the approval, actual run identity, deployment result, or production verification.

## Part 4 — closing (14:30–15:00)

### Kendra says

> “Our verified completion is `[X%]`. We demonstrated `[list only items shown in this video]`. Still open are `[list actual gaps]`. Production service health, AI inference, database writes, and automated deployment are separate checks, and we are only calling each one complete where this recording shows current evidence. Thank you.”

If not all three components were verified, say so explicitly. The recorded repo snapshot currently does not support claiming 90% or completed production AI acceptance.

## Final checklist for your segment

- [ ] Team-approved completion percentage and evidence ready; at least 90% is actually supportable.
- [ ] Instructor has confirmed whether the Chrome extension satisfies “deployed website,” or a hosted website frontend exists.
- [ ] Render production and staging service identity, latest SHA, and logs refreshed.
- [ ] Render-to-Neon staging mapping privately verified before CRUD.
- [ ] Synthetic CRUD record ID supplied by the app presenter; created, updated, reread, deleted, and absent afterward.
- [ ] New test branch, PR, run ID, head SHA, real approval, merge SHA, Render deploy, and production verification all refer to one chain.
- [ ] Auto-deploy is shown as automatic; any manual post-deploy smoke is labelled manual.
- [ ] No secrets, real emails, production writes, unrelated runs, or local-only demo are shown.
- [ ] Total edit is at most 15:00; your segment ends by 14:30.

## References

- [Full 15-minute video flow](video-flow-15-min.md)
- [Repository pipeline status](../PIPELINE.md)
- [Pipeline metrics](devops/metrics.md)
- [Deployment and recovery runbook](devops/runbook.md)
- [Staging identity and environment guidance](devops/staging.md)
- [GitHub rulesets guide](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/managing-rulesets-for-a-repository)
- [GitHub pull request guide](https://docs.github.com/en/pull-requests/get-started/about-pull-requests)
- [Render deploys](https://render.com/docs/deploys), [logs](https://render.com/docs/logging), and [environment variables](https://render.com/docs/configure-environment-variables)

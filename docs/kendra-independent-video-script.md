# Kendra's independent PhishLens DevOps video segment

**Presenter:** Kendra only<br>
**Target clip length:** about 4 minutes 30 seconds<br>
**Use:** Kendra records this role-specific clip independently. The editor combines it with the other members' separate clips; the final team video must stay at or below 15 minutes.

This is Kendra's DevOps Engineer portion. It covers repository controls, CI/CD
configuration, a test-only pull request, teammate approval, current Render
deployment evidence and limitations, production verification, metrics,
environment-variable handling, and rollback. As of November 21, Render reports
production auto-deploy off while the latest deploy record says `new_commit`;
the automatic-deployment path is unresolved and must not be narrated as passed.
Other members can cover the app walkthrough, database CRUD, AI feature, and tests
in their own clips.

## Before you record

- Confirm the current repository is `kendshhh/PhishLens` and refresh the rules, checks, and deployment status on recording day.
- Use a fresh branch from `main` named `codex/video-ci-demo-YYYYMMDD`. Use the actual date in place of `YYYYMMDD`.
- The demo change is test-only. In `backend/tests/test_health.py`, add `assert response.headers["content-type"].startswith("application/json")` after the existing HTTP 200 assertion.
- Open the pull request as a draft, add the `needs-hosted-staging` label, then click **Ready for review**. The current workflow listens for `ready_for_review`; adding the label alone does not start a new CI run.
- Use the checks, approval, merge, and deployment from this same pull request and commit chain. Do not use a different PR's green run.
- Ask a teammate to submit the required approval. Kendra narrates; the teammate does not need to speak.
- Use the verified staging target for staging checks. Do not create demo data in production. Never show secret values.
- Review the [current DevOps evidence index](devops/README.md) and refresh the
  metrics. The Nov 21 service identity refresh is not a new performance sample.
- Do not narrate automatic deployment as verified until the current Render
  auto-deploy setting and deployment trigger have been reconciled.

## Clip outline

| Clip time | What appears on screen | Kendra's task |
|---|---|---|
| 0:00-0:20 | Title, then GitHub repository | Introduce your role and the release path |
| 0:20-0:50 | Active ruleset and CI workflow | Show approval, required checks, triggers, and stages |
| 0:50-1:20 | New branch and test file diff | Create the harmless test-only change |
| 1:20-2:25 | Draft PR, label, CI run, teammate review | Trigger and show checks, then receive a real approval |
| 2:25-3:35 | Merge and Render Deploys | Show the same SHA deployed automatically and verify production |
| 3:35-4:30 | Variables, metrics, runbook, closing slide | Explain secrets, performance evidence, rollback, and remaining limits |

---

## 0:00-0:20 - Introduce your DevOps role

**Screen:** A simple title slide: “PhishLens DevOps workflow.” Show your name and role: Kendra, DevOps Engineer.

**Kendra says:**

> “Hi, I’m Kendra, the DevOps Engineer for PhishLens. In my clip I’ll show our protected review process, the CI checks for one new test change, and how the approved merge reaches Render automatically.”

**Clicks:** Start on the repository `kendshhh/PhishLens` in GitHub. Keep the address bar visible briefly so the repository is clear.

## 0:20-0:50 - Show the repository rules and pipeline configuration

**Clicks:**

1. GitHub repository -> **Settings** -> **Rules** -> **Rulesets** -> open the active ruleset targeting `main`.
2. Show that pull requests require an approval and unresolved review threads must be addressed. Do not change the rules.
3. Return to **Code** -> `.github` -> `workflows` -> `ci.yml`.
4. Show the `pull_request` trigger and the `push` trigger for `main`. Briefly point to the Extension, migration, Backend, Staging, Hosted staging, security, and evaluation jobs.

**Kendra says:**

> “Changes reach `main` through a pull request. The active ruleset requires a teammate's approval. The PR must also pass its required checks before it can merge. Our CI runs for pull requests and for pushes to `main`. It checks the extension, migration source, backend, staging, security, and AI evaluation. The hosted staging gate needs the `needs-hosted-staging` label.”

## 0:50-1:20 - Create a harmless test-only branch

**Clicks:**

1. Open **Code**. Use the branch selector to create `codex/video-ci-demo-YYYYMMDD` from `main`.
2. Open `backend/tests/test_health.py` and choose the pencil icon to edit it.
3. Immediately after `assert response.status_code == 200`, add:

   ```python
   assert response.headers["content-type"].startswith("application/json")
   ```

4. Commit the change to the new `codex/` branch. Show that the diff changes only this assertion.

**Kendra says:**

> “This is a test-only change. It checks that the health endpoint returns JSON, and it does not change application behavior. I committed it to a new branch from `main`.”

## 1:20-2:25 - Open the pull request and show the real CI run

**Clicks:**

1. Choose **Pull requests** -> **New pull request**. Set base to `main` and compare to your `codex/video-ci-demo-YYYYMMDD` branch.
2. Select **Create draft pull request**. Confirm the displayed diff has only the test assertion.
3. Add the `needs-hosted-staging` label, then click **Ready for review**. This event starts the workflow with the hosted staging gate enabled.
4. Record the pull request number and head SHA. Open **Checks** and show the checks for that same SHA.
5. Keep the same run visible while the checks finish. If the video is edited to shorten waiting, retain the same PR number, SHA, run, and final result.
6. Ask a teammate to open **Files changed** -> **Review changes** -> **Approve** -> **Submit review**. Show the submitted approval and green required checks.

**Kendra says:**

> “Making the draft ready starts the pull-request workflow. The run shown here belongs to this PR and this exact commit. The teammate approval and required checks are the merge gate. The hosted staging job is part of the same workflow because this PR carries the staging label.”

**If Hosted staging is skipped or pending:** Do not merge. Check the run summary and confirm the label was present when that run started. If the run started before the label was added, reopen the PR or push a new commit. If the check skips again, inspect the staging environment gates with the repository owner. Keep the new run tied to the same test change.

## 2:25-3:35 - Merge and verify automatic Render deployment

**Clicks:**

1. Once the teammate approval and all required checks are green, merge the PR using the allowed **Squash and merge** method.
2. Record the merge SHA.
3. Render Dashboard -> PhishLens project -> `phishlens-api` -> **Deploys**.
4. Open the deployment triggered by that merge. Show the source SHA matches the merge SHA, the automatic trigger, **Live** status, and a short deployment log excerpt.
5. Open the production API's `/version`, `/health`, and `/ready` endpoints. Show the deployed version and current health/readiness. Do not create a production demo record.

**Kendra says:**

> “Render metadata currently reports auto-deploy off, while this deployment record reports a `new_commit` trigger. That discrepancy is unresolved, so we are not claiming the automatic path has passed. This live version, health, and readiness check identifies the deployment; it does not establish feature acceptance.”

Do not record this as an automatic-deployment success until the service setting
and event have been reconciled and a same-commit merge-to-live run is proven.

## 3:35-4:30 - Show environments, metrics, and rollback

**Clicks:**

1. GitHub repository -> **Settings** -> **Environments** -> show the staging environment and any protection or approval gate.
2. Render -> `phishlens-api` -> **Settings** -> **Environment**. Show variable names or masked values only; do not reveal or copy secrets.
3. Open `docs/devops/metrics.md` and `docs/devops/runbook.md`. Point to the current metrics date and the rollback steps.

**Kendra says:**

> “Staging and production are separate environments. Secrets are stored in GitHub or Render environment settings and remain masked here. Our Nov 14 snapshot measured a 4.58-minute median pull-request workflow, a 1.18-minute median main workflow, and a 3.42-minute median merge-to-live time across 64 matched SHAs. We have not proved an end-to-end speed improvement, and recovery time is still unknown. The runbook restores a verified last-known-good Render deployment, then checks the deployed version and behavior. Thank you.”

Refresh these figures if the repository's latest metrics document has newer numbers. If you cannot verify the rollback or restoration evidence, describe the runbook steps and state what remains unverified.

## Final checklist for Kendra's clip

- [ ] Kendra is the only narrator in this clip.
- [ ] The clip is about 4:30; the combined team video is no longer than 15:00.
- [ ] The branch starts from `main`, and the PR changes only the health-test assertion.
- [ ] The PR, CI run, teammate approval, merge SHA, Render deployment, and production verification are one continuous chain.
- [ ] The staging label is present and the Hosted staging result is successful before merge.
- [ ] No branch protection is disabled to make the clip pass; required controls remain visible.
- [ ] No secrets, real email, or production test record appear on screen.
- [ ] Current rules, status, metrics, and deployment are refreshed before recording.

## Note about the screenshot PR

This is a recording note for Kendra, not spoken narration. The screenshot is PR #156, an existing 22-commit feature PR from another team member. Its **Update branch** action is blocked because its head branch is protected. That action is separate from the missing Hosted staging result. The active rulesets I checked have no bypass actors and report `current_user_can_bypass: never`. I did not disable protection. Reopening PR #156 started a new CI run: Staging integration succeeded, but Hosted staging preflight and Hosted staging were skipped again. Do not merge it with the required staging check skipped. The workflow also gates those jobs on repository variables `SECRETARY_PREVIEW_ENABLED` and `SECRETARY_REPLACES_LEGACY_STAGING`; the owner should confirm the settings. Use a fresh test-only PR for Kendra's assignment demonstration, and do not present PR #156 as that test-only change.

# Contributing to PhishLens

This document explains our team's collaboration workflow.
Instructor requirements remain the main authority:
https://csp221a.vercel.app/

## Team Responsibilities

| Member | Primary Ownership | Reviewer |
|---|---|---|
| Kendra | Git workflow, CI/CD, deployment, configuration and evidence | Leyan |
| Wilberr | AI model integration, inference and evaluation | Trixia |
| Trixia | Backend foundation, database models and migrations | Leyan |
| Leyan | Saved-history API/UI integration and API contract | Trixia and Andrei |
| Andrei | Chrome extension interface and user-facing states | Leyan |

Coordinate before editing another member's components.
Agree on one editor at a time for shared files.

Trixia owns database infrastructure and backend route registration.
Leyan uses that infrastructure for the history API and frontend client.
Andrei and Leyan agree on UI element IDs before integration.

## Issues and Branches

Every task should have a GitHub issue containing:
- One assigned owner.
- A clear goal.
- Acceptance criteria.
- Dependencies.
- Verification evidence.

Use one task branch per issue, created from updated main.
We do not use a separate integration branch during Week 1.

Branch format:
type/issue-number-short-description

Examples:
- chore/1-repository-setup
- feat/2-database-schema
- fix/3-history-error-state

## Starting a Task

Run these commands in the repository's PowerShell terminal.
First ensure you have no unfinished changes from another task.

    git switch main
    git pull --ff-only origin main
    git switch -c feat/2-database-schema

Replace the example branch with your actual task branch.

## Commits

Make focused, meaningful commits.
Do not create unnecessary commits to increase contribution counts.

Before committing:

    git status
    git diff
    git add path/to/changed-file
    git diff --cached
    git commit -m "feat: describe the completed change"

Replace the file path and commit message with your actual changes.
Stage specific files to avoid including unrelated or private files.

Publish your branch:

    git push -u origin your-branch-name

Use your actual branch name.

## Pull Requests and Reviews

1. Open a pull request with main as the base.
2. Link the issue using Closes # followed by its actual number.
3. Explain what changed and why.
4. Include verification steps and results.
5. State limitations or incomplete work honestly.
6. Request review from at least one teammate.
7. Address feedback and pass applicable checks before merging.

Authors must understand and explain their submitted code,
including code prepared with AI assistance.

Kendra coordinates workflow and configuration merges.
Leyan coordinates application merges.
Both need another teammate's approval for their own pull requests.

Do not push normal task work directly to main.
Do not force-push main or bypass checks to hide failures.

## Verification and Completion

Application setup and CI are still being implemented.
Do not claim checks passed when they do not exist yet.

Add verified installation, launch, migration and check commands
to README as components become available.

Our target Definition of Done is:
- Acceptance criteria satisfied.
- Pull request reviewed and merged.
- Applicable pipeline checks passed.
- Changes deployed and verified.
- Issue and documentation updated.

Record missing CI or deployment explicitly.
Local success alone does not prove deployed success.

## After a Merge

Update your local main:

    git switch main
    git pull --ff-only origin main
    git fetch --prune

Delete completed task branches only after confirming that their
pull requests are merged and no unique work remains.

## Conflicts and Mistakes

If main changes while you work, commit your task changes first,
then update your task branch:

    git fetch origin
    git merge origin/main

Resolve conflicts with the affected teammate.
Read both changes and repeat relevant checks.

To stop an unfinished merge:

    git merge --abort

To unstage a file without deleting its edits:

    git restore --staged path/to/file

Fix already-merged mistakes through a reviewed repair pull request.
Avoid rewriting shared history.

## Secrets and Data

- Never commit actual credentials or private .env files.
- Keep .env.example limited to configuration placeholders.
- Never include database credentials or backend secrets in the extension.
- Chrome extensions do not automatically load .env files.
- Use synthetic emails for tracked examples and demonstrations.
- Keep private datasets and downloaded model files out of Git.
- If a secret leaks, revoke or rotate it first, then coordinate cleanup.
- Deleting a file does not remove it from Git history.

## Progress Evidence

Keep issues and the project board updated.
Record two to three standups per sprint: done, next and blocked.
Maintain a sprint plan and a short retrospective.
Link relevant pull requests, checks and deployments.

There is no commit-count quota.
Show meaningful ownership, useful reviews, steady progress
and understanding of your work.
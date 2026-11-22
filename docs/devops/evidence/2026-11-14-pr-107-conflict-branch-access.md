# PR 107 conflict branch access — 2026-11-14

PR [#107](https://github.com/kendshhh/PhishLens/pull/107) targets `main` from
`feat/96-bounded-inference`. GitHub reported the PR as `dirty` with a merge
conflict. The head branch had an exact-name protection rule requiring a pull
request review, which prevented direct conflict-resolution updates.

## Change made in GitHub

The `required_pull_request_reviews` setting was removed from the exact rule for
`feat/96-bounded-inference`. The rule still requires these checks, strictly and
from the GitHub Actions app:

- Backend checks
- Extension checks
- Hosted staging
- Staging integration

Administrator enforcement and conversation resolution remain enabled. Force
pushes and deletion remain disabled. The protection on `main` was not changed;
it still requires one approval and its six configured status checks.

## Scope and follow-up

`xxTrixia` already has write access to the repository. Because this is a
personal-account repository, GitHub does not support a named-user bypass for
this branch protection rule. While the review requirement is removed, any
repository writer can push to this one branch, subject to its required checks.

xxTrixia reports resolving the conflict locally in merge commit
`d0c91962da60d3ceb5b08574af25b1915941dbf2`, preserving the migration assertion
in `scripts/tests/test_migration_lineage.py`. GitHub rejected the direct push
because the four required checks were still expected. The commit has not been
verified or observed on the remote branch. The protected-update path is a small
follow-up PR targeting `feat/96-bounded-inference`, with the merge commit on a
separate head branch. Merge it with GitHub's merge-commit method after the
required checks pass so the merge ancestry is retained; the repository allows
that method. PR #107 should then update from the protected feature branch.
Restore its one-approval review requirement after that update. PR #107 remains
conflicted until then.

Since the head branch remains protected by its status checks, GitHub's web
conflict editor may still require creating a replacement head branch; resolving
locally and proposing that commit through a follow-up PR is the protected path.

This file records the live GitHub setting; it does not apply or enforce the
setting. Branch protection is managed in GitHub repository settings.

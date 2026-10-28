# Automatic issue and PR labels

The Automatic labels workflow runs when an issue or PR is opened, edited or reopened, and when a PR receives commits or becomes ready for review. It includes drafts and fork PRs.

It adds existing repository labels using:
- Conventional title prefixes: fix → bug; docs → documentation; feat/ci/chore/test/refactor/perf/build → enhancement.
- Component keywords in titles and changed PR file paths → area labels.
- Explicit Sprint 1/2 or S1/S2 markers → sprint labels.
- Explicit priority:P0 or priority:P1 declarations → priority labels.
- Explicit same-repository issue relationships (Closes #42, Related to #42, or full issue URLs) → inherited area and sprint labels.

Existing labels are preserved. Generic titles default to enhancement; clear titles and linked issues improve classification. The labeler does not infer completion, review, carryover, or urgency. It does not scan arbitrary checklist prose for component labels, create new labels, or remove stale labels after scope changes. Maintainers can adjust labels manually.

Only trusted default-branch code runs with the repository token; PR code is never checked out or executed. Dependabot pull request events are skipped because their token is read-only. If repository or organization policy denies API access with HTTP 403, the labeler warns and skips without blocking CI. No external AI provider or extra secret is required.

Run the rule tests with:
    node --test scripts/tests/auto_labels.test.mjs

Activation requires merging the workflow, script and tests into the default branch through normal review and checks.

# Pipeline optimization evidence

## Secretary pilot candidates — not measured improvements

Duplicate-event fingerprints avoid repeated report writes and AI calls for
unchanged evidence. Optional AI is capped per invocation; shared staging avoids
per-PR service creation. These are implementation choices, not measured speed or
cost gains. Compare equivalent PRs with the same tests, runner, model and preview
settings; record workflow/run links, cache state, queue time, AI call counts and
deployment count before claiming a gain. No before/after result is available yet.

## Baseline

The measured snapshot through readiness merge 2a70ad3 has 16 PR backend jobs
averaging 25.94 seconds and 7 main backend jobs averaging 32.14 seconds.
Earlier runs lacked database checks; do not use the full-history average as a
like-for-like optimization baseline. Exact records are in ci-run-evidence.csv.

## Candidate: pip download cache

Status: proposed in a separate CI PR; improvement not measured.

- Use setup-python's pip cache, keyed by both pinned runtime/development files.
- Dependency installation, lint, migrations, seed and tests still run every time.
- Cache stores downloaded packages, not a substitute for installation or tests.
- Record the first cold-cache run separately from later cache-hit runs.
- Compare runs with the same test/schema coverage and Python/runner settings.
- Record setup/cache overhead as well as install and total job durations.
- Do not claim a gain if saved download time is offset by cache overhead.
- The Action runtime upgrade accompanies maintenance; isolate its contribution
  before attributing all changes to caching.

| Sample | Commit/run link | Cache hit | Setup seconds | Install seconds | Job seconds |
|---|---|---|---|---|---|
| Comparable baseline | Pending selection | No cache configured | Pending | Pending | Pending |
| Cold cache | Pending CI PR run | Pending | Pending | Pending | Pending |
| Warm cache | Pending subsequent run | Pending | Pending | Pending | Pending |

Source: https://github.com/actions/setup-python#caching-packages-dependencies

# Pipeline optimization evidence

## October 21 measured staging-cache experiment

[Raw comparable job/step timestamps](evidence/2026-10-21-cache-comparison.json).
Two no-cache samples: CI 39452635709 / 39453199728. Two cached samples:
39453836118 / 39454875889. Each ran the same backend/client smoke and 52 deployment
guard tests. Backend, extension and guard-test Git trees are identical; locks,
Python 3.12.15 and ubuntu-26.04 image 20261012.163.1 are unchanged. The first
cached run used a fallback cache and saved the exact runtime-lock key; the second
restored that exact key. Installation and all checks still run.

| Measure | Before (n=2) | Cached (n=2) |
|---|---:|---:|
| Runtime install | 9.0 s | 7.0 s |
| Python setup + install + cleanup | 9.5 s | 9.0 s |
| Whole staging job | 40.5 s | 44.0 s |

Runtime installation averaged 2 seconds lower (22.2%), but the 0.5-second net
dependency-path difference is within timestamp resolution/runner variation.
Whole-job average increased 3.5 seconds. This is **not an established end-to-end
pipeline improvement**; #40 remains open. The cache is a bounded download reuse
change, not justification to skip checks. Collect further equivalent samples
before claiming a total-job gain or removing/retuning it.

An earlier combined backend-install candidate took 13 seconds versus the
11-second baseline installation sum and was reverted. No dependency pins,
migration coverage or tests were removed to manufacture a speed gain.

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

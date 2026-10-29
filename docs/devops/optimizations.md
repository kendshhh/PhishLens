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

## October 28 Extension checks cache trial

The no-cache comparison uses the two latest comparable PR runs before the npm
cache change. Both used `ubuntu-latest`, the same `package-lock.json`, the same
Extension checks steps, and passed.

| Run | Extension job | `npm ci` step | Cache |
|---|---:|---:|---|
| [PR #83 run 40635217771](https://github.com/kendshhh/PhishLens/actions/runs/40635217771) | 11 s | 1 s | No cache |
| [PR #84 run 40635212213](https://github.com/kendshhh/PhishLens/actions/runs/40635212213) | 11 s | 2 s | No cache |

The observed baseline is 11 seconds per job and 1.5 seconds for `npm ci` at
one-second timestamp resolution. It is a small, noisy target. This is not an
optimization result. A one-cold/one-warm cache trial retained `npm ci` and every
check, then the cache and instrumentation were removed when no whole-job gain
was demonstrated.

| Sample | Commit/run | Cache hit | `npm ci` | Extension job |
|---|---|---|---:|---:|
| Cold | [`2606588`, run 40638816002](https://github.com/kendshhh/PhishLens/actions/runs/40638816002) | No | 1 s | 11 s |
| Warm | [`6c9f82e`, run 40639539541](https://github.com/kendshhh/PhishLens/actions/runs/40639539541) | Yes | 1 s | 18 s |

Both cache trial runs passed every Extension checks step, including lint, tests,
manifest validation, packaging, and package identity. The warm sample had a
cache hit but did not shorten `npm ci` and the job took 18 seconds. With one
run per state and substantial timing noise at this duration, the comparison
does not establish a gain; the cache and its instrumentation were removed.
The PR's first
Staging integration attempt also exposed workflow-contract mismatches in the
Secretary/dependency-review files; the follow-up commit includes the corresponding
deployment-lock, event-scope, and reporting adjustments. Do not attribute that fix
to npm caching.

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

## Existing pip download cache

The setup-python pip cache is enabled on main. Its October 21 comparison above
showed lower install time but no end-to-end job improvement; do not describe it as
a measured pipeline speedup.

Source: https://github.com/actions/setup-python#caching-packages-dependencies

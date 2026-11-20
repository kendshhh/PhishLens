# Approved deterministic AI regression policy

AI owner: EnviousCoal. Policy recorded November 15 and reconciled November 18,
2026. [Owner decision in #93](https://github.com/kendshhh/PhishLens/issues/93#issuecomment-6891138424).

The ordinary PR gate requires the reviewed contract inventory to pass exactly
once, with zero missing, extra, duplicated, failed, errored or skipped tests.
The explicit inventory is in `scripts/ai-regression-baseline.json`. It contains
114 tests across the 94 original contracts, the saved-report timeout contract,
eight evidence-guard tests, and 11 bounded provider-smoke controller tests.
Controller tests substitute every HTTP response and make no staging or provider
request.
Pytest subtests are reported separately and are not additional inventory items.

All 40 `synthetic-v1` development cases must complete with valid outputs, zero
errors and zero external provider calls. The reviewed case hash is
`a755533aa841bc695574196b3147f2c3b408129872a62204c1f4c5f149ab226f`.
Both the bundled and evaluated TF-IDF model must match
`a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`.
The guard consumes the JUnit and benchmark artifacts produced by the existing
workflow. It does not run a provider, download weights or access a database.

This policy approves complete execution and contract checks. Development recall
and false positives remain diagnostic; no numeric model-quality threshold is
applied to these development fixtures. Held-out evaluation and hosted acceptance
remain separate evidence. The actual-mail thresholds and scoped historical result
are recorded in [#92](https://github.com/kendshhh/PhishLens/issues/92#issuecomment-6891137984).

## Verification

Run the eight paths in the baseline's `test_paths` list with Python 3.12 and
`backend/requirements-dev.txt`, with `AI_MODE=mock`, saving JUnit XML. Then:

```powershell
$env:AI_MODE = 'tfidf'
python scripts/benchmark_ai.py --models tfidf --repeats 1 --limit 0 --pause 0 |
    Set-Content -Encoding utf8NoBOM output/ai-evaluation/development-benchmark.jsonl
python -m scripts.verify_ai_regression `
    --contracts output/ai-evaluation/contract-tests.xml `
    --benchmark output/ai-evaluation/development-benchmark.jsonl
```

PowerShell 7 is used above. Check each command's exit code in automation. The
workflow uses Bash `pipefail` for the benchmark and runs the verifier as its own
required workload step.

An intentional test or development/model inventory change requires a reviewed
baseline update with its rationale and the AI owner's decision. A dependency
change that changes collected test identities also requires reconciliation.
Do not silently regenerate the baseline during CI. In particular, merge #107's
additional provider test with an explicitly reviewed inventory update if that
changes this selection.

## Required-status delivery

This change reuses the already-reviewed workflow fix from
[PR #220](https://github.com/kendshhh/PhishLens/pull/220): the exact
`Deterministic AI Evaluation` status name, a fail-closed change detector and
the explicit not-applicable path for unrelated changes. This guard's workflow
step has the same AI-change condition. #93 stays
open until the reviewed source is delivered and both applicable and
not-applicable status behavior is verified. A passing local workload does not
prove that GitHub's required status or branch protection is configured correctly.

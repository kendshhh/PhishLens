# Implementation checks — 29 October 2026

This records software integration, not a new model benchmark. The primary
TF-IDF model and threshold are unchanged. The frozen test cohorts were not read.

| Check | Evidence |
|---|---|
| Extension tests | 140 passed; `implementation/live_review/results/javascript-tests.xml` |
| Local Python tests | 357 passed, 86 passing subtests, 38 skipped; PostgreSQL/provider opt-ins were not enabled locally |
| Lint and inventory | ESLint, Ruff and extension manifest/required asset validation passed |
| Real local LLM | Chrome 156.0.8078.73 on Windows 10.0.26300; pinned Llama q4f16, WebGPU; seed passed, 13 generated tokens |
| First and warm software example | 38,257.3 ms and 4,382.5 ms respectively; one sentence repeated, not latency percentiles |
| Actual review outcome | All three classifiers were below their thresholds; the LLM disagreed. The application displayed Uncertain |
| Report controls | Explicit consent, create/reread/history, notes/feedback/delete passed with intercepted API responses |
| Cancellation | Clear removed the active scan; no stale result reappeared |
| Privacy in Chrome check | No unintercepted external request hosts; temporary browser profile removed |
| Auxiliary exports | 12 calibration-only parity inputs: KRR maximum absolute margin difference 6.66e-16; LightGBM 0 |
| KRR implementation | Weighted sparse primal calculation matched explicit linear-kernel KRR within 1.12e-15 |
| Historical evidence | All 108 archived files retained their SHA-256 values; original research records untouched |
| Final package changes | 12 packaging tests and 8 subtests passed after streaming ZIP hashes and storing quantized weight entries |

The Chrome example is recorded in
`implementation/live_review/results/browser-software-check.json`. The LLM's
disagreement is a real observed limitation, not an accuracy measurement or an
outcome to conceal. The example validates the Uncertain path. Unit tests also
exercise supported release and malformed-output paths with explicit software
fixtures; those fixtures are not claimed as actual LLM results.

The first implementation hit Chrome's large-resource allocation limit. Splitting
the external model data into verified 4 MB parts resolved the process crash.
Missing ONNX asyncify assets and contradictory generated audit fields were also
fixed. The final compact schema uses a combined audit/reason code and an exact
quote ID, so the two fields cannot contradict one another. Semantic judgement
still requires evaluation; schema validity does not establish correctness.

GitHub push protection falsely flagged a public Mistral model-class registry
string in the upstream Transformers.js bundle. Published and local SHA-256
values matched exactly. The documented vendor patch uses concatenated strings
with the identical runtime value. Actual Chrome inference and report controls
were checked again afterward. Push protection was not bypassed.

The Windows test harness initially decoded Node's Unicode JSON as Windows-1252.
It now requests UTF-8 explicitly. Two existing Alembic configuration deprecation
warnings are unrelated to inference. Local checks use Python 3.12.14 and existing
installed dependencies; GitHub CI checks the repository's pinned dependencies.

The required CI database gate now includes a real saved-create, fresh-session
reread and delete test for local review metadata. It allows only the disposable
localhost database. No development, production, staging or expired Neon branch
was used. Browser API interception alone does not establish persistence.

No public deployment, new combined accuracy/recall result, human review pass,
macOS test or original benchmark qualification is claimed by these checks.
The full local bundle needs roughly 1.1 GB of model weights plus runtime assets,
and a WebGPU device supporting shader-f16. These are practical costs of running
the teacher's complete workflow on every scan.

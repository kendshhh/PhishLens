# AI evaluation workflow

The deterministic AI workflow runs for pull requests and main pushes when
backend/extension AI code, prompt/schema/model settings, evaluation scripts,
AI tests, or pinned AI dependencies change. It tests provider contracts and
verifies that Gemini request and per-run dollar caps block inference before the
provider call. It also evaluates the bundled TF-IDF model over the 40 synthetic
development cases. This check reports evaluation completion; it does not
approve model quality until an AI owner has set and reviewed thresholds.

Normal CI and this workflow make no paid provider request. The development
cohort records model behavior and confusion metrics but is not a held-out test
set. Current code reports those metrics without enforcing an accuracy threshold
because the AI owner has not approved one. A held-out cohort stays separate and
must follow the review protocol in
`docs/ai/tfidf-sprint-3-evaluation-protocol.md`.

## Latest local development evaluation

On 2026-11-14, the full 40-case synthetic cohort completed with zero inference
errors using TF-IDF model SHA
`a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c` and zero
Gemini/provider calls. Results were **65% binary accuracy**, **18.75% phishing
recall (3/16 phishing cases detected)**, and **6.25% legitimate false-positive
rate (1/16)**. All eight spam cases were predicted as legitimate; this binary
benchmark does not claim three-class accuracy. These results are on a small
synthetic development set, not a held-out or production set, but the phishing
recall is weak and must be reviewed before claiming acceptable AI behavior.
The result is not a release-quality pass. No accuracy threshold has been
approved, so the workflow currently blocks incomplete runs and provider-cap
regressions but does not block low model scores.

## Gemini spend guard

Before Gemini can run in the API, configure all of these on that service:

| Setting | Meaning |
|---|---|
| `GEMINI_PER_REQUEST_COST_CAP_USD` | Maximum upper-bound cost for one API inference |
| `GEMINI_INPUT_USD_PER_MILLION_TOKENS` | Current paid input-token rate for the selected model |
| `GEMINI_OUTPUT_USD_PER_MILLION_TOKENS` | Current paid output-token rate for the selected model |
| `GEMINI_COST_MODEL_ID` | Exact model identifier those two rates describe; must equal `GEMINI_MODEL` |

The runtime estimates input tokens conservatively from UTF-8 byte counts for
the contents, system instruction, response schema, and fixed serialization
overhead. It reserves the configured maximum output tokens. It blocks the API
call before `generate_content` when the upper-bound cost exceeds the cap. It
fails closed when a cap or rate is absent, invalid, or zero.

For explicitly run local Gemini evaluations, also set:

| Setting | Meaning |
|---|---|
| `GEMINI_PER_RUN_COST_CAP_USD` | Aggregate upper-bound cost for the evaluation process |
| `GEMINI_MAX_REQUESTS` | Exact inference-call count allowed by the selected script |

`ai_smoke.py` requires three calls. `benchmark_ai.py` requires one cold-start
call plus `repeats × selected cases`; the complete one-pass development
benchmark requires 41 calls. Each request reserves cost before inference and
the run stops if the next request would exceed the dollar or request ceiling.

Rates are owner-maintained from the current provider pricing schedule and are
bound to the selected model by exact identifier. The guard does not read billing
or account-level quota, and does not model charges for features this client
does not use (tools, search grounding, or cached input). The runtime cap is a
pre-call estimate based on the configured rates and conservative token bounds,
not an invoice guarantee or provider quota. The deployed API cap is per request;
it does not impose an aggregate daily/monthly budget across concurrent requests,
instances, or restarts. A provider-side quota or shared durable accounting limit
is still required before enabling production Gemini traffic. Tests prove local
pre-call blocking behavior; no paid provider run was made for this change.

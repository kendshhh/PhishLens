# AI classification contract and runtime

TF-IDF v12a is the primary PhishLens classifier. The extension scores selected
text locally. For a saved report, the backend scores the submitted body again
and stores its own classification, risk, evidence and model revision.

## TF-IDF contract

- Set `AI_MODE=tfidf` for the matching backend. The bundled model is
  `word_plus_char_wb_C1p0`, SHA-256
  `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`.
  See the [artifact attribution and source rights](../extension/ai/ATTRIBUTION.md).
  The backend scorer runs on CPU with the bundled JSON artifact.
- The scorer uses the visible body, masks email local parts, phone-like patterns
  and long numbers, and collapses whitespace. After cleaning, long input is
  reduced to the first 2,000 and last 300 Unicode code points. The backend accepts
  a subject and sender, which do not contribute to the TF-IDF score.
- Word and within-word character features produce a raw margin. A margin at or
  above zero triggers a phishing alert. The frozen sigmoid maps that boundary
  to a displayed phishing score of about 88.71%. The score is tied to the study
  mixture. TF-IDF emits two labels: `phishing` and `legitimate` (below the
  threshold). It does not emit `spam` or a predicted-class confidence.
- The backend maps the label to risk and validates quoted evidence against the
  request. Word-feature contributions are partial statistical explanations.
  A below-threshold result does not authenticate the sender, links or attachments.
- The separate browser review uses KRR, LightGBM and a local judge. It can return
  `Uncertain`. The backend records the judge output as browser-reported and
  persists the server's primary TF-IDF provenance. See the
  [browser workflow](ai/live-workflow.md) for its assets and requirements.

`GET /model-info` advertises the matching save capability and model hash.
`POST /analyses` runs inference without saving. The extension's
`POST /api/analyses` sends `X-PhishLens-Model` with the expected hash.
A mismatched model returns `503 analysis_unavailable` before database setup.

```sh
python scripts/ai_smoke.py --mode tfidf
python scripts/verify_tfidf_evaluation.py
```

The [sprint verification handoff](ai/tfidf-sprint-closeout.md) records local
runtime checks, historical held-out results, model quality limits and what the
release owner still needs to verify on the chosen deployment.

## Provider selection

`AI_MODE` also supports `mock`, `gemini`, and legacy `local` DistilBERT.
The default is `mock` for development and ordinary CI.

`gemini` uses the Google GenAI API and requires `GEMINI_API_KEY` and
`GEMINI_MODEL`. The adapter has a separate explicit-schema path for hosted Gemma;
mocked tests cover that path, but this handoff contains no live Gemma evidence.

The optional local provider uses `dima806/phishing-email-detection` from
[Hugging Face](https://huggingface.co/dima806/phishing-email-detection/tree/310a5602280486e01dd60e37230980cfcc327b41),
pinned to revision `310a5602280486e01dd60e37230980cfcc327b41`.
Its cached model card declares Apache-2.0 and English; its configuration identifies
`distilbert-base-cased`. The adapter verifies architecture and label metadata,
loads safetensors on CPU, and uses four PyTorch threads. It does not train or
fine-tune the checkpoint.

## Optional provider input, tokenizer, and score policy

- `POST /analyses` accepts `text` (1 to 30,000 characters, excluding blank-only
  input), optional `subject` and `sender` (each at most 320 characters).
  Extra request fields are rejected. Subject, sender, and body are JSON-escaped
  before being sent to the shared service's provider.
- Local inference uses subject and body. Sender metadata is not used by that
  classifier. The case-preserving tokenizer uses at most 512 tokens per window,
  including special tokens, with 64 content tokens of overlap. Overflow windows
  are all processed, in batches of up to four; accepted input is not silently
  limited to its first window.
- Local checkpoint label 0 is literally `SAVE EMAIL` (the author's spelling),
  mapped to `legitimate`. Label 1 is `PHISHING EMAIL`, mapped to `phishing`.
  Apply softmax to logits, take class 1 for each window, then take the maximum
  across windows to obtain `p`. The fixed decision is `p >= 0.5` for phishing,
  otherwise legitimate. The returned `confidence` is `p` for phishing and `1-p`
  for legitimate. This is an uncalibrated classifier score, not measured accuracy.
  No separate spam class exists in the local checkpoint.
- Google handles its tokenizer; the application does not define a hosted input
  token limit. The application character limit still applies. Hosted generation
  is capped at 2,048 output tokens with temperature 0. Hosted payloads return a
  classification and explanations, without a numeric confidence or numeric
  decision threshold. Unset metadata fields are omitted from the HTTP response.
- The API maps `legitimate` to `low`, `spam` to `medium`, and `phishing` to `high`.
  These are category mappings, not additional numeric score bands.

## Optional provider indicators and validation

Local indicators are explicit regular-expression matches for sensitive-information
terms, urgency, payment requests, and links in the subject/body. Evidence includes
the actual matched text. `explanation_source=rules` distinguishes these matches
from neural attribution; a match alone does not establish phishing.

Hosted indicators and evidence are generated from the supplied email using
prompt version `phishing-v2`, with `explanation_source=model`. The backend validates
the response schema and checks that every evidence quote occurs in a supplied
field after normalizing whitespace. This verifies quote provenance, not that the
classification or explanation is correct. Confidence and provenance are assigned
by the backend rather than accepted from the generated payload.

Neither path visits URLs, scans attachments, or authenticates a sender.
Configuration failures return HTTP 503. Invalid provider output, unsupported
evidence, and inference failures return HTTP 502. Recognized Google daily quota
exhaustion returns HTTP 503; the benchmark stops rather than repeatedly retrying
that exhausted quota. Hosted requests have a 30-second timeout and one SDK attempt.

## Tests and optional provider smoke

From the repository root in an activated Python 3.12 virtual environment:

```sh
python -m pip install -r backend/requirements.txt
python -m pip install -r backend/requirements-dev.txt
python -m pytest backend/tests -q -p no:cacheprovider
python -m ruff check backend
python -m pip check
```

Ordinary tests mock inference and do not download models or require Google keys.
The two PostgreSQL tests require the isolated migrated and seeded database used by
CI and `RUN_DATABASE_TESTS=1`; never point them at the hosted application database.

For optional real CPU inference:

```sh
python -m pip install -r backend/requirements-ai.txt
python scripts/ai_smoke.py --mode local --download-model
python scripts/ai_smoke.py --mode local
python scripts/benchmark_ai.py --models local --repeats 1 --pause 0
```

`MODEL_PATH` selects the Hugging Face cache directory; its default is ignored
`models/`. Model download is an explicit preparation action. Normal API startup
does not load or download weights; the first local inference loads cached weights.
Configure `AI_MODE=local` for API use and restart the backend after changing mode.
The optional requirements include CPU PyTorch, Transformers, and psutil; ordinary
API/CI installs exclude these heavy dependencies. The benchmark needs psutil for
memory measurements, including when comparing hosted models.

Hosted smoke calls use `python scripts/ai_smoke.py --mode gemini`; configure the
private credentials first. Hosted benchmarks consume provider quota and may incur
cost. No new hosted calls were made during this review handoff.

## Historical DistilBERT evidence

See [the October 18 DevOps handoff](devops/ai-review-2026-10-18.md) and
[actual local benchmark summary](devops/evidence/ai-local-2026-10-18.json).
The 40 original synthetic development cases demonstrate runtime behavior, not
representative deployment accuracy. They include spam as non-phishing for binary
metrics, although the local model has no spam class. Model/provider acceptance,
threshold calibration, staging deployment, and installed-Chrome verification
remain separate review tasks.

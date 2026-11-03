# PhishLens model comparison — October 22, 2026

Recorded (Asia/Manila): 2026-10-22T13:53:06.792852+08:00

Source commit: `00d0bf60deb4f90544435e2af24563b3a5b376fe`. Suite: `synthetic-v1`.

All models use the existing AIService and its output/evidence validation. The frozen suite contains 40 original synthetic emails: 16 phishing, 16 legitimate and 8 spam. Each model is assigned the same case order, one scored pass and a separate unscored initial request; the Gemini 3.8 run stops before completing the suite because its daily quota is exhausted. These development cases do not establish representative production accuracy.

## Implementation decision

Gemini 3.1 Flash-Lite is the recommended provider for the current implementation based on this run. It completed all 40 scored attempts, returned 37 validated analyses, made no false phishing accusations, and produced 36 exact three-class matches. Its median valid response took 4.2466 seconds. This improves detection and label usefulness over the tested local checkpoint, while requiring provider availability handling for the three original failed requests. The existing local configuration already selects Flash-Lite.

Gemini 3.8 Flash is not sufficiently evaluated to rank its classification quality. Its run stopped at daily quota after 20 attempts: two valid responses, 18 errors, and 20 unattempted cases. The 18 scored errors comprise 13 HTTP 504 responses, four HTTP 503 responses and the quota-stop response; its unscored initial request also failed with HTTP 504. It was operationally unreliable with the tested provider, account and application settings. A complete accuracy comparison requires sufficient quota and another recorded run; no further calls were made after quota exhaustion.

DistilBERT was the fastest after loading and returned all 40 analyses, but its 60% binary accuracy, four missed phishing examples, twelve false phishing warnings and absence of a spam output class make this checkpoint a weaker primary detector in this suite. No application settings were changed.

## Detection and product behavior

Binary accuracy treats spam as non-phishing; three-class accuracy requires the exact label. DistilBERT has no spam output class. Failed analyses remain in the requested-case denominator. Incomplete runs have no comparable full-suite accuracy.

| Model | Valid / attempted analyses | Binary accuracy | Three-class accuracy | Phishing recall | Phishing precision | Phishing F1 | False-positive rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DistilBERT | 40/40 | 60.0% | 60.0% | 75.0% | 50.0% | 60.0% | 50.0% |
| Gemini 3.1 Flash-Lite | 37/40 | 92.5% | 90.0% | 87.5% | 100.0% | 93.3% | 0.0% |
| Gemini 3.8 Flash | 2/20 | N/A | N/A | N/A | N/A | N/A | N/A |

## Runtime

| Model | Initial request (unscored) | Median scored latency | p95 scored latency | Mean scored latency | Errors / unattempted | Peak process RSS |
| --- | --- | --- | --- | --- | --- | --- |
| DistilBERT | 7.8436 s | 0.0164 s | 0.0537 s | 0.0379 s | 0 / 0 | 579.36 MiB |
| Gemini 3.1 Flash-Lite | 4.1276 s | 4.2466 s | 7.3476 s | 4.4903 s | 3 / 0 | 78.77 MiB |
| Gemini 3.8 Flash | N/A | 23.1090 s | 26.1719 s | 23.1090 s | 18 / 20 | 78.45 MiB |

Timing includes inference and shared-service validation. Hosted timing includes network travel; the intentional five-second pauses are excluded. Scored latency statistics cover valid analyses only. The local initial request includes loading cached model weights into a fresh process; OS caches may already be warm. Hosted RSS measures only the local API client, not Google's model-serving memory. Provider token usage, resolved hosted model versions, actual billing and cost per analysis were not recorded.

Hosted generation uses the current application settings: temperature 0, maximum 2,048 output tokens, 30-second HTTP timeout, one SDK attempt and provider-default thinking configuration. The two hosted workers ran concurrently, with sequential requests within each model; shared-account traffic and quota may affect results. The local run completed before hosted generation began. Access-check calls successfully retrieved metadata for both exact requested Gemini model IDs.

## Classification versus availability

The main accuracy table counts failed analyses as unsuccessful outcomes. The following table isolates label correctness among valid returned analyses. This separates model decisions from provider availability, timeouts and output-validation failures. A small number of returned analyses is insufficient to judge overall quality.

| Model | Valid analyses | Binary accuracy among valid analyses | Three-class accuracy among valid analyses | p95 latency including failed calls |
| --- | --- | --- | --- | --- |
| DistilBERT | 40 | 60.0% | 60.0% | 0.0537 s |
| Gemini 3.1 Flash-Lite | 37 | 100.0% | 97.3% | 7.3476 s |
| Gemini 3.8 Flash | 2 | 100.0% | 100.0% | 29.0779 s |

Gemini 3.8's two valid responses were both phishing examples. Its 100% conditional figures describe only these two returned answers and cannot establish classification quality or performance on legitimate email or spam.

## Case outcomes

### DistilBERT

Run status: `finished`.

```json
{
  "phishing->phishing": 12,
  "phishing->legitimate": 4,
  "legitimate->legitimate": 12,
  "legitimate->phishing": 4,
  "spam->phishing": 8
}
```

- `p06-gift-card`: expected phishing; returned legitimate.
- `p08-macro`: expected phishing; returned legitimate.
- `p12-campus`: expected phishing; returned legitimate.
- `p15-long-tail`: expected phishing; returned legitimate.
- `l02-receipt`: expected legitimate; returned phishing.
- `l04-reset`: expected legitimate; returned phishing.
- `l10-transaction-alert`: expected legitimate; returned phishing.
- `l16-anti-injection`: expected legitimate; returned phishing.
- `s01-sale`: expected spam; returned phishing.
- `s02-course`: expected spam; returned phishing.
- `s03-furniture`: expected spam; returned phishing.
- `s04-newsletter`: expected spam; returned phishing.
- `s05-travel`: expected spam; returned phishing.
- `s06-fitness`: expected spam; returned phishing.
- `s07-business`: expected spam; returned phishing.
- `s08-urgent-sale`: expected spam; returned phishing.

### Gemini 3.1 Flash-Lite

Run status: `finished`.

```json
{
  "phishing->phishing": 14,
  "phishing->ERROR": 2,
  "legitimate->legitimate": 15,
  "legitimate->ERROR": 1,
  "spam->spam": 7,
  "spam->legitimate": 1
}
```

- `p15-long-tail`: expected phishing; returned ERROR: Gemini is temporarily unavailable (HTTP 503). Please try again..
- `p16-injection`: expected phishing; returned ERROR: Gemini is temporarily unavailable (HTTP 503). Please try again..
- `l02-receipt`: expected legitimate; returned ERROR: Gemini is temporarily unavailable (HTTP 504). Please try again..
- `s08-urgent-sale`: expected spam; returned legitimate.

Error counts:

```json
{
  "Gemini is temporarily unavailable (HTTP 503). Please try again.": 2,
  "Gemini is temporarily unavailable (HTTP 504). Please try again.": 1
}
```

### Gemini 3.8 Flash

Run status: `daily_quota_exhausted`.

```json
{
  "phishing->ERROR": 14,
  "phishing->phishing": 2,
  "legitimate->ERROR": 4
}
```

- `p01-credential`: expected phishing; returned ERROR: Gemini is temporarily unavailable (HTTP 504). Please try again..
- `p02-payroll`: expected phishing; returned ERROR: Gemini is temporarily unavailable (HTTP 504). Please try again..
- `p03-invoice-bec`: expected phishing; returned ERROR: Gemini is temporarily unavailable (HTTP 503). Please try again..
- `p04-qr`: expected phishing; returned ERROR: Gemini is temporarily unavailable (HTTP 504). Please try again..
- `p05-mfa`: expected phishing; returned ERROR: Gemini is temporarily unavailable (HTTP 504). Please try again..
- `p07-delivery-fee`: expected phishing; returned ERROR: Gemini is temporarily unavailable (HTTP 504). Please try again..
- `p08-macro`: expected phishing; returned ERROR: Gemini is temporarily unavailable (HTTP 504). Please try again..
- `p09-oauth`: expected phishing; returned ERROR: Gemini is temporarily unavailable (HTTP 504). Please try again..
- `p11-tax`: expected phishing; returned ERROR: Gemini is temporarily unavailable (HTTP 503). Please try again..
- `p12-campus`: expected phishing; returned ERROR: Gemini is temporarily unavailable (HTTP 504). Please try again..
- `p13-tagalog`: expected phishing; returned ERROR: Gemini is temporarily unavailable (HTTP 503). Please try again..
- `p14-obfuscated`: expected phishing; returned ERROR: Gemini is temporarily unavailable (HTTP 503). Please try again..
- `p15-long-tail`: expected phishing; returned ERROR: Gemini is temporarily unavailable (HTTP 504). Please try again..
- `p16-injection`: expected phishing; returned ERROR: Gemini is temporarily unavailable (HTTP 504). Please try again..
- `l01-meeting`: expected legitimate; returned ERROR: Gemini is temporarily unavailable (HTTP 504). Please try again..
- `l02-receipt`: expected legitimate; returned ERROR: Gemini is temporarily unavailable (HTTP 504). Please try again..
- `l03-training`: expected legitimate; returned ERROR: Gemini is temporarily unavailable (HTTP 504). Please try again..
- `l04-reset`: expected legitimate; returned ERROR: The AI provider's daily request quota is exhausted. Check provider quota before retrying..
- Initial request failed: Gemini is temporarily unavailable (HTTP 504). Please try again.

Error counts:

```json
{
  "Gemini is temporarily unavailable (HTTP 504). Please try again.": 13,
  "Gemini is temporarily unavailable (HTTP 503). Please try again.": 4,
  "The AI provider's daily request quota is exhausted. Check provider quota before retrying.": 1
}
```

## Supplemental Flash-Lite retries

Each of the three original failed cases was retried once through the same AIService and provider settings. All three returned the expected labels on retry. These are diagnostic follow-up calls; they do not replace, remove or improve the original benchmark scores.

| Case | Expected | Retry result | Seconds |
| --- | --- | --- | --- |
| p15-long-tail | phishing | phishing | 3.5962 |
| p16-injection | phishing | phishing | 6.3437 |
| l02-receipt | legitimate | legitimate | 6.7627 |

## Reproduce

Use the configured private credentials; do not commit credentials or private emails.

```powershell
.\.venv\Scripts\python.exe -u scripts\benchmark_ai.py --worker local --repeats 1 --pause 0
.\.venv\Scripts\python.exe -u scripts\benchmark_ai.py --worker gemini-3.1-flash-lite --repeats 1 --pause 5
.\.venv\Scripts\python.exe -u scripts\benchmark_ai.py --worker gemini-3.8-flash --repeats 1 --pause 5
```

Raw per-model JSONL, access-check evidence, comparison.json and cases.csv are saved beside this report. The source files and case hash are recorded in comparison.json. No application configuration was changed.

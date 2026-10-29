# TF-IDF integration — 29 October 2026

Authorized by the project owner’s request to update main, preserve benchmark
records, create a branch, and integrate the selected AI with contributor work.

Branch: `codex/tfidf-v12a-workflow-20261029`.
Base: `1344fcb061272bac93ced5911f1ab8fbb3b6785d` (origin/main).
The original dirty benchmark checkout stays untouched.

1. Snapshot shareable historical reports in `benchmark-records/`, with an HTML
   index and SHA-256 inventory. Keep private source mail and full working runs
   in their original location; do not publish them or copy them into the ZIP.
2. Package the exact v12a weights, preprocessing, calibration and cutoff.
   Scan highlighted visible text in the extension service worker. Verify model
   integrity, return complete English observations and exact checked quotes,
   preserve Clear/latest-request behavior, and display failures explicitly.
3. Wire the contributors’ saved-report client into the popup. Saving is
   optional and explicitly uploads text; browsing history is also explicit.
   The server recomputes using its own TF-IDF artifact instead of accepting
   client-supplied verdicts. Existing idempotency and refresh failure handling
   remain in use. No hosted environment or database configuration is changed.
4. Add straightforward developer commands and Chrome debugging instructions.
   Check unit/contract tests, JavaScript/Python parity, packaging and browser
   behavior. Do not rerun the held-out cohort or change benchmark claims.

This is an advisory integration pilot. It does not close the original missing
OOD/adversarial/authenticated bank coverage, human explanation review, macOS
evaluation or public-release acceptance. No model is guaranteed correct.

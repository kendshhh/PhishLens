# Extension analysis and saved-report journey

The extension supports highlighted email text and pasted email text. Both use
the existing local analysis workflow. The separate **Analyze and save on the
server** form uploads its input immediately when submitted.

## Local analysis

The popup opens in **Check email**. **Saved reports** explicitly loads history
from the API; switching back keeps the current draft and local result. Plain
language results and next actions lead the screen. Wording observations, model
scores/review details, and checked text are expandable. Below-threshold results
explicitly do not confirm authenticity; incomplete reviews remain uncertain.

1. Highlight the complete visible email and choose **Analyze selection with
   PhishLens**, or paste it into **Email text** and select **Check this email**.
2. Wait for the outcome. Closing the popup does not cancel the background scan.
   The pasted draft is kept in Chrome session storage and restored when the
   popup reopens; it is not persisted across browser sessions. Deleting its text
   updates the stored draft.
3. Review the score, observations, local judge, reevaluation, and limitations.
   Missing model weights or unsupported GPU features produce uncertainty rather
   than a reviewed verdict. **Clear local scan** cancels/clears scan state; the
   pasted draft remains available for another scan.

## Save, reopen, edit, delete

1. Enter an optional report title, select the upload consent checkbox, and select
   **Save report**. Only this action uploads the original analyzed text.
2. The extension checks `/model-info` without sending the text. The server must
   support the matching TF-IDF model and browser-reported local reviews.
3. Save performs one POST and rereads detail/history. A refresh failure or failure
   to write the local save marker does not undo a confirmed save. Check history
   before another attempt when a warning appears.
4. An uncertain acknowledgement retains the request key. Reopening the popup
   restores that attempt's title so explicitly retrying the unchanged report
   uses the same key. Consent is never restored automatically. Changing the title
   represents a different request; recover the original attempt first if its
   outcome is unknown.
5. **Load / refresh history**, then **View details**. Edit notes/feedback, close
   and reopen the popup, and reload history to confirm the saved values.
6. Delete only your own synthetic test report using its confirmation. Refresh
   and reopen history to check that it is absent. Deleting a locally saved report
   also clears its local saved marker when storage is available.

## Verification and remaining acceptance

Popup tests cover exact local input, draft reopening, duplicate-submit blocking,
worker failures, titled retry keys, confirmed saves despite local marker failure,
and CRUD/uncertainty rendering. `npm run test:browser` loads the packaged extension
in Chromium with a disposable synthetic API and exercises pasted analysis,
local-report saving/reopening without duplicate creation, CRUD, and focus.

These tests do not prove hosted PostgreSQL behavior. For installed-Chrome staging
acceptance, use the workflow's `PhishLens-Staging-Extension` artifact, compare its
deployed commit with `/version`, confirm `/ready` and `/model-info`, and follow
the same journey using authorized synthetic data. Shared staging and database
ownership must be confirmed before record-changing tests. See
[staging](devops/staging.md) and [release verification](release-verification.md).

The default package excludes local Llama weights. Full reviewed analysis also
requires verified model assets and compatible WebGPU; see
[model setup and packaging](ai/live-workflow.md). Current shared demo history is
not authenticated per-user storage. No deployed or full-model acceptance is
implied by the synthetic browser test.

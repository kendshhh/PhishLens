# Extension analysis and saved-report journey

## Local staging preview

From the repository root, run `python3 scripts/prepare_local_staging.py` after
local UI edits. In Chrome, load or reload
`output/staging-local/extension` and disable any production-targeted copy. The
popup must show **STAGING · LOCAL UI PREVIEW** and
`phishlens-staging.onrender.com`. Loading the source `extension` directory instead
uses the production API.

The preview is a snapshot of the latest local runtime files with staging-only
configuration and permission. Refresh it with the command after further edits.
The default preview excludes LLM weights. For complete local-model testing, first
run `node scripts/setup_judge_assets.mjs --download`, then refresh with
`python3 scripts/prepare_local_staging.py --include-models`. The pinned model
files are verified before packaging and remain ignored by Git. Allow additional
disk space for the model, ZIP and extracted preview. This build does not deploy
the backend, modify records or establish release acceptance. Use the matching
CI artifact for release checks.

The primary flow is highlighted email text followed by **Analyze selection with
PhishLens** in the right-click menu. It automatically opens the Chrome action
popup in the source window, showing the original selection and scan progress.
Chrome 127 or later is required for programmatic action popups. If Chrome cannot
open the popup, analysis continues and the toolbar popup retains the result.
The secondary **Or paste email text** option is collapsed by default. Both use
the existing local analysis workflow. The separate **Analyze and save on the
server** form uploads its input immediately when submitted.

The original-text preview preserves paragraph breaks, blank lines, tabs and
repeated spaces, and wraps within the same 150px maximum-height box. Long text
scrolls vertically; the preview is keyboard focusable. On right-click, temporary
`activeTab` and `scripting` access reads only the selected text from the clicked
frame before the popup takes focus. That value is used only when its words match
Chrome's context-menu selection. If the page denies access or the selection has
changed, Chrome's original menu text is retained. No broad website permission or
page-wide content collection is added.

## Local analysis

The popup opens in **Check email** with selection instructions or the current
highlighted text and outcome. **Saved reports** explicitly loads history
from the API; switching back keeps the current draft and local result. Plain
language results and next actions lead the screen. Relevant wording observations
are shown beside the assessment (up to three at first, with more expandable).
The first recommended action is prominent; further advice remains available.
Model internals and a duplicate normalized-text panel are not
shown in the main check interface; the analysis and save contract retain their
existing model data. A plain-language warning identifies partial checks of long
emails. Below-threshold results
explicitly do not confirm authenticity; incomplete reviews remain uncertain.

1. Highlight the complete visible email and choose **Analyze selection with
   PhishLens**. The popup opens automatically. Alternatively, expand **Or paste
   email text**, paste into **Email text**, and select **Check this email**.
2. Wait for the outcome. Closing the popup does not cancel the background scan.
   The pasted draft is kept in Chrome session storage and restored when the
   popup reopens; it is not persisted across browser sessions. Deleting its text
   updates the stored draft.
3. Review the plain-language assessment, observations, next action and limitations.
   Missing model weights or unsupported GPU features produce uncertainty rather
   than a reviewed verdict. **Clear local scan** cancels/clears scan state; the
   pasted draft remains available for another scan.
4. While checking, **Cancel check** stops the current analysis and retains the
   selected text. **Check again** restarts it. **Try again** on an error reuses
   the exact original selection. These controls do not upload or save reports.

## Save, reopen, edit, delete

1. Enter an optional report title, select the upload consent checkbox, and select
   **Save report**. Only this action uploads the original analyzed text.
2. The extension checks `/model-info` without sending the text. The server must
   support the matching TF-IDF model and browser-reported local reviews.
3. Save performs one POST and rereads detail/history. A refresh failure or failure
   to write the local save marker does not undo a confirmed save. Check history
   before another attempt when a warning appears.
   The save card shows **Not saved yet** until a saved copy is confirmed. A
   failure before submission shows **Report not saved** in a focused alert.
   A request that may have reached the server instead shows **Save not confirmed**
   and asks the user to check history. The attempt's submitted marker preserves
   that uncertainty on popup reopening. Retry reuses its original request key;
   an unavailable capability check on that retry does not erase an earlier
   unknown outcome.
   Confirmation stays on the result screen with **View report**; repeated saves
   are disabled for the confirmed report. The returned copy can be viewed even
   when rereading failed. After reopening, **View report** fetches its saved ID.
4. An uncertain acknowledgement retains the request key. Reopening the popup
   restores that attempt's title so explicitly retrying the unchanged report
   uses the same key. Consent is never restored automatically. Changing the title
   represents a different request; recover the original attempt first if its
   outcome is unknown.
5. **Load / refresh history**, then **View details**. Edit notes/feedback, close
   and reopen the popup, and reload history to confirm the saved values.
   Cards show title, assessment, date and a short explanation preview; they do
   not fetch every email body merely to populate the list. Edit/delete stay in
   the report details.
   Search filters the loaded titles and summaries locally, and the count reflects
   the loaded set rather than claiming a database-wide total. Opening a report
   switches to its detail view; **All reports** restores the library and query.
   Detail uses the report title, saved date, original text, summary, assessment,
   notes and feedback. Source information is plain language; raw model hashes,
   revision IDs and duplicate model assessments are not displayed. Mock and
   unverified-source warnings remain explicit.
   **Edit notes** keeps annotations separate from optional correction feedback.
   Expand **Think this result is wrong?** to choose a plain-language opinion.
   There is one no-feedback choice; notes-only edits preserve legacy null values
   without displaying a second equivalent option. Feedback does not change the
   saved assessment or automatically update future checks.
6. Delete only your own synthetic test report using its confirmation. Refresh
   and reopen history to check that it is absent. Deleting a locally saved report
   also clears its local saved marker when storage is available.

## Verification and remaining acceptance

On November 7, the local staging preview passed the real hosted create/read/
update/delete journey, including popup reopening and confirmed cleanup. See
[the dated evidence](evidence/frontend-staging-crud-2026-11-07.md) for exact backend
revision, local controller hash, limitations and the earlier harness wait issue.
This is not production or release-candidate acceptance.

Popup tests cover exact local input, draft reopening, duplicate-submit blocking,
worker failures, titled retry keys, confirmed saves despite local marker failure,
and CRUD/uncertainty rendering. `npm run test:browser` loads the packaged extension
in Chromium with a disposable synthetic API and invokes the production selection
handler with synthetic highlighted text, verifies an actual Chrome action popup
context, checks original-text display and the secondary pasted-analysis flow,
local-report saving/reopening without duplicate creation, CRUD, and focus.

The operating system's native right-click menu still needs a manual check; the
automated test invokes its registered handler rather than clicking that menu.
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

# Installed Chrome staging CRUD follow-up

## Candidate

- Backend and extension source: `68b8f9abefbbdcbd6506d9a1acdc543c8a4ecee1` (PR #61).
- Trusted preview run: https://github.com/kendshhh/PhishLens/actions/runs/42910759210
- Artifact: `13807221763`, outer ZIP SHA-256 `2a187357d99f5114cab50f6efac50c5c726dabab09824f3143ef4744f406687f`.
- Installed Chrome extension ID: `immlhmcllcjepgickihiaolbbhebebkp`.
- Isolated staging only. The trusted controller checks the allowed database target before deployment. No production or authentication configuration was changed.

## November 11

Used the installed extension page to create one synthetic record, subject `QA disposable CRUD 2026-11-11 2050`, ID `01885c37-6249-494f-87bc-eb8594dabb00`. DevTools showed POST 201 (8.37 seconds), history GET 200 and returned-ID detail GET 200. The report displayed phishing/high, unavailable confidence, nonempty evidence and explanation, and TF-IDF revision `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`.

Edited notes to `Synthetic persistence check 2026-11-11. Safe to delete after acceptance.` and feedback to `none`. PATCH and refreshed history returned 200. A newly opened toolbar popup listed the record. The interrupted session did not finish deletion.

## November 13

Rechecked staging /version: the same source remained deployed. A fresh detail request returned the same record with the edited notes, feedback and original report fields two days after creation. The installed extension also displayed the persisted edit.

Deleted only that disposable record through the extension confirmation flow. DevTools showed DELETE 204 (143 ms) and history GET 200 (281 ms). The UI displayed “Analysis deleted successfully.” and the original five entries, without the disposable subject. Existing QA seed records were not changed.

## Limits and follow-up

This records observed native Chrome behavior, not a complete release acceptance. Final detail-404 and absence after a fresh popup reopen still need capture. HAR export was attempted but did not save successfully; no exported capture is claimed. Exact browser version and a reviewable screenshot/Network evidence bundle remain to be attached. Authentication, local Llama weights, provider fault injection and Week 1 subject/result mutation were not tested here.

The run exposed a presentation defect: supported `tfidf` provenance was labeled `Unrecognized (tfidf)`. The accompanying fix adds the display label and a regression test; it does not alter the deployed package or claim that the fix is already deployed.

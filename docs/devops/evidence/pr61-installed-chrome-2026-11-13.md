# PR #61 — matched installed Chrome CRUD acceptance

Manual browser evidence supplied for the 2026-11-13 run. Screenshot filenames indicate captures from 21:00 through 21:11 Asia/Manila. The manual run is paired below with the exact staging package and deployment identity.

## Package and deployment identity

| Item | Verified value |
|---|---|
| PR/source SHA tested | `04cd88466971c7775181764d346a8dd61c621ee1` |
| Staging deployment | `dep-dbrge3rbc2fs73d0pb8g` |
| Staging `/version` | `{"commit":"04cd88466971c7775181764d346a8dd61c621ee1","environment":"staging"}` |
| Staging `/ready` | `{"status":"ready","database":"connected"}` |
| Staging `/model-info` | TF-IDF; model SHA-256 `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`; `accepts_tfidf_reports=true`; `accepts_local_reviews=true`; threshold `0.8871260470833809` |
| Secretary preview | Run `43428196362`; artifact `Veriqo-Staging-Extension` (artifact `14038464116`); preview evidence recorded at `2026-11-13T12:50:32.246318+00:00` |
| Outer artifact SHA-256 | `3b7c3194aa03ed45cc6083d6ebb1c99d7f570ccc8f2d284f536bf97325c3cb2c` |
| Inner extension ZIP | `Veriqo-Staging-Extension.zip`; SHA-256 `a1494157212f0cd749406e4da5ef0fcfc9edcde34554a99aa85fd672f662fe71` |
| Inner `preview-info.json` | PR `61`; SHA `04cd88466971c7775181764d346a8dd61c621ee1`; origin `https://phishlens-staging.onrender.com` |
| Installed Chrome extension | ID `dldecnfhiapkacbonaminmemdaecidha`; Chrome profile records the loaded unpacked path as the extracted folder for this staging ZIP |
| Browser | Google Chrome `157.0.8103.79` Official Build, 64-bit; Windows 11 25H2, build `26200.9974` |

The package is marked partial and excludes local Llama weights. This run verifies the staging CRUD flow and TF-IDF provider path; it does not establish offline local-Llama inference.

The preview's automated evidence also reports health, readiness, version, and seeded-history smoke passed; synthetic saved-report CRUD passed with cleanup; TF-IDF provenance passed; and packaged browser acceptance passed in CI run `43427838648` (`Extension-Browser-Acceptance`). Its synthetic API record ID was `97af504b-22d7-4ac0-8a5c-6129c64bc6fe` and was cleaned up.

## Manual Chrome CRUD evidence

The supplied screenshots show:

1. A saved-history list after reload with the previously deleted test entry absent.
2. A synthetic `[URGENT NOTICE]` Save an analysis form and a success message with the entry in the saved list.
3. Notes entered as `This is an accurate analysis.` and the corresponding saved detail.
4. Delete confirmation followed by `Analysis deleted successfully.` and a list without `[URGENT NOTICE]`.
5. The tester reports closing and reopening the popup and confirming notes and feedback persisted; the supplied reopened detail screenshots show `Updated notes` and feedback `Unspecified`.

The screenshots do not show the popup reopen occurring immediately after deleting `[URGENT NOTICE]`; the separately supplied reopened-list screenshot shows a prior deleted test entry absent. No claim is made that the newly created `[URGENT NOTICE]` was checked after a later reopen.

## Redacted DevTools Network evidence

The supplied Network captures show these selected requests. They contain no visible cookies, authorization headers, tokens, credentials, or personal data.

| Operation | Request | Result |
|---|---|---|
| Load history | `GET /api/analyses` | `200 OK` |
| Create | `POST /api/analyses` | `201 Created` |
| Refresh history | `GET /api/analyses` | `200 OK` |
| Edit notes/feedback | `PATCH /api/analyses/51069ad5-3265-4492-8088-349927de4421` | `200 OK` |
| Delete | `DELETE /api/analyses/51069ad5-3265-4492-8088-349927de4421` | `204 No Content` |

The Network request list also shows requests for the record-detail path, but the supplied captures do not select a detail GET to show its status panel.

## Screenshots

| File | SHA-256 |
|---|---|
| `01-reopened-list.png` | `a2be9a8037ecc4953a1faaa59eae47a31b168e62cc13103695d7a36fa3996fb7` |
| `02-save-form.png` | `d5f350ebcaf84e7de218d439ff8fc9b34f24f758dda7a63ce7e1c34555aac578` |
| `03-save-success-list.png` | `b22bd341afc5e104a36b75afda2819fe985b4ba90b707be04f04a7a2c8cc739b` |
| `04-edit-form.png` | `9321047fee317822f43188cef24f5e1e06a6f659472f9caeca0741ac2479a2a0` |
| `05-edited-detail.png` | `e9b857f5f61bc7e924d64d4ccbf75af5b10b7829d342ec51abad53e1bea9c656` |
| `06-delete-confirmation.png` | `9b158086c74fc2d217313048f55679c34803dd57d254e4cef17f9671f9d6bfe0` |
| `07-delete-success-list.png` | `1358e492f7e23769ac9c962b71ef40ef80b55657bc1d9aaa75d500cc11d3970d` |
| `08-reopened-edited-detail.png` | `b0ee876a666d78e24e102d3d707cd886ee168917197248b0a69f48b8ee271dd7` |
| `09-edited-detail-reread.png` | `38fce6dea6d0ec931242cf932bbaa04a8bc5eb1e85817a8637a8dc9595b88243` |
| `10-network-get-list.png` | `383f536772ab6fc001ce955b3aa14cb27f5136133786f7ffdcd844a4b7486538` |
| `11-network-post-create.png` | `9377f83a52387399c526aab8dbdde518154d64a7cdbb71f1a7c3b1dc62132925` |
| `12-network-get-history.png` | `98009846f7d70b358a4a6d89c63a3aecc71f47e76a13efe53dfd97652801e5b3` |
| `13-network-patch-edit.png` | `1c497e7c9ba095c265885c3d90f8854f9ef8de25a1fb99d119e031927290bea5` |
| `14-network-delete.png` | `443a7b42536695760374df1a8a312f20c780de1efd1f3e513a24409e90b99417` |

Files are in `docs/devops/evidence/pr61-chrome-crud-2026-11-13-matched/`.

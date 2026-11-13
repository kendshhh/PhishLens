# PR #61 — final installed Chrome CRUD evidence

This supplemental manual run records the final requested detail-read and delete-persistence checks. It uses the package built for the exact staging commit reported by `/version` and `preview-evidence.json`.

## Package and staging identity

| Item | Value |
|---|---|
| PR | #61 |
| Source SHA in package | `e2f9ee46cf25ec029bd9ba3851412fd800df6fa1` |
| Staging `/version` supplied for the run | `{"commit":"e2f9ee46cf25ec029bd9ba3851412fd800df6fa1","environment":"staging"}` |
| Staging deployment | `dep-dbrh6q5bedkc73djudkg` |
| Staging preview evidence | Recorded `2026-11-13T13:44:42.418877+00:00`; exact SHA smoke passed |
| Automated packaged browser acceptance | CI run `43435298405`, source SHA `e2f9ee46cf25ec029bd9ba3851412fd800df6fa1` |
| Downloaded package | `Veriqo-Staging-Extension.zip`; SHA-256 `6a9b26d6b6a48598a26f481aaabb6f7740aaa87c7fe12c07293a0926723ad890` |
| Package `preview-info.json` | PR `61`; source SHA above; origin `https://phishlens-staging.onrender.com` |
| Installed extension ID | `dldecnfhiapkacbonaminmemdaecidha` |
| Browser | Google Chrome `157.0.8103.79` Official Build, 64-bit (same version as the preceding run) |

The extension ID shown in the supplied text was one character short; the 32-character ID above is the ID in Chrome's installed profile. The ZIP's embedded `preview-info.json` establishes that the package was built for the same SHA as the supplied staging `/version`.

## Manual CRUD journey

The synthetic Chrome-run record ID was `f66f9c0-b3e3-42b8-82cf-1f4f3c0a0295`. The captures show it being created, opened, edited, fetched, deleted, then absent from the saved list after reopening the popup and refreshing history.

| Check | Evidence |
|---|---|
| Create and open record | `01-create-and-open-detail.png` |
| Edit notes and feedback; save and reload detail | `02-edit-form.png`, `03-edit-save-success.png`, `04-detail-after-history-reload.png` |
| Delete; success and empty history | `05-delete-success-empty-list.png` |
| Detail request for the same record | `GET /api/analyses/f66f9c0-b3e3-42b8-82cf-1f4f3c0a0295` — `200 OK`; `09-network-detail-get-200.png` |
| Delete request for the same record | `DELETE /api/analyses/f66f9c0-b3e3-42b8-82cf-1f4f3c0a0295` — `204 No Content`; `13-network-delete-204.png` |
| Reopen and verify absence | `16-popup-reopened-empty-list.png`; refreshed `GET /api/analyses` — `200 OK`, empty-list response; `17-network-reopened-list-get-200.png` |

Other redacted Network captures show create `POST /api/analyses` — `201 Created`, history `GET /api/analyses` — `200 OK`, edit `PATCH /api/analyses/f66f9c0-b3e3-42b8-82cf-1f4f3c0a0295` — `200 OK`, and refreshed history. The screenshots show methods, paths, and statuses without cookies, authorization values, tokens, credentials, or personal data.

The manual browser request timestamps visible in Network span approximately `2026-11-13 14:03–14:06 UTC`. The tester reports that saved feedback also persisted after closing and reopening the popup; the supplied reopened-detail screenshot shows the edited content, while the screenshots do not independently establish the feedback field value after reopening.

## Screenshot checksums

| File | SHA-256 |
|---|---|
| `01-create-and-open-detail.png` | `f2f49a7114b583860813295372fd84a1cf33e82f9efc72e2916182937b2591e4` |
| `02-edit-form.png` | `99e393a244a55abd1505fe97cffad1b730fc2aae81b997ce2c5574d2758908de` |
| `03-edit-save-success.png` | `d1b6313c26ed90db293a70df993d67196bc7d3af25dc91c211b2fa472a0df604` |
| `04-detail-after-history-reload.png` | `e54482c26d5e7d7b2032727bf8549474f560bd8e4aff38e987626648382f9a57` |
| `05-delete-success-empty-list.png` | `a06cef316caff782676f8e48f91f52874c36abd7a78c10e0467ddd9d6f9c0c67` |
| `06-network-create-201.png` | `b1f973fcb23cd2f7a33d8702eb98d86e0c2dc704b927b9fe62010299c926a942` |
| `07-network-create-record.png` | `1c2f060bb79a9bc803ce80cdab999e7b95b4b924a358380bdf093204968e6b87` |
| `08-network-history-get-200.png` | `bc91a635c75ca500fa5c757ae866d036b558a33c6ecc78cfcad851f2ad1f862b` |
| `09-network-detail-get-200.png` | `c3e32e3dc9edd2348091a0f80383a6eddda45c5304eee7c1479002eb20b77872` |
| `10-network-edit-patch-200.png` | `744278e0326ad19810800c4add2af38829faccac372983fe4aa925b3eccd9988` |
| `11-network-history-after-edit.png` | `7958062ccc1a8cfd28257e6785170e43c6cc9f8820535fe278f90de0649beffa` |
| `12-network-history-reload.png` | `2c3d991ebe796f0502dc8d9f5612f315ed434820dea85e0723a59b0af769f76e` |
| `13-network-delete-204.png` | `60b9c574daa5d95d68084d85209baf78c075926838e6d9442058185854ceb6ef` |
| `14-network-list-after-delete-200.png` | `811631d29aac37b420f9116b744370270eb755acdd004b5488acf84ec38b3d39` |
| `15-popup-empty-state.png` | `e4d2b4fad39a3a14b89d3000aec046439cdd9aa76dafd562ad411123fd16f315` |
| `16-popup-reopened-empty-list.png` | `976380a2b759f69c38326a16c70ae97f3a387468fd3fc5d6e4ae9570beffdcd3` |
| `17-network-reopened-list-get-200.png` | `5a86dc14f6eb476c335d7bd0be41ce5b10350418f1b6597088314f069a3e93dd` |

Screenshots are in `docs/devops/evidence/pr61-chrome-crud-2026-11-13-final/`. This package is a partial staging build and excludes local Llama weights; this evidence concerns the staging TF-IDF CRUD path only.

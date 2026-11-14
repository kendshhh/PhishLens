# PR #61 — user-supplied Chrome CRUD screenshots

Capture date indicated by the supplied filenames: 2026-11-13, 20:40–20:41 Asia/Manila. These screenshots document visible Chrome UI states from a later CRUD attempt. The earlier 2026-11-04 save failure remains a separate historical attempt.

## Observed states

1. `01-save-form.png` shows the Save an analysis form populated with a synthetic unusual sign-in alert subject and email body.
2. `02-saved-list.png` shows a saved record titled `[ACTION REQUIRED] Unusual Sign-In Activity Detected on Your Account` in the list, labeled Phishing · high.
3. `03-edit-notes-feedback.png` shows the edit form with notes `Hi` and feedback `Unspecified` selected.
4. `04-edited-detail.png` shows the record detail with notes `Hi`, feedback `Unspecified`, TF-IDF provider/model provenance, model revision `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`, research model score `99.96%`, and alert threshold `88.71%`.
5. `05-delete-confirmation.png` shows the delete confirmation for that record.
6. `06-delete-success.png` shows the deletion success message and the saved list without that record.

Together these images show the visible create/list, edit/detail, and delete states. They do not show the popup being closed and reopened, so they do not establish persistence after reopen or continued absence after reopen.

## Identity and evidence limits

The screenshots do not display `chrome://version`, the installed extension ZIP hash, extension `preview-info.json`, or a contemporaneous staging `/version` response. They also do not include DevTools Network evidence. Therefore the screenshots are recorded as user-supplied browser evidence, but cannot be paired to PR #61's current source/package SHA or a specific staging deployment.

At the time of the preceding staging update, `/version` reported `ee5087e873ff6dd2e51081d4fb032ca49ad62443` for PR #181, while PR #61's head was `21f13583dc4653fea4aaa6903327786840bf1563`. No identity match is inferred for these screenshots.

## Screenshot checksums

| File | SHA-256 |
|---|---|
| `01-save-form.png` | `acba2a7005546d21e74c3a05fdc7ea30ff73e18fd5bd6155ec2f6b7944d5111f` |
| `02-saved-list.png` | `0ba33160dbf344361e6c7af753d60161e876fb320c2da171d7e3e1d237a433f5` |
| `03-edit-notes-feedback.png` | `0883911f8d4b7ffea6e2acf70deb060f096608da7302ae2e45966e73471a4d0c` |
| `04-edited-detail.png` | `98ea9ad6c8eaabe0493006cdc4c4b416a656fb0487ba0e37db49e0283d2566ba` |
| `05-delete-confirmation.png` | `f5c3f80f3dc1aa223e2851d1acc5206084b4d8e436fdf37521a489d8ad8c69e7` |
| `06-delete-success.png` | `2b820ebcd11395286e294766b6a5d14174453896b8b0dd5eb40b62be2377e927` |

## Remaining acceptance evidence

- Capture package source SHA, inner ZIP SHA-256, Chrome version, and the staging `/version`, `/ready`, and `/model-info` responses immediately before the run; confirm they identify the same intended PR #61 candidate.
- Close and reopen the popup to verify the edited notes/feedback remain and the deleted record remains absent.
- Capture redacted DevTools Network methods, paths, statuses, and outcomes; omit cookies, credentials, tokens, and personal data.
- Request independent review after pairing the browser evidence to the intended package and deployment.

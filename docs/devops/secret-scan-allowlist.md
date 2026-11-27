# Gitleaks false-positive review — 2026-11-23

The required `Dependency security` job scans the checked-out repository with
Gitleaks CLI 8.30.1. The workflow downloads the official Linux x64 release and
checks its SHA-256 before execution. Gitleaks output is redacted. The job is an
existing required protected-branch status, so any finding outside this exact
fingerprint list fails the PR gate.

The scanner found 13 generic-api-key heuristic matches in the current tree. Each
`.gitleaksignore` entry is limited to one file, rule, and line fingerprint:

| Fingerprint | Reviewed disposition |
|---|---|
| `docs/frontend/issue-131/package-identity.json:generic-api-key:19` | SHA-256 package/source integrity digest, not a credential. |
| `docs/frontend/issue-131/package-identity.json:generic-api-key:30` | SHA-256 package/source integrity digest, not a credential. |
| `docs/frontend/issue-136/installed-a11y-package-identity.json:generic-api-key:19` | SHA-256 package/source integrity digest, not a credential. |
| `docs/frontend/issue-136/installed-a11y-package-identity.json:generic-api-key:30` | SHA-256 package/source integrity digest, not a credential. |
| `docs/frontend/issue-136/package-evidence.json:generic-api-key:19` | SHA-256 package/source integrity digest, not a credential. |
| `docs/frontend/issue-141/demo-package-identity.json:generic-api-key:19` | SHA-256 package/source integrity digest, not a credential. |
| `docs/frontend/issue-141/demo-package-identity.json:generic-api-key:30` | SHA-256 package/source integrity digest, not a credential. |
| `docs/frontend/issue-146/release-package-identity.json:generic-api-key:19` | SHA-256 package/source integrity digest, not a credential. |
| `docs/frontend/issue-146/release-package-identity.json:generic-api-key:30` | SHA-256 package/source integrity digest, not a credential. |
| `docs/frontend/issue-151/release-package-identity.json:generic-api-key:19` | SHA-256 package/source integrity digest, not a credential. |
| `docs/frontend/issue-151/release-package-identity.json:generic-api-key:30` | SHA-256 package/source integrity digest, not a credential. |
| `extension/manifest.json:generic-api-key:5` | Public Chrome extension manifest key; this is distributed as part of the extension identity. |
| `extension/vendor/ml/transformers.min.js:generic-api-key:3` | Reviewed minified-code false positive; the matched text is not a credential assignment. Re-review if this line changes. |

No broad path or rule suppression is used. If an allowlisted line moves or
changes, its fingerprint no longer matches and the finding must be reviewed
again. This gate scans the current checkout; GitHub Secret Protection and push
protection remain separate controls for pushes and repository history.

# Extension identity

PhishLens uses a fixed Chrome extension ID so that the Auth provider can trust a
single extension origin. Unpacked installs otherwise receive a path-based ID that
differs between machines and folders.

| Item | Value |
|---|---|
| Extension ID | `ceneonaedddlkdocdapimkfggbjcchlb` |
| Extension origin | `chrome-extension://ceneonaedddlkdocdapimkfggbjcchlb` |
| Public key | `key` in [`extension/manifest.json`](../extension/manifest.json) |
| Key type | RSA 2048-bit, generated locally (no Chrome Web Store item) |

## Status

- Approved by Trixia (`xxTrixia`) as the staging extension's fixed identity, with
  the public key added to `manifest.json`, subject to the ID check and diff review.
- This change does **not** configure or authorize a trusted-origin change, Render or
  Neon configuration, deployment, or a live Auth test. Those remain on hold until
  separately approved.
- Every package built from this manifest has this ID, including the staging preview
  package, whose packager changes only the name and host permissions. Which origins
  an environment trusts is controlled by that environment's Auth configuration.

## How the ID is derived

Chrome derives the ID from the DER-encoded public key: take the SHA-256 digest, keep
the first 32 hexadecimal characters, and map `0–f` to `a–p`. The extension test
`extension/tests/extension-identity.test.mjs` recomputes the ID from the manifest and
fails if it no longer matches.

## Verification

On 2026-11-14, a copy of `main` at `205ec26` with only this public key added was
loaded unpacked into installed Google Chrome `157.0.8103.79` in a disposable profile
with all network requests blocked. Chrome reported `ceneonaedddlkdocdapimkfggbjcchlb`
as the extension ID, and `chrome.runtime.id` inside the extension matched. The
profile and the copy were deleted.

The full package built by `scripts/package_extension.py` from a clean checkout of
the proposal commit, unzipped and loaded the same way, reported the same ID. The
staging auth package is checked separately once its backend pairing is agreed.

## Private key custody

- Holder: Andrei (`JupitraxNeptuna`). The private key is kept outside the repository,
  readable only by the holder's account, and is never placed in the repository, chat,
  issues, pull requests, or evidence. The likely accidental locations (`/key.pem`,
  `/extension.pem` and `/extension/key.pem`) are git-ignored as a safeguard.
- The backup arrangement for recovery is confirmed privately with Trixia.
- The private key is not needed to build, install or run the extension. It is only
  needed to publish to the Chrome Web Store under this same ID.

## Rotation

If the private key is exposed or lost and a Web Store release under this ID is
needed, generate a new key pair, replace `key` in the manifest, update
`EXPECTED_EXTENSION_ID` in the identity test and this document, and have the Auth
owner replace the trusted origin. Installs built from the old key keep the old ID
until they are rebuilt from the new manifest.

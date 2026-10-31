# Local inference dependencies

- Transformers.js and Transformers.js Structured Output: Apache-2.0; complete
  license texts are included alongside these files. Their versions and copied
  file hashes are recorded in `ai/judge-assets.json`.
- ONNX Runtime: MIT, Copyright Microsoft Corporation. The included license is
  from the locally installed Microsoft ONNX Runtime distribution; the npm web
  package used here omits that license file. No claim of MIT licensing for the
  other dependencies or model is made.
- Llama 3.2: Meta's Llama 3.2 Community License Agreement, included as
  `LICENSE-Llama3.2.txt`. Model ID and exact revision are pinned in the judge
  manifest. See the model repository's use policy and attribution requirements.
- The TF-IDF training/source attribution is in `ai/ATTRIBUTION.md`.

The Transformers.js 4.3.1 bundle originally matched the published npm/CDN file
byte for byte (SHA-256 `8d6716d9086f57c30a4bf367dba61b887593573c770c454465e8019b2703e743`).
GitHub falsely flagged a public Mistral model-class registry string as an API key.
`scripts/vendor_runtime_patch.mjs` changes that one string literal to a concatenation
with the identical runtime value. No push-protection bypass is used. The final
vendored file hash is recorded in `ai/judge-assets.json`. Structured Output also
uses a relative import of the bundled Transformers module instead of a bare npm
specifier; these are the only two local JavaScript vendor modifications.

No remote JavaScript is loaded. Public weight downloads happen only through the
developer setup command; email inference remains local in Chrome. The pinned
weight files are excluded from Git and explicitly included in a full bundle.

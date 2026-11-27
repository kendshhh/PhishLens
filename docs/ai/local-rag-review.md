# Local guidance for the on-device review

The browser runs TF-IDF screening, retrieves up to three guidance cards with BM25, and passes the cards to the existing on-device Llama judge before TF-IDF, KRR, and LightGBM reevaluation. The six cards are bundled with the extension. **Analysis details → Local guidance retrieved for this review** shows the cards the judge received.

Email text stays in the browser during the scan. The judge still cites a quote from the email and applies the existing review rules. If retrieval finds no match, the judge receives no cards. If cards would put the prompt over 1,536 tokens, it drops the lowest-ranked cards first. A retrieval error leaves the judge and reevaluators available.

## Demo verification

The feature uses the same retrieval, judge, workflow, and UI files tested in Chrome 158 with the full model bundle based on PR #293 at `6056419bae22507a4dd922feb19185e5d7c97d9a`. The three synthetic checks covered suspicious with guidance, no strong warning signs with no retrieval match, and uncertain with guidance when classifiers disagreed. The demo ZIP SHA-256 is `6f9a7cceadeaa24f989f6dad0f6590fe80731ec94170cd81387655c6c8e9eb00`.

For an unpacked Chrome check from source, follow the model setup in [the extension journey](../extension-journey.md). Open PhishLens, paste an example into **Check email**, then open **Analysis details**. Hosted Auth and CRUD and representative holdout scoring are outside the scope of these demo checks.

import { saveAnalysisAndRefresh } from './report-client.js';

// Check capability without sending text, then require the same model at POST.
// The server enforces the header even if its configuration changes meanwhile.
export async function saveLocalReport({ client, baseUrl, modelSha, input, idempotencyKey,
    fetchImpl = fetch }) {
    const response = await fetchImpl(`${baseUrl.replace(/\/+$/, '')}/model-info`, {
        signal: AbortSignal.timeout(10000)
    });
    if (!response.ok) throw new Error('The save service could not be checked. The local scan is retained.');
    const info = await response.json();
    if (info.provider_mode !== 'tfidf' || info.accepts_tfidf_reports !== true || info.model_sha256 !== modelSha) {
        throw new Error('Saving is disabled: the server needs the matching TF-IDF v12a model. The local scan still works.');
    }
    return saveAnalysisAndRefresh(client, input, { idempotencyKey });
}

import { saveAnalysisAndRefresh } from './report-client.js';

// Check capability without sending text, then require the same model at POST.
// The server enforces the header even if its configuration changes meanwhile.
export async function saveLocalReport({ client, baseUrl, modelSha, input, idempotencyKey, beforeCreate,
    fetchImpl = fetch }) {
    try {
        const response = await fetchImpl(`${baseUrl.replace(/\/+$/, '')}/model-info`, {
            signal: AbortSignal.timeout(10000), redirect: 'error'
        });
        if (!response.ok) throw new Error('Unavailable capability');
        const info = await response.json();
        if (info?.provider_mode !== 'tfidf' || info.accepts_tfidf_reports !== true || info.model_sha256 !== modelSha ||
            (input.local_review && info.accepts_local_reviews !== true)) throw new Error('Incompatible capability');
    } catch {
        const error = new Error('Report saving is temporarily unavailable. Your local result is still here. Please try again later.');
        error.code = 'save_service_unavailable';
        throw error;
    }
    if (beforeCreate) await beforeCreate();
    return saveAnalysisAndRefresh(client, input, { idempotencyKey });
}

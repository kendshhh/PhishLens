import { getAnalyses } from '../extension/js/api.js';

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

function isTransientHistoryFailure(error) {
    return error?.origin === 'network' || error?.origin === 'timeout' ||
        error?.status === 408 || error?.status === 425 || error?.status === 429 ||
        (error?.status >= 500 && error.status <= 599);
}

export async function readStagingHistory(baseUrl, fetchImpl = globalThis.fetch, {
    attempts = 6,
    delayMs = 1000,
    timeoutMs = 5000,
} = {}) {
    if (!Number.isSafeInteger(attempts) || attempts < 1) {
        throw new Error('History endpoint attempts must be a positive integer');
    }
    if (!Number.isSafeInteger(delayMs) || delayMs < 0) {
        throw new Error('History retry delay must be a nonnegative integer');
    }

    for (let attempt = 1; attempt <= attempts; attempt++) {
        try {
            return await getAnalyses(baseUrl, {
                fetchImpl,
                timeoutMs,
                retries: 0,
            });
        } catch (error) {
            error.attempt = attempt;
            error.attempts = attempt;
            error.maxAttempts = attempts;

            if (error.status === 401) {
                const challenge = error.wwwAuthenticate || '';
                if (!/^\s*Bearer(?:\s|$)/i.test(challenge)) {
                    error.code = 'history_missing_bearer_challenge';
                    error.message += '; anonymous history returned HTTP 401 without a Bearer challenge';
                    throw error;
                }
                return null;
            }

            if (attempt === attempts || !isTransientHistoryFailure(error)) throw error;
            await delay(delayMs);
        }
    }

    throw new Error('History endpoint attempts exhausted');
}

import { getAnalyses } from '../extension/js/api.js';

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

function isTransient(error) {
  return error?.origin === 'network' || error?.origin === 'timeout' ||
    error?.status === 408 || error?.status === 425 || error?.status === 429 ||
    (error?.status >= 500 && error.status <= 599);
}

/**
 * Wait for GET /api/analyses to become available after health/readiness pass.
 * A 401 is returned as an expected endpoint response so the caller can check
 * the authentication challenge; successful 200 responses are schema-validated
 * by the same client used by the extension.
 */
export async function waitForHistoryEndpoint(baseUrl, {
  fetchImpl = globalThis.fetch,
  attempts = 60,
  delayMs = 3000,
  timeoutMs = 10000,
} = {}) {
  if (!Number.isSafeInteger(attempts) || attempts < 1) {
    throw new Error('History endpoint attempts must be a positive integer');
  }
  if (!Number.isSafeInteger(delayMs) || delayMs < 0) {
    throw new Error('History endpoint delay must be a nonnegative integer');
  }

  for (let attempt = 1; attempt <= attempts; attempt++) {
    try {
      const items = await getAnalyses(baseUrl, {
        fetchImpl,
        timeoutMs,
        retries: 0,
      });
      return { status: 200, items, attempt };
    } catch (error) {
      error.attempt = attempt;
      error.attempts = attempt;
      error.maxAttempts = attempts;

      if (error.status === 401) {
        return { status: 401, error, attempt };
      }
      if (attempt === attempts || !isTransient(error)) throw error;
      await delay(delayMs);
    }
  }

  throw new Error('History endpoint attempts exhausted');
}

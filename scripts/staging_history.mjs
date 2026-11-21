export function isRetryableStagingHistoryError(error) {
    // An HTTP response is authoritative: retry only explicitly transient
    // statuses, regardless of phrases in its diagnostic body.
    if (Number.isInteger(error?.status)) {
        return error.status === 408 || error.status === 425 || error.status === 429 ||
            (error.status >= 500 && error.status <= 599);
    }

    // Text matching is reserved for failures that have no HTTP response.
    return /network request|timed out|timeout|ECONNRESET|ECONNREFUSED|fetch failed|aborted/i.test(
        String(error?.message || error)
    );
}

async function responseError(response, message) {
    let body = '';
    try {
        body = (await response.text()).trim().slice(0, 500);
    } catch {}

    const error = new Error(
        `${message} (HTTP ${response.status})${body ? `: ${body}` : ''}`
    );
    error.status = response.status;
    error.responseBody = body;
    return error;
}

export async function readStagingHistory(baseUrl, fetchImpl = globalThis.fetch) {
    const cleanBaseUrl = baseUrl.replace(/\/+$/, '');
    const response = await fetchImpl(`${cleanBaseUrl}/api/analyses`, {
        signal: AbortSignal.timeout(10000),
        redirect: 'error'
    });

    if (response.status === 401) {
        const challenge = response.headers.get('www-authenticate') || '';
        if (!/^\s*Bearer(?:\s|$)/i.test(challenge)) {
            throw await responseError(response, 'Anonymous history returned without a Bearer challenge');
        }
        return null;
    }

    if (!response.ok) {
        throw await responseError(response, 'Failed to load staging history');
    }

    const data = await response.json();
    if (!data || !Array.isArray(data.items)) {
        throw new Error('Invalid staging history data');
    }
    return data.items;
}

function historyError(message, { endpoint, status, wwwAuthenticate, cause } = {}) {
    const error = new Error(message, cause ? { cause } : undefined);
    error.endpoint = endpoint;
    error.status = status;
    error.wwwAuthenticate = wwwAuthenticate;
    return error;
}

export async function readStagingHistory(baseUrl, fetchImpl = globalThis.fetch, { timeoutMs = 10000 } = {}) {
    const cleanBaseUrl = baseUrl.replace(/\/+$/, '');
    const endpoint = `${cleanBaseUrl}/api/analyses`;
    let response;
    try {
        response = await fetchImpl(endpoint, {
            signal: AbortSignal.timeout(timeoutMs),
            redirect: 'error'
        });
    } catch (cause) {
        const reason = cause instanceof Error ? cause.message : String(cause);
        throw historyError(`Failed to load staging history: network request to ${endpoint} failed (${reason})`, {
            endpoint,
            cause
        });
    }

    if (response.status === 401) {
        const challenge = response.headers?.get?.('www-authenticate') || '';
        if (!/^\s*Bearer(?:\s|$)/i.test(challenge)) {
            throw historyError(`Anonymous history at ${endpoint} returned HTTP 401 without a Bearer challenge`, {
                endpoint,
                status: 401,
                wwwAuthenticate: challenge
            });
        }
        return null;
    }

    if (!response.ok) {
        let detail = '';
        try {
            detail = (await response.text()).trim().slice(0, 500);
        } catch {}
        throw historyError(
            `Failed to load staging history: ${endpoint} returned HTTP ${response.status}${detail ? `: ${detail}` : ''}`,
            { endpoint, status: response.status, wwwAuthenticate: response.headers?.get?.('www-authenticate') || '' }
        );
    }

    let data;
    try {
        data = await response.json();
    } catch (cause) {
        const reason = cause instanceof Error ? cause.message : String(cause);
        throw historyError(`Invalid staging history JSON from ${endpoint}: ${reason}`, {
            endpoint,
            status: response.status,
            cause
        });
    }
    if (!data || !Array.isArray(data.items)) {
        throw historyError(`Invalid staging history data from ${endpoint}`, {
            endpoint,
            status: response.status
        });
    }
    return data.items;
}

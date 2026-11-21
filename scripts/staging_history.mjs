export async function readStagingHistory(baseUrl, fetchImpl = globalThis.fetch) {
    const cleanBaseUrl = baseUrl.replace(/\/+$/, '');
    const response = await fetchImpl(`${cleanBaseUrl}/api/analyses`, {
        signal: AbortSignal.timeout(10000),
        redirect: 'error'
    });

    if (response.status === 401) {
        const challenge = response.headers.get('www-authenticate') || '';
        if (!/^\s*Bearer(?:\s|$)/i.test(challenge)) {
            throw new Error('Anonymous history returned HTTP 401 without a Bearer challenge');
        }
        return null;
    }

    if (!response.ok) {
        throw new Error(`Failed to load staging history (HTTP ${response.status})`);
    }

    const data = await response.json();
    if (!data || !Array.isArray(data.items)) {
        throw new Error('Invalid staging history data');
    }
    return data.items;
}

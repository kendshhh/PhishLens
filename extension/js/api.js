function isValidUuid(value) {
    const uuidPattern =
        /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

    return typeof value === "string" && uuidPattern.test(value);
}

function isValidUtcTimestamp(value) {
    if (typeof value !== "string") {
        return false;
    }

    const timestampPattern =
        /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)$/;

    if (!timestampPattern.test(value)) {
        return false;
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return false;
    }

    // Reject impossible dates that JavaScript silently adjusts.
    return date.toISOString().slice(0, 19) === value.slice(0, 19);
}

function isValidAnalysis(analysis) {
    if (!analysis || typeof analysis !== "object") {
        return false;
    }

    if (
        !isValidUuid(analysis.id) ||
        typeof analysis.subject !== "string"
    ) {
        return false;
    }

    const predictions = ["phishing", "legitimate", "spam"];

    if (
        analysis.prediction !== null &&
        !predictions.includes(analysis.prediction)
    ) {
        return false;
    }

    if (analysis.confidence !== null) {
        if (
            typeof analysis.confidence !== "number" ||
            !Number.isFinite(analysis.confidence) ||
            analysis.confidence < 0 ||
            analysis.confidence > 1
        ) {
            return false;
        }
    }

    const riskLevels = ["low", "medium", "high", "critical"];

    if (
        analysis.risk_level !== null &&
        !riskLevels.includes(analysis.risk_level)
    ) {
        return false;
    }

    if (!Array.isArray(analysis.threat_indicators)) {
        return false;
    }

    for (const indicator of analysis.threat_indicators) {
        if (
            !indicator ||
            typeof indicator.type !== "string" ||
            typeof indicator.detail !== "string" ||
            (indicator.quote !== undefined && typeof indicator.quote !== "string")
        ) {
            return false;
        }
    }

    if (
        analysis.explanation !== null &&
        typeof analysis.explanation !== "string"
    ) {
        return false;
    }

    if (!isValidUtcTimestamp(analysis.created_at)) {
        return false;
    }
    if (analysis.review_status !== undefined && analysis.review_status !== null &&
        !['released', 'uncertain'].includes(analysis.review_status)) return false;

    return true;
}

export async function getAnalyses(baseUrl) {
    const cleanBaseUrl = baseUrl.replace(/\/+$/, "");

    const response = await fetch(
        `${cleanBaseUrl}/api/analyses`,
        { signal: AbortSignal.timeout(10000), redirect: 'error' }
    );

    if (!response.ok) {
        throw new Error("Failed to load history");
    }

    const data = await response.json();

    if (!data || !Array.isArray(data.items)) {
        throw new Error("Invalid history data");
    }

    for (const analysis of data.items) {
        if (!isValidAnalysis(analysis)) {
            throw new Error("Invalid history data");
        }
    }

    return data.items;
}

export function createAnalysisClient(baseUrl, fetchImpl = globalThis.fetch, { createTimeoutMs = 25000, requiredModel, getAccessToken } = {}) {
    if (!Number.isSafeInteger(createTimeoutMs) || createTimeoutMs < 1 || createTimeoutMs > 2147483647) {
        throw new Error('Create timeout must be a positive integer in milliseconds');
    }
    if (getAccessToken !== undefined && typeof getAccessToken !== 'function') {
        throw new TypeError('getAccessToken must be a function');
    }
    const url = baseUrl.replace(/\/+$/, '') + '/api/analyses';
    const pendingCreateKeys = new Map();

    async function request(path, method, expectedStatus, body, timeoutMs = 10000, headers = {}) {
        let authorization;
        if (getAccessToken !== undefined) {
            let token;
            try {
                token = await getAccessToken();
            } catch {
                const error = new Error('Unable to access your session. Try signing in again.');
                error.code = 'session_unavailable';
                throw error;
            }
            if (typeof token !== 'string' || !/^[A-Za-z0-9._~+/-]+=*$/.test(token)) {
                const error = new Error('Sign in to access saved analyses.');
                error.status = 401;
                error.code = 'authentication_required';
                throw error;
            }
            authorization = { Authorization: 'Bearer ' + token };
        }
        const options = { method, signal: AbortSignal.timeout(timeoutMs), redirect: 'error' };
        if (authorization) options.headers = authorization;
        if (body !== undefined) {
            options.headers = { 'Content-Type': 'application/json', ...headers, ...authorization };
            options.body = JSON.stringify(body);
        }
        const response = await fetchImpl(path, options);
        if (getAccessToken !== undefined && response.status === 401) {
            const error = new Error('Your session has expired. Sign in again.');
            error.status = 401;
            error.code = 'authentication_required';
            throw error;
        }
        if (!response.ok) {
            let message = 'Request failed (HTTP ' + response.status + ')';
            try {
                const errorBody = await response.json();
                if (typeof errorBody?.detail === 'string' && errorBody.detail.trim()) {
                    message = errorBody.detail;
                }
            } catch {
                // Some servers return an empty or non-JSON error body.
            }
            const error = new Error(message);
            error.status = response.status;
            throw error;
        }
        if (response.status !== expectedStatus) {
            const error = new Error('Unexpected response status: ' + response.status);
            error.status = response.status;
            throw error;
        }
        if (expectedStatus === 204) return;
        return response.json();
    }

    function recordUrl(id) {
        if (!isValidUuid(id)) throw new Error('A valid analysis UUID is required');
        return url + '/' + encodeURIComponent(id);
    }

    function checkRecord(record, detail = false) {
        if (!isValidAnalysis(record)) throw new Error('Invalid analysis data');
        if (detail && (
            typeof record.body !== 'string' ||
            !(record.notes === null || typeof record.notes === 'string') ||
            ![null, 'none', 'false_positive', 'false_negative'].includes(record.feedback) ||
            !['mock', 'real', 'unknown', null].includes(record.analysis_mode) ||
            (record.analysis_provenance !== undefined && record.analysis_provenance !== null &&
                (typeof record.analysis_provenance !== 'object' || Array.isArray(record.analysis_provenance)))
        )) {
            throw new Error('Invalid analysis detail');
        }
        return record;
    }

    return {
        async listAnalyses() {
            const data = await request(url, 'GET', 200);
            if (!data || !Array.isArray(data.items)) throw new Error('Invalid history data');
            return data.items.map(record => checkRecord(record));
        },
        async getAnalysis(id) {
            return checkRecord(await request(recordUrl(id), 'GET', 200), true);
        },
        async createAnalysis(input, { idempotencyKey } = {}) {
            const fingerprint = JSON.stringify([input?.subject ?? '', input?.body, input?.local_review ?? null]);
            const automaticKey = idempotencyKey === undefined;
            const key = idempotencyKey ?? pendingCreateKeys.get(fingerprint) ?? globalThis.crypto.randomUUID();
            if (automaticKey) pendingCreateKeys.set(fingerprint, key);

            try {
                const created = checkRecord(
                    await request(
                        url,
                        'POST',
                        201,
                        input,
                        createTimeoutMs,
                        { 'Idempotency-Key': key, ...(requiredModel ? { 'X-PhishLens-Model': requiredModel } : {}) }
                    ),
                    true
                );
                if (pendingCreateKeys.get(fingerprint) === key) pendingCreateKeys.delete(fingerprint);
                return created;
            } catch (error) {
                if (automaticKey && error?.status >= 400 && error.status < 500 &&
                    ![408, 409, 425, 429].includes(error.status) &&
                    pendingCreateKeys.get(fingerprint) === key) {
                    pendingCreateKeys.delete(fingerprint);
                }
                if (error && typeof error === 'object') {
                    error.idempotencyKey = key;
                }
                throw error;
            }
        },
        async updateAnalysis(id, patch) {
            return checkRecord(await request(recordUrl(id), 'PATCH', 200, patch), true);
        },
        async deleteAnalysis(id) {
            await request(recordUrl(id), 'DELETE', 204);
        }
    };
}

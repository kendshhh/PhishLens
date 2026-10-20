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

    const predictions = ["phishing", "legitimate"];

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
            typeof indicator.detail !== "string"
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

    return true;
}



export async function getAnalyses(baseUrl) {
    const response = await fetch(
        `${baseUrl}/api/analyses`,
        { signal: AbortSignal.timeout(10000) }
    );

    if (!response.ok) {
        throw new Error("Failed to load history");
    }

    const data = await response.json();

    if (!data || !Array.isArray(data.items)) {
        throw new Error("Invalid history data");
    }

    return data.items;
}


export function createAnalysisClient(baseUrl, fetchImpl = globalThis.fetch) {
    const url = baseUrl.replace(/\/+$/, '') + '/api/analyses';

    async function request(path, method, expectedStatus, body) {
        const options = { method, signal: AbortSignal.timeout(10000) };
        if (body !== undefined) {
            options.headers = { 'Content-Type': 'application/json' };
            options.body = JSON.stringify(body);
        }
        const response = await fetchImpl(path, options);
        if (!response.ok) {
            let message = 'Request failed (HTTP ' + response.status + ')';
            try {
                const errorBody = await response.json();
                if (typeof errorBody?.detail === 'string') message = errorBody.detail;
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
            !['none', 'false_positive', 'false_negative'].includes(record.feedback) ||
            !['mock', 'real', 'unknown', null].includes(record.analysis_mode)
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
        async createAnalysis(input) {
            return checkRecord(await request(url, 'POST', 201, input), true);
        },
        async updateAnalysis(id, patch) {
            return checkRecord(await request(recordUrl(id), 'PATCH', 200, patch), true);
        },
        async deleteAnalysis(id) {
            await request(recordUrl(id), 'DELETE', 204);
        }
    };
}

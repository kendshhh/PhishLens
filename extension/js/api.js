function isValidAnalysis(analysis) {
    if (!analysis || typeof analysis !== "object") {
        return false;
    }

    if (
        typeof analysis.id !== "string" ||
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

    if (
        typeof analysis.created_at !== "string" ||
        Number.isNaN(Date.parse(analysis.created_at))
    ) {
        return false;
    }

    return true;
}

export async function getAnalyses(baseUrl) {
    const cleanBaseUrl = baseUrl.replace(/\/+$/, "");

    const response = await fetch(
        `${cleanBaseUrl}/api/analyses`,
        { signal: AbortSignal.timeout(10000) }
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
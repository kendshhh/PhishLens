
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

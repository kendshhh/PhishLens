export async function saveAnalysisAndRefresh(client, input, options) {
    const saved = await client.createAnalysis(input, options);
    const [detailResult, historyResult] = await Promise.allSettled([
        client.getAnalysis(saved.id),
        client.listAnalyses()
    ]);

    const refreshErrors = [];
    if (detailResult.status === 'rejected') {
        refreshErrors.push({ operation: 'detail', error: detailResult.reason });
    }
    if (historyResult.status === 'rejected') {
        refreshErrors.push({ operation: 'history', error: historyResult.reason });
    }

    return {
        saved,
        detail: detailResult.status === 'fulfilled' ? detailResult.value : null,
        history: historyResult.status === 'fulfilled' ? historyResult.value : null,
        refreshErrors
    };
}


import test from 'node:test';
import assert from 'node:assert/strict';
import { saveAnalysisAndRefresh } from '../js/report-client.js';

const saved = {
    id: '29d80c39-ec0d-4db8-a6e5-87444ba2600c',
    subject: '', body: 'Synthetic body', analysis_mode: 'mock',
    prediction: 'spam', confidence: null, analysis_provenance: { provider_mode: 'mock' }
};
const input = Object.freeze({ body: saved.body });

function setup(overrides = {}) {
    const calls = [];
    const client = {
        async createAnalysis(body, options) {
            calls.push(['create', body, options]);
            return saved;
        },
        async getAnalysis(id) {
            calls.push(['detail', id]);
            return saved;
        },
        async listAnalyses() {
            calls.push(['history']);
            return [saved];
        },
        ...overrides
    };
    return { client, calls };
}

test('creates once and refreshes using the returned server ID', async () => {
    const { client, calls } = setup();
    const result = await saveAnalysisAndRefresh(client, input);
    assert.deepEqual(calls, [['create', input, undefined], ['detail', saved.id], ['history']]);
    assert.deepEqual(result, { saved, detail: saved, history: [saved], refreshErrors: [] });
    assert.deepEqual(input, { body: saved.body });
});

test('forwards a retained retry key without generating or changing it', async () => {
    const { client, calls } = setup();
    const options = { idempotencyKey: 'retained-request-key' };
    await saveAnalysisAndRefresh(client, input, options);
    assert.equal(calls[0][2], options);
});

test('detail refresh failure preserves the saved report and successful history', async () => {
    const error = new Error('Detail unavailable');
    const { client, calls } = setup({ getAnalysis: async () => { throw error; } });
    const result = await saveAnalysisAndRefresh(client, input);
    assert.equal(result.saved, saved);
    assert.equal(result.detail, null);
    assert.deepEqual(result.history, [saved]);
    assert.deepEqual(result.refreshErrors, [{ operation: 'detail', error }]);
    assert.equal(calls.filter(([operation]) => operation === 'create').length, 1);
});

test('history refresh failure is not returned as successful empty history', async () => {
    const error = new Error('History unavailable');
    const { client } = setup({ listAnalyses: async () => { throw error; } });
    const result = await saveAnalysisAndRefresh(client, input);
    assert.equal(result.saved, saved);
    assert.equal(result.detail, saved);
    assert.equal(result.history, null);
    assert.deepEqual(result.refreshErrors, [{ operation: 'history', error }]);
});

test('both refresh failures preserve the server-confirmed save', async () => {
    const detailError = new Error('Detail failed');
    const historyError = new Error('History failed');
    const { client } = setup({
        getAnalysis: async () => { throw detailError; },
        listAnalyses: async () => { throw historyError; }
    });
    const result = await saveAnalysisAndRefresh(client, input);
    assert.equal(result.saved.id, saved.id);
    assert.deepEqual(result.refreshErrors, [
        { operation: 'detail', error: detailError },
        { operation: 'history', error: historyError }
    ]);
});

for (const status of [409, 422, 502, 503, 504]) {
    test('create HTTP ' + status + ' propagates without refresh or resubmission', async () => {
        const error = Object.assign(new Error('Controlled failure'), {
            status, idempotencyKey: 'retain-after-failure'
        });
        let creates = 0;
        const { client, calls } = setup({
            createAnalysis: async () => { creates++; throw error; }
        });
        await assert.rejects(saveAnalysisAndRefresh(client, input), actual => actual === error);
        assert.equal(creates, 1);
        assert.deepEqual(calls, []);
        assert.deepEqual(input, { body: saved.body });
    });
}

test('network/timeout error retains its identity and retry key', async () => {
    const error = Object.assign(new DOMException('Synthetic timeout', 'TimeoutError'),
        { idempotencyKey: 'uncertain-create-key' });
    const { client, calls } = setup({ createAnalysis: async () => { throw error; } });
    await assert.rejects(saveAnalysisAndRefresh(client, input), actual => actual === error);
    assert.deepEqual(calls, []);
});

test('keeps completion pending until the requested refreshes settle', async () => {
    let finishDetail;
    let finishHistory;
    const { client } = setup({
        getAnalysis: () => new Promise(resolve => { finishDetail = resolve; }),
        listAnalyses: () => new Promise(resolve => { finishHistory = resolve; })
    });
    let finished = false;
    const pending = saveAnalysisAndRefresh(client, input).then(result => {
        finished = true;
        return result;
    });
    await Promise.resolve();
    finishDetail(saved);
    await Promise.resolve();
    assert.equal(finished, false);
    finishHistory([]);
    const result = await pending;
    assert.deepEqual(result.history, []);
    assert.deepEqual(result.refreshErrors, []);
});


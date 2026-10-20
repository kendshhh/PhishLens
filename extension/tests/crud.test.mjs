import test from 'node:test';
import assert from 'node:assert/strict';
import { createAnalysisClient } from '../js/api.js';

const id = '29d80c39-ec0d-4db8-a6e5-87444ba2600c';
const record = {
    id, subject: 'Synthetic notice', prediction: 'phishing', confidence: 0.93,
    risk_level: 'high', threat_indicators: [{ type: 'link', detail: 'Synthetic link' }],
    explanation: 'Synthetic test', created_at: '2026-10-13T15:07:51.365605+00:00',
    body: 'Synthetic email body', notes: null, feedback: 'none', analysis_mode: 'mock'
};

function setup(status, data, jsonError) {
    const calls = [];
    const client = createAnalysisClient('https://example.test/', async (url, options) => {
        calls.push({ url, ...options });
        return {
            ok: status >= 200 && status < 300, status,
            json: async () => {
                if (jsonError) throw jsonError;
                return data;
            }
        };
    });
    return { client, calls };
}

test('lists records and normalizes the base URL', async () => {
    const { client, calls } = setup(200, { items: [record] });
    assert.deepEqual(await client.listAnalyses(), [record]);
    assert.equal(calls[0].url, 'https://example.test/api/analyses');
    assert.equal(calls[0].method, 'GET');
    assert.equal(calls[0].body, undefined);
    assert.ok(calls[0].signal instanceof AbortSignal);
});

test('accepts an empty list', async () => {
    assert.deepEqual(await setup(200, { items: [] }).client.listAnalyses(), []);
});

test('gets one detail record', async () => {
    const { client, calls } = setup(200, record);
    assert.deepEqual(await client.getAnalysis(id), record);
    assert.equal(calls[0].url, 'https://example.test/api/analyses/' + id);
    assert.equal(calls[0].method, 'GET');
});

test('creates with POST JSON and accepts 201', async () => {
    const { client, calls } = setup(201, record);
    const input = { subject: record.subject, body: record.body };
    assert.deepEqual(await client.createAnalysis(input), record);
    assert.equal(calls[0].method, 'POST');
    assert.equal(calls[0].headers['Content-Type'], 'application/json');
    assert.deepEqual(JSON.parse(calls[0].body), input);
});

test('patches notes and feedback without adding omitted fields', async () => {
    const patch = { notes: 'Reviewed', feedback: 'false_positive' };
    const updated = { ...record, ...patch };
    const { client, calls } = setup(200, updated);
    assert.deepEqual(await client.updateAnalysis(id, patch), updated);
    assert.equal(calls[0].method, 'PATCH');
    assert.equal(calls[0].url, 'https://example.test/api/analyses/' + id);
    assert.deepEqual(JSON.parse(calls[0].body), patch);
});

test('sends null notes to clear them', async () => {
    const { client, calls } = setup(200, record);
    await client.updateAnalysis(id, { notes: null });
    assert.deepEqual(JSON.parse(calls[0].body), { notes: null });
});

test('deletes with 204 and never parses its empty body', async () => {
    const { client, calls } = setup(204, undefined, new Error('Must not parse'));
    assert.equal(await client.deleteAnalysis(id), undefined);
    assert.equal(calls[0].method, 'DELETE');
    assert.equal(calls[0].url, 'https://example.test/api/analyses/' + id);
    assert.equal(calls[0].body, undefined);
});

for (const status of [404, 422, 503]) {
    test('preserves HTTP ' + status + ' and readable detail', async () => {
        const { client } = setup(status, { detail: 'Request unavailable' });
        await assert.rejects(client.getAnalysis(id), error => {
            assert.equal(error.status, status);
            assert.equal(error.message, 'Request unavailable');
            return true;
        });
    });
}

test('keeps a useful error for a non-JSON failure', async () => {
    const { client } = setup(503, null, new SyntaxError('Not JSON'));
    await assert.rejects(client.listAnalyses(), error => error.status === 503 && /503/.test(error.message));
});

test('handles FastAPI validation error arrays', async () => {
    const { client } = setup(422, { detail: [{ msg: 'Field required' }] });
    await assert.rejects(client.createAnalysis({}), error => error.status === 422 && /422/.test(error.message));
});

test('rejects malformed success JSON', async () => {
    const { client } = setup(200, null, new SyntaxError('Invalid JSON'));
    await assert.rejects(client.listAnalyses(), SyntaxError);
});

test('propagates network failure', async () => {
    const client = createAnalysisClient('https://example.test', async () => { throw new TypeError('Network unavailable'); });
    await assert.rejects(client.listAnalyses(), /Network unavailable/);
});

test('propagates request timeout', async () => {
    const client = createAnalysisClient('https://example.test', async () => { throw new DOMException('Request timed out', 'TimeoutError'); });
    await assert.rejects(client.listAnalyses(), { name: 'TimeoutError' });
});

for (const data of [null, {}, { items: {} }, { items: [null] }]) {
    test('rejects malformed list ' + JSON.stringify(data), async () => {
        await assert.rejects(setup(200, data).client.listAnalyses(), /Invalid/);
    });
}

for (const patch of [
    { id: 'not-a-uuid' }, { created_at: '0' }, { confidence: '0.93' },
    { confidence: 2 }, { prediction: 'spam' }, { risk_level: 'unknown' },
    { threat_indicators: ['link'] }
]) {
    test('rejects invalid record ' + JSON.stringify(patch), async () => {
        await assert.rejects(setup(200, { items: [{ ...record, ...patch }] }).client.listAnalyses(), /Invalid/);
    });
}

for (const field of ['body', 'notes', 'feedback', 'analysis_mode']) {
    test('requires detail field ' + field, async () => {
        const incomplete = { ...record };
        delete incomplete[field];
        await assert.rejects(setup(200, incomplete).client.getAnalysis(id), /Invalid analysis detail/);
    });
}

test('accepts nullable results and legacy unknown mode', async () => {
    const pending = { ...record, prediction: null, confidence: null, risk_level: null, explanation: null, analysis_mode: null };
    assert.deepEqual(await setup(200, pending).client.getAnalysis(id), pending);
});

test('rejects invalid IDs before making requests', async () => {
    const { client, calls } = setup(200, record);
    await assert.rejects(client.getAnalysis('../other'), /UUID/);
    assert.equal(calls.length, 0);
});

test('rejects unexpected success statuses', async () => {
    await assert.rejects(setup(200, record).client.createAnalysis({ subject: 'Test', body: 'Test' }), /Unexpected response status/);
});

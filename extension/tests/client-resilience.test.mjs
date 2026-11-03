import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { createAnalysisClient, getAnalyses } from '../js/api.js';

const id = '29d80c39-ec0d-4db8-a6e5-87444ba2600c';
const record = {
    id, subject: 'Synthetic resilience check', body: 'Synthetic test body.',
    prediction: 'spam', confidence: null, risk_level: 'medium',
    threat_indicators: [], explanation: null, created_at: '2026-11-02T01:00:00Z',
    notes: null, feedback: null, analysis_mode: 'mock',
    analysis_provenance: { provider_mode: 'mock', model: null }
};

async function serve(t, handler) {
    const server = createServer(handler);
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    t.after(() => new Promise(resolve => {
        server.closeAllConnections();
        server.close(resolve);
    }));
    return 'http://127.0.0.1:' + server.address().port;
}

for (const detail of ['', '   ']) {
    test('HTTP errors retain readable status when detail is ' + JSON.stringify(detail), async () => {
        const client = createAnalysisClient('https://example.test', async () => ({
            ok: false, status: 503, json: async () => ({ detail })
        }));
        await assert.rejects(client.listAnalyses(), error =>
            error.status === 503 && error.message === 'Request failed (HTTP 503)');
    });
}

for (const method of ['history', 'list', 'create']) {
    test(method + ' refuses HTTP redirects without reaching the destination', async t => {
        let destinationCalls = 0;
        const origin = await serve(t, (request, response) => {
            if (request.url === '/destination') {
                destinationCalls++;
                response.writeHead(request.method === 'POST' ? 201 : 200, { 'Content-Type': 'application/json' });
                response.end(JSON.stringify(request.method === 'POST' ? record : { items: [record] }));
                return;
            }
            response.writeHead(307, { Location: '/destination' });
            response.end();
        });
        const client = createAnalysisClient(origin);
        await assert.rejects(
            method === 'history' ? getAnalyses(origin) :
            method === 'list' ? client.listAnalyses() :
            client.createAnalysis({ subject: record.subject, body: record.body })
        );
        assert.equal(destinationCalls, 0);
    });
}

test('timed-out create keeps one key for an explicit retry with no automatic POST', async t => {
    const keys = [];
    let stored = false;
    const origin = await serve(t, (request, response) => {
        keys.push(request.headers['idempotency-key']);
        stored = true;
        if (keys.length === 1) return;
        response.writeHead(201, { 'Content-Type': 'application/json' });
        response.end(JSON.stringify(record));
    });
    const client = createAnalysisClient(origin, fetch, { createTimeoutMs: 200 });
    const input = { subject: record.subject, body: record.body };
    let retryKey;
    await assert.rejects(client.createAnalysis(input), error => {
        retryKey = error.idempotencyKey;
        return ['TimeoutError', 'AbortError'].includes(error.name);
    });
    assert.equal(keys.length, 1);
    assert.equal(stored, true);
    assert.equal(typeof retryKey, 'string');
    const saved = await client.createAnalysis(input, { idempotencyKey: retryKey });
    assert.equal(saved.id, id);
    assert.deepEqual(keys, [retryKey, retryKey]);
    assert.deepEqual(input, { subject: record.subject, body: record.body });
});

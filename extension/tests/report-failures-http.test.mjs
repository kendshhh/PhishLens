import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { createAnalysisClient } from '../js/api.js';
import { saveAnalysisAndRefresh } from '../js/report-client.js';

const input = { subject: '', body: 'Synthetic report failure check' };
const saved = {
    id: '29d80c39-ec0d-4db8-a6e5-87444ba2600c', ...input,
    prediction: 'spam', confidence: null, risk_level: 'medium',
    threat_indicators: [], explanation: null, created_at: '2026-11-02T10:00:00Z',
    notes: null, feedback: null, analysis_mode: 'mock',
    analysis_provenance: { provider_mode: 'mock' }
};

async function fixture(t, handle, options) {
    const calls = [];
    const server = createServer(async (request, response) => {
        let body = '';
        for await (const chunk of request) body += chunk;
        calls.push({ method: request.method, path: request.url, body,
            key: request.headers['idempotency-key'] });
        handle(request, response, calls);
    });
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    t.after(() => new Promise(resolve => {
        server.closeAllConnections();
        server.close(resolve);
    }));
    return { calls, client: createAnalysisClient(
        'http://127.0.0.1:' + server.address().port, globalThis.fetch, options
    ) };
}

function send(response, status, body) {
    response.writeHead(status, { 'Content-Type': 'application/json' });
    response.end(JSON.stringify(body));
}

for (const [status, detail] of [
    [422, 'Email body is invalid'],
    [502, 'Inference failed'],
    [503, 'Analysis storage is unavailable'],
    [504, 'Analysis processing timed out']
]) {
    test(`saved-report HTTP ${status} rejects without refresh or automatic POST retry`, async t => {
        const { client, calls } = await fixture(t, (_request, response) => send(response, status, { detail }));
        const original = structuredClone(input);
        await assert.rejects(saveAnalysisAndRefresh(client, input), error => {
            assert.equal(error.status, status);
            assert.equal(error.message, detail);
            assert.equal(error.idempotencyKey, calls[0].key);
            return true;
        });
        assert.deepEqual(input, original);
        assert.equal(calls.length, 1);
        assert.equal(calls[0].method, 'POST');
        assert.deepEqual(JSON.parse(calls[0].body), input);
    });
}

test('malformed successful POST retains the retry key and never reports an empty history', async t => {
    const { client, calls } = await fixture(t, (_request, response) => {
        response.writeHead(201, { 'Content-Type': 'application/json' });
        response.end('{');
    });
    await assert.rejects(saveAnalysisAndRefresh(client, input), error => {
        assert.ok(error instanceof SyntaxError);
        assert.equal(error.idempotencyKey, calls[0].key);
        return true;
    });
    assert.equal(calls.length, 1);
});

test('a stalled POST body times out before refresh and preserves the request key', async t => {
    const { client, calls } = await fixture(t, (_request, response) => {
        response.writeHead(201, { 'Content-Type': 'application/json' });
        response.flushHeaders();
        response.write('{');
    }, { createTimeoutMs: 200 });
    await assert.rejects(saveAnalysisAndRefresh(client, input), error => {
        assert.ok(['TimeoutError', 'AbortError'].includes(error.name));
        assert.equal(error.idempotencyKey, calls[0].key);
        return true;
    });
    assert.equal(calls.length, 1);
});

test('simultaneous detail and history failures keep the confirmed save and both original errors', async t => {
    const { client, calls } = await fixture(t, (request, response) => {
        if (request.method === 'POST') send(response, 201, saved);
        else if (request.url.endsWith('/' + saved.id)) send(response, 200, { id: saved.id });
        else send(response, 503, { detail: 'History temporarily unavailable' });
    });
    const result = await saveAnalysisAndRefresh(client, input);
    assert.deepEqual(result.saved, saved);
    assert.equal(result.detail, null);
    assert.equal(result.history, null);
    assert.deepEqual(result.refreshErrors.map(item => item.operation), ['detail', 'history']);
    assert.match(result.refreshErrors[0].error.message, /Invalid analysis/);
    assert.equal(result.refreshErrors[1].error.status, 503);
    assert.equal(result.refreshErrors[1].error.message, 'History temporarily unavailable');
    assert.equal(calls.filter(call => call.method === 'POST').length, 1);
    assert.equal(calls.filter(call => call.method === 'GET').length, 2);
});

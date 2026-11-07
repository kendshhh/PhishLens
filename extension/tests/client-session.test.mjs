import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { createAnalysisClient } from '../js/api.js';
import { saveAnalysisAndRefresh } from '../js/report-client.js';

const id = '29d80c39-ec0d-4db8-a6e5-87444ba2600c';
const record = {
    id, subject: '', body: 'Synthetic content', prediction: 'spam', confidence: null,
    risk_level: 'medium', threat_indicators: [], explanation: null,
    created_at: '2026-11-06T00:00:00Z', notes: null, feedback: null, analysis_mode: 'mock'
};

const operations = [
    ['list', 'GET', 200, { items: [record] }, client => client.listAnalyses()],
    ['detail', 'GET', 200, record, client => client.getAnalysis(id)],
    ['create', 'POST', 201, record, client => client.createAnalysis({ body: record.body }, { idempotencyKey: 'session-test' })],
    ['update', 'PATCH', 200, record, client => client.updateAnalysis(id, { notes: 'Synthetic note' })],
    ['delete', 'DELETE', 204, undefined, client => client.deleteAnalysis(id)]
];

for (const [name, method, status, data, invoke] of operations) {
    test(`${name} sends the supplied token and preserves existing request headers`, async () => {
        let calls = 0;
        const client = createAnalysisClient('https://example.test', async (url, options) => {
            calls++;
            assert.equal(options.method, method);
            assert.equal(options.headers.Authorization, 'Bearer synthetic.jwt.token');
            assert.equal(options.redirect, 'error');
            assert.ok(!url.includes('synthetic.jwt.token'));
            if (method === 'POST') {
                assert.equal(options.headers['Idempotency-Key'], 'session-test');
                assert.equal(options.headers['X-PhishLens-Model'], 'synthetic-model');
                assert.equal(options.headers['Content-Type'], 'application/json');
                assert.deepEqual(JSON.parse(options.body), { body: record.body });
            }
            return { ok: true, status, json: async () => {
                assert.notEqual(status, 204, 'DELETE must not parse JSON');
                return data;
            } };
        }, { getAccessToken: async () => 'synthetic.jwt.token', requiredModel: 'synthetic-model' });
        await invoke(client);
        assert.equal(calls, 1);
    });
}

test('requests obtain the current token and refuse to fetch after sign-out', async () => {
    let token = 'first-token', calls = 0;
    const headers = [];
    const client = createAnalysisClient('https://example.test', async (_url, options) => {
        calls++;
        headers.push(options.headers.Authorization);
        return { ok: true, status: 200, json: async () => ({ items: [] }) };
    }, { getAccessToken: () => token });
    await client.listAnalyses();
    token = 'second-token';
    await client.listAnalyses();
    token = null;
    await assert.rejects(client.listAnalyses(), { status: 401, code: 'authentication_required' });
    assert.equal(calls, 2);
    assert.deepEqual(headers, ['Bearer first-token', 'Bearer second-token']);
});

test('invalid tokens stop before fetch without exposing their contents', async () => {
    for (const token of [null, undefined, '', ' ', 123, 'Bearer already-prefixed', 'private\r\nvalue']) {
        const client = createAnalysisClient('https://example.test', () => {
            assert.fail('An absent or invalid session must not make a request');
        }, { getAccessToken: () => token });
        await assert.rejects(client.listAnalyses(), error => {
            assert.equal(error.status, 401);
            assert.equal(error.code, 'authentication_required');
            assert.equal(error.message, 'Sign in to access saved analyses.');
            return true;
        });
    }
});

test('token lookup failures are redacted and do not become anonymous requests', async () => {
    const client = createAnalysisClient('https://example.test', () => assert.fail('Unexpected fetch'), {
        getAccessToken() { throw new Error('private-token-value'); }
    });
    await assert.rejects(client.listAnalyses(), error => {
        assert.equal(error.code, 'session_unavailable');
        assert.equal(error.status, undefined);
        assert.ok(!error.message.includes('private-token-value'));
        return true;
    });
});

test('session configuration rejects a non-function getter', () => {
    assert.throws(() => createAnalysisClient('https://example.test', fetch, {
        getAccessToken: 'private-token-value'
    }), { name: 'TypeError', message: 'getAccessToken must be a function' });
});

test('unauthenticated compatibility mode adds no Authorization header', async () => {
    const client = createAnalysisClient('https://example.test', async (_url, options) => {
        assert.equal(options.headers, undefined);
        return { ok: true, status: 200, json: async () => ({ items: [] }) };
    });
    assert.deepEqual(await client.listAnalyses(), []);
});

test('HTTP 401 preserves create input and key without refresh or automatic retry', async t => {
    let requests = 0, tokenReads = 0;
    const server = createServer((request, response) => {
        requests++;
        assert.equal(request.method, 'POST');
        assert.equal(request.headers.authorization, 'Bearer synthetic-token');
        request.resume();
        response.writeHead(401, { 'Content-Type': 'application/json' });
        response.end(JSON.stringify({ detail: 'private-server-detail' }));
    });
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    t.after(() => new Promise(resolve => { server.closeAllConnections(); server.close(resolve); }));
    const client = createAnalysisClient('http://127.0.0.1:' + server.address().port, fetch, {
        getAccessToken: () => { tokenReads++; return 'synthetic-token'; }
    });
    const input = { subject: '', body: record.body };
    const original = structuredClone(input);
    await assert.rejects(saveAnalysisAndRefresh(client, input, { idempotencyKey: 'session-test' }), error => {
        assert.equal(error.status, 401);
        assert.equal(error.code, 'authentication_required');
        assert.equal(error.message, 'Your session has expired. Sign in again.');
        assert.equal(error.idempotencyKey, 'session-test');
        return true;
    });
    assert.deepEqual(input, original);
    assert.equal(requests, 1);
    assert.equal(tokenReads, 1);
});

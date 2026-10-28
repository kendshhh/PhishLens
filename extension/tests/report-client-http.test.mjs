import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { createAnalysisClient } from '../js/api.js';
import { saveAnalysisAndRefresh } from '../js/report-client.js';

const id = '29d80c39-ec0d-4db8-a6e5-87444ba2600c';
const input = { subject: 'Synthetic report', body: 'Synthetic body only' };
const record = {
    id, ...input, prediction: 'spam', confidence: null, risk_level: 'medium',
    threat_indicators: [{ type: 'evidence', quote: 'Synthetic body', detail: 'Synthetic reason' }],
    explanation: null, created_at: '2026-10-28T01:00:00Z',
    notes: null, feedback: null, analysis_mode: 'mock',
    analysis_provenance: { provider_mode: 'mock', model: null }
};

async function startServer(t, { failHistory = false, loseFirstAcknowledgement = false } = {}) {
    const keys = [];
    const records = new Map();
    let detailReads = 0;
    const server = createServer(async (request, response) => {
        const send = (status, data) => {
            response.writeHead(status, { 'Content-Type': 'application/json' });
            response.end(JSON.stringify(data));
        };
        if (request.method === 'POST' && request.url === '/api/analyses') {
            let body = '';
            for await (const chunk of request) body += chunk;
            const key = request.headers['idempotency-key'];
            keys.push(key);
            assert.deepEqual(JSON.parse(body), input);
            if (!records.has(key)) records.set(key, structuredClone(record));
            if (loseFirstAcknowledgement && keys.length === 1) {
                request.socket.destroy();
                return;
            }
            send(201, records.get(key));
        } else if (request.url === '/api/analyses/' + id) {
            detailReads++;
            send(200, record);
        } else if (request.url === '/api/analyses') {
            send(failHistory ? 503 : 200, failHistory
                ? { detail: 'History temporarily unavailable' }
                : { items: [record] });
        } else {
            send(404, { detail: 'Not found' });
        }
    });
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    t.after(() => new Promise(resolve => {
        server.closeAllConnections();
        server.close(resolve);
    }));
    return {
        client: createAnalysisClient('http://127.0.0.1:' + server.address().port),
        keys, records, get detailReads() { return detailReads; }
    };
}

test('actual API client and local HTTP: create, detail and history preserve report fields', async t => {
    const fixture = await startServer(t);
    const result = await saveAnalysisAndRefresh(fixture.client, input);
    assert.deepEqual(result.saved, record);
    assert.deepEqual(result.detail, record);
    assert.deepEqual(result.history, [record]);
    assert.deepEqual(result.refreshErrors, []);
    assert.equal(fixture.keys.length, 1);
    assert.match(fixture.keys[0], /^[A-Za-z0-9_-]{1,255}$/);
});

test('actual API client and local HTTP: refresh 503 preserves the confirmed save', async t => {
    const fixture = await startServer(t, { failHistory: true });
    const result = await saveAnalysisAndRefresh(fixture.client, input);
    assert.equal(result.saved.id, id);
    assert.equal(result.detail.id, id);
    assert.equal(result.history, null);
    assert.equal(result.refreshErrors[0].operation, 'history');
    assert.equal(result.refreshErrors[0].error.status, 503);
    assert.equal(fixture.keys.length, 1);
});

test('actual API client and local HTTP: caller retry recovers a lost acknowledgement with the same key', async t => {
    const fixture = await startServer(t, { loseFirstAcknowledgement: true });
    await assert.rejects(saveAnalysisAndRefresh(fixture.client, input),
        error => typeof error.idempotencyKey === 'string');
    assert.equal(fixture.keys.length, 1);
    assert.equal(fixture.detailReads, 0);
    const recovered = await saveAnalysisAndRefresh(fixture.client, input);
    assert.equal(recovered.saved.id, id);
    assert.equal(fixture.keys.length, 2);
    assert.equal(fixture.keys[0], fixture.keys[1]);
    assert.equal(fixture.records.size, 1);
});

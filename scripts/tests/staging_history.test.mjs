import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';

import { classifyHistoryAccess, readStagingHistory, writeHistoryAccessOutput } from '../staging_history.mjs';

const validAnalysis = {
    id: '29d80c39-ec0d-4db8-a6e5-87444ba2600c',
    subject: 'Synthetic account notice',
    prediction: 'phishing',
    confidence: 0.93,
    risk_level: 'high',
    threat_indicators: [],
    explanation: 'Synthetic integration test',
    created_at: '2026-10-14T04:00:00Z',
};

async function serve(t, handler) {
    const server = createServer(handler);
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    t.after(() => new Promise(resolve => {
        server.closeAllConnections();
        server.close(resolve);
    }));
    return `http://127.0.0.1:${server.address().port}`;
}

test('accepts anonymous history rejection when the API requires Bearer auth', async () => {
    const items = await readStagingHistory('https://staging.example.test/', async url => {
        assert.equal(url, 'https://staging.example.test/api/analyses');
        return new Response(JSON.stringify({ detail: 'Sign in to access saved reports' }), {
            status: 401,
            headers: { 'WWW-Authenticate': 'Bearer' },
        });
    });

    assert.equal(items, null);
    assert.equal(classifyHistoryAccess(items), 'auth_required');
});

test('rejects an unauthorized response without a Bearer challenge with diagnostics', async () => {
    await assert.rejects(
        readStagingHistory('https://staging.example.test', async () => new Response(null, { status: 401 })),
        error => error.status === 401 &&
            error.url === 'https://staging.example.test/api/analyses' &&
            error.code === 'history_missing_bearer_challenge' &&
            /without a Bearer challenge/.test(error.message)
    );
});

test('reports other staging history HTTP failures with status and response body', async () => {
    await assert.rejects(
        readStagingHistory('https://staging.example.test', async () =>
            new Response(JSON.stringify({ detail: 'database unavailable' }), { status: 503 }),
        { attempts: 1 }),
        error => error.status === 503 &&
            error.category === 'staging_api_outage' &&
            error.code === 'history_http_5xx' &&
            error.url === 'https://staging.example.test/api/analyses' &&
            /database unavailable/.test(error.responseBody)
    );
});

test('returns schema-valid seeded history items in demo mode', async () => {
    const expected = [validAnalysis];
    const items = await readStagingHistory('https://staging.example.test', async () =>
        Response.json({ items: expected })
    );

    assert.deepEqual(items, expected);
    assert.equal(classifyHistoryAccess(items), 'anonymous');
});

test('rejects an unexpected history result before selecting a hosted verification path', () => {
    assert.throws(() => classifyHistoryAccess(undefined), /array or null/);
});

test('writes the checked history access mode to a GitHub Actions output file', async t => {
    const directory = await mkdtemp(join(tmpdir(), 'phishlens-history-output-'));
    t.after(() => rm(directory, { recursive: true, force: true }));
    const outputPath = join(directory, 'output');

    await writeHistoryAccessOutput(null, outputPath);

    assert.equal(await readFile(outputPath, 'utf8'), 'history_access_mode=auth_required\n');
});

test('rejects an invalid history response wrapper as a contract mismatch', async () => {
    await assert.rejects(
        readStagingHistory('https://staging.example.test', async () => Response.json({ analyses: [] })),
        error => error.category === 'backend_contract_mismatch' &&
            error.code === 'history_schema_mismatch' &&
            /items array/.test(error.message)
    );
});

test('waits for GET /api/analyses to recover after readiness has passed', async t => {
    let calls = 0;
    const baseUrl = await serve(t, (request, response) => {
        assert.equal(request.url, '/api/analyses');
        calls++;
        if (calls === 1) {
            response.writeHead(503, { 'Content-Type': 'application/json' });
            response.end(JSON.stringify({ detail: 'database is starting' }));
            return;
        }
        response.writeHead(200, { 'Content-Type': 'application/json' });
        response.end(JSON.stringify({ items: [validAnalysis] }));
    });

    const items = await readStagingHistory(baseUrl, fetch, {
        attempts: 3,
        delayMs: 5,
        timeoutMs: 1000,
    });

    assert.deepEqual(items, [validAnalysis]);
    assert.equal(calls, 2);
});

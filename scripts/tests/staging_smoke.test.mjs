import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const smokeScript = fileURLToPath(new URL('../staging_smoke.mjs', import.meta.url));

function sendJson(response, status, value, headers = {}) {
    response.writeHead(status, { 'content-type': 'application/json', ...headers });
    response.end(JSON.stringify(value));
}

async function runSmoke(t, handler, overrides = {}) {
    const server = createServer(handler);
    await new Promise((resolve, reject) => {
        server.once('error', reject);
        server.listen(0, '127.0.0.1', resolve);
    });
    const { port } = server.address();
    const tempDir = await mkdtemp(path.join(os.tmpdir(), 'phishlens-staging-smoke-'));
    const summaryPath = path.join(tempDir, 'summary.md');
    await writeFile(summaryPath, '', 'utf8');
    t.after(async () => {
        server.closeAllConnections();
        await new Promise(resolve => server.close(resolve));
        await rm(tempDir, { recursive: true, force: true });
    });

    const result = await new Promise((resolve, reject) => {
        const child = spawn(process.execPath, [smokeScript], {
            env: {
                ...process.env,
                STAGING_BASE_URL: `http://127.0.0.1:${port}`,
                STAGING_SMOKE_TIMEOUT_MS: '2000',
                STAGING_MAX_ATTEMPTS: '4',
                STAGING_RETRY_DELAY_MS: '10',
                GITHUB_STEP_SUMMARY: summaryPath,
                ...overrides,
            },
            stdio: ['ignore', 'pipe', 'pipe'],
        });
        let stdout = '';
        let stderr = '';
        child.stdout.setEncoding('utf8').on('data', chunk => { stdout += chunk; });
        child.stderr.setEncoding('utf8').on('data', chunk => { stderr += chunk; });
        child.once('error', reject);
        child.once('close', (code, signal) => resolve({ code, signal, stdout, stderr }));
    });
    return { ...result, summary: await readFile(summaryPath, 'utf8') };
}

function readyEndpoint(request, response) {
    if (request.url === '/health') {
        sendJson(response, 200, { status: 'ok', service: 'phishlens-api' });
    } else if (request.url === '/ready') {
        sendJson(response, 200, { status: 'ready', database: 'connected' });
    } else {
        return false;
    }
    return true;
}

test('accepts only a 401 response with a Bearer challenge for anonymous history', async t => {
    const result = await runSmoke(t, (request, response) => {
        if (readyEndpoint(request, response)) return;
        sendJson(response, 401, { detail: 'authentication required' }, {
            'www-authenticate': 'Bearer realm="saved-reports"',
        });
    });

    assert.equal(result.code, 0, result.stderr);
    assert.match(result.stdout, /HTTP 401 Bearer/);
    assert.equal(result.summary, '');
});

test('fails a permanent 401 without Bearer and reports endpoint and status', async t => {
    let historyRequests = 0;
    const result = await runSmoke(t, (request, response) => {
        if (readyEndpoint(request, response)) return;
        historyRequests += 1;
        sendJson(response, 401, { detail: 'wrong challenge' }, {
            'www-authenticate': 'Basic realm="saved-reports"',
        });
    });

    assert.equal(result.code, 1);
    assert.equal(historyRequests, 1, 'a permanent authentication contract error must not be retried');
    assert.match(result.summary, /Endpoint: .*\/api\/analyses/);
    assert.match(result.summary, /Final result: HTTP 401/);
    assert.match(result.summary, /Anonymous history .*HTTP 401 without a Bearer/);
});

test('does not retry a rejected redirect from saved-report history', async t => {
    let historyRequests = 0;
    const result = await runSmoke(t, (request, response) => {
        if (readyEndpoint(request, response)) return;
        historyRequests += 1;
        response.writeHead(302, { location: '/redirect-target' });
        response.end();
    });

    assert.equal(result.code, 1);
    assert.equal(historyRequests, 1, 'a redirect contract failure must not be retried');
    assert.match(result.summary, /Endpoint: .*\/api\/analyses/);
    assert.match(result.summary, /attempts: 1/);
});

test('retries a transient history 503 then validates seeded history through the staging history contract', async t => {
    let historyRequests = 0;
    const demo = {
        id: '29d80c39-ec0d-4db8-a6e5-87444ba2600c',
        subject: 'Synthetic account notice',
        prediction: 'phishing',
        confidence: 0.93,
        risk_level: 'high',
        threat_indicators: [{ type: 'link', detail: 'Synthetic lookalike link' }],
        explanation: 'Synthetic test explanation',
        created_at: '2026-10-14T04:00:00Z',
    };
    const result = await runSmoke(t, (request, response) => {
        if (readyEndpoint(request, response)) return;
        historyRequests += 1;
        if (historyRequests === 1) {
            sendJson(response, 503, { detail: 'brief startup propagation' });
            return;
        }
        sendJson(response, 200, { items: [demo] });
    });

    assert.equal(result.code, 0, result.stderr);
    assert.equal(historyRequests, 2);
    assert.match(result.stdout, /seeded history through the staging history contract/);
});

test('does not retry a successful HTTP response that violates the seeded-history contract', async t => {
    let historyRequests = 0;
    const result = await runSmoke(t, (request, response) => {
        if (readyEndpoint(request, response)) return;
        historyRequests += 1;
        sendJson(response, 200, { items: [] });
    });

    assert.equal(result.code, 1);
    assert.equal(historyRequests, 1, 'a permanent history contract error must not be retried');
    assert.match(result.summary, /Final result: HTTP 200/);
    assert.match(result.summary, /Migrated and seeded demo analysis must be returned/);
});

test('stops transient retries at the overall deadline and records the last HTTP result', async t => {
    let healthRequests = 0;
    const startedAt = Date.now();
    const result = await runSmoke(t, (request, response) => {
        healthRequests += 1;
        sendJson(response, 503, { detail: 'still starting' });
    }, {
        STAGING_SMOKE_TIMEOUT_MS: '80',
        STAGING_MAX_ATTEMPTS: '30',
        STAGING_RETRY_DELAY_MS: '10',
    });
    const elapsedMs = Date.now() - startedAt;

    assert.equal(result.code, 1);
    assert.ok(healthRequests > 0 && healthRequests < 30);
    assert.ok(elapsedMs < 1000, `bounded smoke took ${elapsedMs} ms`);
    assert.match(result.summary, /Final result: HTTP 503/);
    assert.match(result.summary, /Overall deadline: 80 ms/);
});

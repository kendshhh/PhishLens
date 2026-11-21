import assert from 'node:assert/strict';
import { readStagingHistory, writeHistoryAccessOutput } from './staging_history.mjs';

const baseUrl = process.env.STAGING_BASE_URL || 'http://127.0.0.1:8000';
const attempts = Number(process.env.STAGING_ATTEMPTS || 60);
const historyAttempts = Number(process.env.STAGING_HISTORY_ATTEMPTS || 6);
const historyDelayMs = Number(process.env.STAGING_HISTORY_DELAY_MS || 1000);
const historyTimeoutMs = Number(process.env.STAGING_HISTORY_TIMEOUT_MS || 5000);
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const emitGithubOutput = process.argv.includes('--github-output');

async function reportHistoryAccess(items) {
    if (!emitGithubOutput) return;
    await writeHistoryAccessOutput(items, process.env.GITHUB_OUTPUT);
}

async function read(path) {
  const response = await fetch(baseUrl + path, { signal: AbortSignal.timeout(10000) });
  assert.equal(response.status, 200, path + ' must return HTTP 200');
  return response.json();
}

// Retry only startup readiness. Contract failures after startup fail immediately.
let ready = false;
for (let attempt = 0; attempt < attempts; attempt++) {
  try {
    assert.deepEqual(await read('/health'), { status: 'ok', service: 'phishlens-api' });
    assert.deepEqual(await read('/ready'), { status: 'ready', database: 'connected' });
    ready = true;
    break;
  } catch {
    if (attempt + 1 < attempts) await delay(3000);
  }
}
assert.ok(ready, 'Staging API did not become healthy and database-ready');
const historyUrl = `${baseUrl.replace(/\/+$/, '')}/api/analyses`;

function reportHistoryFailure(error, status, responseBody) {
    console.error(`Staging history check failed: GET ${error?.url || historyUrl}`);
    console.error(`status=${status ?? error?.status ?? 'unavailable'} origin=${error?.origin || 'assertion'} category=${error?.category || 'staging_contract'} code=${error?.code || 'history_assertion_failed'} attempts=${error?.attempts ?? error?.attempt ?? 1}/${error?.maxAttempts ?? historyAttempts}`);
    const body = responseBody ?? error?.responseBody;
    if (body) console.error(`Response body (bounded): ${body}`);
    console.error(error?.message || String(error));
}

let items;
try {
    items = await readStagingHistory(baseUrl, fetch, {
        attempts: historyAttempts,
        delayMs: historyDelayMs,
        timeoutMs: historyTimeoutMs,
    });
    await reportHistoryAccess(items);

    if (items === null) {
        console.log('Staging passed: health and database readiness; anonymous history correctly requires Bearer authentication.');
    } else {
        const demo = items.find(item => item.id === '29d80c39-ec0d-4db8-a6e5-87444ba2600c');
        assert.ok(demo, 'Migrated and seeded demo analysis must be returned in demo mode');
        assert.equal(demo.subject, 'Synthetic account notice');
        assert.equal(demo.prediction, 'phishing');
        assert.equal(demo.risk_level, 'high');
        assert.equal(demo.confidence, 0.93);
        assert.ok(Array.isArray(demo.threat_indicators));
        assert.ok(Number.isFinite(Date.parse(demo.created_at)));
        console.log('Staging passed: health, database readiness, and seeded demo history.');
    }
} catch (error) {
    const responseBody = Array.isArray(items) ?
        JSON.stringify({ items }).slice(0, 2048) : undefined;
    reportHistoryFailure(error, Array.isArray(items) ? 200 : undefined, responseBody);
    throw error;
}

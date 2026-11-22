import assert from 'node:assert/strict';
import { waitForHistoryEndpoint } from './staging_history.mjs';

const baseUrl = process.env.STAGING_BASE_URL || 'http://127.0.0.1:8000';
const attempts = Number(process.env.STAGING_ATTEMPTS || 60);
const historyAttempts = Number(process.env.STAGING_HISTORY_ATTEMPTS || 6);
const historyDelayMs = Number(process.env.STAGING_HISTORY_DELAY_MS || 1000);
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

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

function reportHistoryFailure(error, status) {
  console.error(`Staging history check failed: GET ${error?.url || historyUrl}`);
  console.error(`origin=${error?.origin || 'assertion'} category=${error?.category || 'staging_contract'} code=${error?.code || 'history_assertion_failed'} status=${status ?? error?.status ?? 'unavailable'} attempts=${error?.attempts ?? error?.attempt ?? 1}/${error?.maxAttempts ?? historyAttempts}`);
  if (error?.wwwAuthenticate) console.error(`WWW-Authenticate: ${error.wwwAuthenticate}`);
  console.error(error?.category ? error.message : 'Synthetic history contract mismatch; response data omitted.');
}

let history;
try {
  history = await waitForHistoryEndpoint(baseUrl, {
    attempts: historyAttempts,
    delayMs: historyDelayMs,
    timeoutMs: 10000,
  });
} catch (error) {
  reportHistoryFailure(error);
  throw error;
}

try {
  if (history.status === 401) {
    assert.match(
      history.error.wwwAuthenticate || '',
      /^Bearer\b/i,
      'Anonymous saved-report access must return a Bearer authentication challenge',
    );
    console.log('Staging passed: health, database readiness, and anonymous saved-report authentication.');
  } else {
    const demo = history.items.find(item => item.id === '29d80c39-ec0d-4db8-a6e5-87444ba2600c');
    assert.ok(demo, 'Migrated and seeded demo analysis must be returned through the extension client');
    assert.equal(demo.subject, 'Synthetic account notice');
    assert.equal(demo.prediction, 'phishing');
    assert.equal(demo.risk_level, 'high');
    assert.equal(demo.confidence, 0.93);
    assert.ok(Array.isArray(demo.threat_indicators));
    assert.ok(Number.isFinite(Date.parse(demo.created_at)));
    console.log('Staging passed: health, database readiness, seeded history through the real extension client.');
  }
} catch (error) {
  reportHistoryFailure(history.error || error, history.status);
  throw new Error(`Staging history contract failed (HTTP ${history.status}); response data omitted.`);
}

import assert from 'node:assert/strict';
import { getAnalyses } from '../extension/js/api.js';

const baseUrl = process.env.STAGING_BASE_URL || 'http://127.0.0.1:8000';
const attempts = Number(process.env.STAGING_ATTEMPTS || 60);
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
const items = await getAnalyses(baseUrl);
const demo = items.find(item => item.id === '29d80c39-ec0d-4db8-a6e5-87444ba2600c');
assert.ok(demo, 'Migrated and seeded demo analysis must be returned through the extension client');
assert.equal(demo.subject, 'Synthetic account notice');
assert.equal(demo.prediction, 'phishing');
assert.equal(demo.risk_level, 'high');
assert.equal(demo.confidence, 0.93);
assert.ok(Array.isArray(demo.threat_indicators));
assert.ok(Number.isFinite(Date.parse(demo.created_at)));
console.log('Staging passed: health, database readiness, seeded history through the real extension client.');

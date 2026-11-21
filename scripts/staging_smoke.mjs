import assert from 'node:assert/strict';
import { getAnalyses } from '../extension/js/api.js';

const baseUrl = (process.env.STAGING_BASE_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');
const attempts = Number(process.env.STAGING_ATTEMPTS || 60);
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

async function read(path) {
    let response;
    try {
        response = await fetch(baseUrl + path, {
            signal: AbortSignal.timeout(10000)
        });
    } catch (error) {
        const reason = error instanceof Error ? error.message : String(error);
        throw new Error(`${path} request failed: ${reason}`);
    }

    if (!response.ok) {
        let detail = '';
        try {
            detail = (await response.text()).trim().slice(0, 500);
        } catch {}
        throw new Error(`${path} returned HTTP ${response.status}${detail ? `: ${detail}` : ''}`);
    }

    try {
        return await response.json();
    } catch (error) {
        throw new Error(`${path} returned invalid JSON: ${error instanceof Error ? error.message : String(error)}`);
    }
}

// Retry only startup/readiness endpoints. Contract failures after startup fail immediately.
let ready = false;
for (let attempt = 0; attempt < attempts; attempt++) {
    try {
        assert.deepEqual(await read('/health'), { status: 'ok', service: 'phishlens-api' });
        assert.deepEqual(await read('/ready'), { status: 'ready', database: 'connected' });
        ready = true;
        break;
    } catch (error) {
        if (attempt + 1 < attempts) {
            console.error(`Staging startup attempt ${attempt + 1}/${attempts} failed: ${error.message}`);
            await delay(3000);
        }
    }
}
assert.ok(ready, 'Staging API did not become healthy and database-ready');

let items;
for (let attempt = 0; attempt < attempts; attempt++) {
    try {
        items = await getAnalyses(baseUrl);
        break;
    } catch (error) {
        // Readiness and history consistency may briefly diverge after deployment.
        const transient = error?.status === 502 || error?.status === 503 || error?.status === 504 ||
            /network request|timed out|ECONNRESET|fetch failed/i.test(error?.message || '');
        if (!transient || attempt + 1 === attempts) throw error;
        console.error(`Staging history attempt ${attempt + 1}/${attempts} failed: ${error.message}`);
        await delay(3000);
    }
}

const demo = items.find(item => item.id === '29d80c39-ec0d-4db8-a6e5-87444ba2600c');
assert.ok(demo, 'Migrated and seeded demo analysis must be returned through the extension client');
assert.equal(demo.subject, 'Synthetic account notice');
assert.equal(demo.prediction, 'phishing');
assert.equal(demo.risk_level, 'high');
assert.equal(demo.confidence, 0.93);
assert.ok(Array.isArray(demo.threat_indicators));
assert.ok(Number.isFinite(Date.parse(demo.created_at)));
console.log('Staging passed: health, database readiness, seeded history through the real extension client.');

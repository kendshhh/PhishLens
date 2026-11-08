import assert from 'node:assert/strict';
import { createAnalysisClient } from '../extension/js/api.js';
import { saveAnalysisAndRefresh } from '../extension/js/report-client.js';

const origin = new URL(process.argv[2]);
assert.equal(origin.protocol, 'http:');
assert.equal(origin.hostname, '127.0.0.1', 'This verifier only uses its disposable loopback server');
const token = process.argv[3];
assert.match(token || '', /^[\w-]{32}$/, 'Run this verifier through the Python harness');
const probe = await fetch(new URL('/__client_contract', origin), {
    redirect: 'error', signal: AbortSignal.timeout(10000)
});
assert.equal(probe.status, 200);
assert.deepEqual(await probe.json(), { kind: 'disposable-client-contract', token });
const client = createAnalysisClient(origin.origin);
const cases = [
    [409, 'valid', 'Synthetic body', 'contract-conflict'],
    [422, 'valid', '   ', 'contract-invalid'],
    [500, 'unexpected-error', 'Synthetic body', 'contract-internal'],
    [502, 'provider-failed', 'Synthetic body', 'contract-failed'],
    [503, 'provider-unavailable', 'Synthetic body', 'contract-unavailable'],
    [504, 'provider-timeout', 'Synthetic body', 'contract-timeout']
];
for (const [status, subject, body, idempotencyKey] of cases) {
    const input = { subject, body };
    const original = structuredClone(input);
    await assert.rejects(saveAnalysisAndRefresh(client, input, { idempotencyKey }), error => {
        assert.equal(error.status, status);
        assert.equal(error.idempotencyKey, idempotencyKey);
        assert.ok(error.message.trim());
        assert.doesNotMatch(error.message, /must not escape/);
        return true;
    });
    assert.deepEqual(input, original);
    console.log(`FastAPI HTTP ${status}: status, safe message, input and retry key preserved`);
}
const retryInput = { subject: 'provider-unavailable', body: 'Synthetic explicit retry' };
let key;
for (let attempt = 0; attempt < 2; attempt++) {
    await assert.rejects(client.createAnalysis(retryInput), error => {
        assert.equal(error.status, 503);
        assert.ok(error.idempotencyKey);
        if (key) assert.equal(error.idempotencyKey, key);
        key = error.idempotencyKey;
        return true;
    });
}
console.log('Explicit uncertain-create retry retains its key; no automatic retry or refresh');

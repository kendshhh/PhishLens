import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { verifySavedReport } from '../../scripts/verify_saved_report.mjs';

const sha = 'a'.repeat(40);
const modelSha = 'b'.repeat(64);
const id = '29d80c39-ec0d-4db8-a6e5-87444ba2600c';

async function fixture(t, {
    createStatus, failHistory, failCleanup, invalidJson, identitySha = sha,
    detailTimestamp, historyTimestamp, createdFields = {}, historyFields = {},
    deployedModelSha = modelSha
} = {}) {
    let record;
    let requestedModel;
    const calls = [];
    const server = createServer(async (request, response) => {
        calls.push(request.method + ' ' + request.url);
        const send = (status, body) => {
            response.writeHead(status, { 'Content-Type': 'application/json' });
            response.end(body === undefined ? undefined : JSON.stringify(body));
        };
        if (request.url === '/version') return send(200, { commit: identitySha, environment: 'disposable' });
        if (request.url === '/ready') return send(200, { status: 'ready', database: 'connected' });
        if (request.url === '/model-info') return send(200, {
            provider_mode: 'tfidf', accepts_tfidf_reports: true, model_sha256: deployedModelSha
        });
        if (request.method === 'POST') {
            requestedModel = request.headers['x-phishlens-model'];
            let body = '';
            for await (const chunk of request) body += chunk;
            if (createStatus) return send(createStatus, { detail: 'Controlled create failure' });
            if (invalidJson) {
                response.writeHead(201, { 'Content-Type': 'application/json' });
                return response.end('{');
            }
            assert.ok(request.headers['idempotency-key']);
            record = {
                id, ...JSON.parse(body), prediction: 'spam', confidence: null, risk_level: 'medium',
                threat_indicators: [{ type: 'evidence', quote: 'Synthetic', detail: 'Fixture only' }],
                explanation: 'Synthetic explanation', created_at: '2026-10-31T01:00:00Z',
                notes: null, feedback: null, analysis_mode: 'mock',
                analysis_provenance: { provider_mode: 'mock', model: null },
                ...createdFields
            };
            return send(201, record);
        }
        if (request.method === 'DELETE') {
            if (failCleanup) return send(503, { detail: 'Cleanup unavailable' });
            record = undefined;
            return send(204);
        }
        if (request.url === '/api/analyses') {
            return failHistory ? send(503, { detail: 'History unavailable' })
                : send(200, { items: record ? [{
                    ...record, created_at: historyTimestamp ?? record.created_at, ...historyFields
                }] : [] });
        }
        return record ? send(200, {
            ...record, created_at: detailTimestamp ?? record.created_at
        }) : send(404, { detail: 'Absent' });
    });
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    t.after(() => new Promise(resolve => {
        server.closeAllConnections();
        server.close(resolve);
    }));
    return {
        url: 'http://127.0.0.1:' + server.address().port,
        options: { environment: 'disposable', expectedSha: sha, allowWrites: true },
        calls, get record() { return record; }, get requestedModel() { return requestedModel; }
    };
}

test('guarded report replay uses returned ID, refreshes and confirms cleanup', async t => {
    const f = await fixture(t);
    const result = await verifySavedReport(f.url, f.options);
    assert.equal(result.result, 'passed');
    assert.equal(result.recordId, id);
    assert.equal(result.analysisMode, 'mock');
    assert.equal(result.cleanedUp, true);
    assert.equal(f.record, undefined);
    assert.equal(f.calls.filter(x => x.startsWith('POST')).length, 1);
    assert.equal(f.calls.filter(x => x === 'GET /api/analyses/' + id).length, 2);
});

test('controlled HTTP replay retains nonempty evidence and explanation across create, detail and history', async t => {
    const f = await fixture(t, { createdFields: {
        threat_indicators: [
            { type: 'evidence', quote: 'Synthetic verification message.', detail: 'Synthetic first reason' },
            { type: 'evidence', quote: 'No personal content or credentials.', detail: 'Synthetic second reason' }
        ],
        explanation: 'Tactics: synthetic test. Recommendations: verify with the sender.'
    } });
    const result = await verifySavedReport(f.url, f.options);
    assert.equal(result.result, 'passed');
    assert.equal(result.cleanedUp, true);
    assert.equal(f.record, undefined);
    assert.equal(f.calls.filter(call => call.startsWith('POST')).length, 1);
    assert.ok(f.calls.includes('GET /api/analyses'));
    assert.ok(f.calls.includes('GET /api/analyses/' + id));
});

for (const mode of ['mock', 'real']) {
    test('new ' + mode + ' report with null prediction cannot pass acceptance', async t => {
        const f = await fixture(t, { createdFields: {
            prediction: null,
            analysis_mode: mode,
            analysis_provenance: { provider_mode: mode === 'mock' ? 'mock' : 'local', model: null }
        } });
        await assert.rejects(verifySavedReport(f.url, f.options), /New report prediction/);
        assert.equal(f.record, undefined);
    });
}

for (const prediction of ['legitimate', 'spam', 'phishing']) {
    test('new report accepts ' + prediction + ' with nullable confidence', async t => {
        const f = await fixture(t, { createdFields: { prediction, confidence: null } });
        const result = await verifySavedReport(f.url, f.options);
        assert.equal(result.result, 'passed');
        assert.equal(result.cleanedUp, true);
    });
}

test('guarded report replay accepts equivalent Z and +00:00 timestamps', async t => {
    const f = await fixture(t, {
        detailTimestamp: '2026-10-31T01:00:00+00:00',
        historyTimestamp: '2026-10-31T01:00:00+00:00'
    });
    const result = await verifySavedReport(f.url, f.options);
    assert.equal(result.result, 'passed');
    assert.equal(result.cleanedUp, true);
});

for (const field of ['detailTimestamp', 'historyTimestamp']) {
    test('guarded report replay rejects a different instant in ' + field, async t => {
        const f = await fixture(t, { [field]: '2026-10-31T01:00:01+00:00' });
        await assert.rejects(verifySavedReport(f.url, f.options), /timestamp differs/);
        assert.equal(f.record, undefined);
    });
}

test('guarded report replay rejects mismatched source before POST', async t => {
    const f = await fixture(t, { identitySha: 'b'.repeat(40) });
    await assert.rejects(verifySavedReport(f.url, f.options), /does not match/);
    assert.equal(f.calls.some(x => x.startsWith('POST')), false);
});

test('guarded report replay rejects production and missing write opt-in', async () => {
    await assert.rejects(verifySavedReport('https://phishlens-api-ocvt.onrender.com', {
        environment: 'demo', expectedSha: sha, allowWrites: true
    }), /approved staging origin/);
    await assert.rejects(verifySavedReport('http://127.0.0.1', {
        environment: 'disposable', expectedSha: sha
    }), /Explicit write permission/);
});

for (const status of [422, 500, 502, 503, 504]) {
    test('guarded report replay preserves HTTP ' + status + ' without retry', async t => {
        const f = await fixture(t, { createStatus: status });
        await assert.rejects(verifySavedReport(f.url, f.options), error =>
            error.status === status && typeof error.idempotencyKey === 'string');
        assert.equal(f.calls.filter(x => x.startsWith('POST')).length, 1);
        assert.equal(f.calls.some(x => x.startsWith('DELETE')), false);
    });
}

test('guarded report replay rejects malformed create JSON without retry', async t => {
    const f = await fixture(t, { invalidJson: true });
    await assert.rejects(verifySavedReport(f.url, f.options), error =>
        error instanceof SyntaxError && typeof error.idempotencyKey === 'string');
    assert.equal(f.calls.filter(x => x.startsWith('POST')).length, 1);
});

test('refresh failure cannot pass and still cleans the confirmed record', async t => {
    const f = await fixture(t, { failHistory: true });
    await assert.rejects(verifySavedReport(f.url, f.options), error =>
        error instanceof AggregateError && error.errors[0].status === 503);
    assert.equal(f.record, undefined);
    assert.equal(f.calls.filter(x => x.startsWith('POST')).length, 1);
});

test('unconfirmed cleanup fails with the exact synthetic record ID', async t => {
    const f = await fixture(t, { failCleanup: true });
    await assert.rejects(verifySavedReport(f.url, f.options), error =>
        /cleanup could not be confirmed/.test(error.message) && error.recordId === id);
    assert.equal(f.record.id, id);
});

for (const [name, historyFields] of [
    ['missing evidence', { threat_indicators: [] }],
    ['changed evidence', { threat_indicators: [{ type: 'evidence', quote: 'Synthetic', detail: 'Changed reason' }] }],
    ['missing explanation', { explanation: null }],
    ['changed explanation', { explanation: 'Changed explanation' }]
]) {
    test('report verification rejects history ' + name, async t => {
        const f = await fixture(t, { historyFields });
        await assert.rejects(verifySavedReport(f.url, f.options), /History differs/);
        assert.equal(f.record, undefined);
    });
}

for (const [name, createdFields] of [
    ['null mode', { analysis_mode: null }],
    ['legacy mode', { analysis_mode: 'unknown' }],
    ['missing provenance', { analysis_provenance: undefined }],
    ['null provenance', { analysis_provenance: null }],
    ['empty provenance', { analysis_provenance: {} }],
    ['unknown provider', { analysis_provenance: { provider_mode: 'unknown' } }],
    ['mismatched provider', { analysis_provenance: { provider_mode: 'local' } }]
]) {
    test('report verification rejects newly created ' + name, async t => {
        const f = await fixture(t, { createdFields });
        await assert.rejects(verifySavedReport(f.url, f.options), /New report/);
        assert.equal(f.record, undefined);
    });
}

for (const provider of ['gemini', 'local']) {
    test('report verification accepts real provenance for ' + provider, async t => {
        const f = await fixture(t, { createdFields: {
            analysis_mode: 'real',
            analysis_provenance: { provider_mode: provider, model: 'synthetic-model' }
        } });
        const result = await verifySavedReport(f.url, f.options);
        assert.equal(result.analysisMode, 'real');
        assert.equal(result.cleanedUp, true);
    });
}

test('TF-IDF verification pins the deployed and saved model and cleans up', async t => {
    const f = await fixture(t, { createdFields: {
        prediction: 'legitimate', risk_level: 'low', analysis_mode: 'real',
        analysis_provenance: { provider_mode: 'tfidf', model_revision: modelSha }
    } });
    const result = await verifySavedReport(f.url, { ...f.options, expectedModelSha: modelSha });
    assert.equal(f.requestedModel, modelSha);
    assert.equal(result.providerMode, 'tfidf');
    assert.equal(result.modelRevision, modelSha);
    assert.equal(result.cleanedUp, true);
});

test('TF-IDF verification refuses a different deployed model before saving', async t => {
    const f = await fixture(t, { deployedModelSha: 'c'.repeat(64) });
    await assert.rejects(verifySavedReport(f.url, { ...f.options, expectedModelSha: modelSha }),
        /Target model SHA-256 differs/);
    assert.equal(f.calls.some(call => call.startsWith('POST')), false);
});

test('TF-IDF verification cleans up when saved provenance has a different model', async t => {
    const f = await fixture(t, { createdFields: {
        analysis_mode: 'real',
        analysis_provenance: { provider_mode: 'tfidf', model_revision: 'c'.repeat(64) }
    } });
    await assert.rejects(verifySavedReport(f.url, { ...f.options, expectedModelSha: modelSha }),
        /Saved model SHA-256 differs/);
    assert.equal(f.record, undefined);
});

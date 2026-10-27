import test from 'node:test';
import assert from 'node:assert/strict';
import { createAnalysisClient } from '../js/api.js';

const id = '29d80c39-ec0d-4db8-a6e5-87444ba2600c';
const record = {
    id, subject: 'Synthetic notice', prediction: 'phishing', confidence: 0.93,
    risk_level: 'high', threat_indicators: [{ type: 'link', detail: 'Synthetic link' }],
    explanation: 'Synthetic test', created_at: '2026-10-13T15:07:51.365605+00:00',
    body: 'Synthetic email body', notes: null, feedback: 'none', analysis_mode: 'mock'
};

function setup(status, data, jsonError) {
    const calls = [];
    const client = createAnalysisClient('https://example.test/', async (url, options) => {
        calls.push({ url, ...options });
        return {
            ok: status >= 200 && status < 300, status,
            json: async () => {
                if (jsonError) throw jsonError;
                return data;
            }
        };
    });
    return { client, calls };
}

test('lists records and normalizes the base URL', async () => {
    const { client, calls } = setup(200, { items: [record] });
    assert.deepEqual(await client.listAnalyses(), [record]);
    assert.equal(calls[0].url, 'https://example.test/api/analyses');
    assert.equal(calls[0].method, 'GET');
    assert.equal(calls[0].body, undefined);
    assert.ok(calls[0].signal instanceof AbortSignal);
});

test('accepts an empty list', async () => {
    assert.deepEqual(await setup(200, { items: [] }).client.listAnalyses(), []);
});

test('gets one detail record', async () => {
    const { client, calls } = setup(200, record);
    assert.deepEqual(await client.getAnalysis(id), record);
    assert.equal(calls[0].url, 'https://example.test/api/analyses/' + id);
    assert.equal(calls[0].method, 'GET');
});

test('creates with POST JSON and accepts 201', async () => {
    const { client, calls } = setup(201, record);
    const input = { subject: record.subject, body: record.body };
    assert.deepEqual(await client.createAnalysis(input), record);
    assert.equal(calls[0].method, 'POST');
    assert.equal(calls[0].headers['Content-Type'], 'application/json');
    assert.match(calls[0].headers['Idempotency-Key'], /^[A-Za-z0-9_-]{1,255}$/);
    assert.deepEqual(JSON.parse(calls[0].body), input);
});

test('create retry reuses its idempotency key after an uncertain network failure', async () => {
    const calls = [];
    let attempt = 0;
    const client = createAnalysisClient('https://example.test', async (url, options) => {
        calls.push({ url, ...options });
        if (attempt++ === 0) throw new TypeError('Connection lost after request');
        return { ok: true, status: 201, json: async () => record };
    });
    const input = { subject: record.subject, body: record.body };

    await assert.rejects(client.createAnalysis(input), error => {
        assert.match(error.idempotencyKey, /^[A-Za-z0-9_-]{1,255}$/);
        return true;
    });
    assert.deepEqual(await client.createAnalysis(input), record);
    assert.equal(calls.length, 2);
    assert.equal(calls[0].headers['Idempotency-Key'], calls[1].headers['Idempotency-Key']);
});

test('create retry reuses its idempotency key after an analysis timeout response', async () => {
    const calls = [];
    let attempt = 0;
    const client = createAnalysisClient('https://example.test', async (url, options) => {
        calls.push({ url, ...options });
        if (attempt++ === 0) {
            return {
                ok: false,
                status: 504,
                json: async () => ({ detail: 'Email analysis timed out', code: 'analysis_timeout' })
            };
        }
        return { ok: true, status: 201, json: async () => record };
    });
    const input = { subject: record.subject, body: record.body };

    await assert.rejects(client.createAnalysis(input), error => error.status === 504);
    await client.createAnalysis(input);

    assert.equal(calls[0].headers['Idempotency-Key'], calls[1].headers['Idempotency-Key']);
});

test('explicit idempotency key supports retry after recreating the client', async () => {
    const calls = [];
    const fetchImpl = async (url, options) => {
        calls.push({ url, ...options });
        if (calls.length === 1) throw new TypeError('Connection lost after request');
        return { ok: true, status: 201, json: async () => record };
    };
    const input = { subject: record.subject, body: record.body };
    const client = createAnalysisClient('https://example.test', fetchImpl);

    let retryKey;
    await assert.rejects(client.createAnalysis(input), error => {
        retryKey = error.idempotencyKey;
        return true;
    });
    await createAnalysisClient('https://example.test', fetchImpl)
        .createAnalysis(input, { idempotencyKey: retryKey });

    assert.equal(calls[1].headers['Idempotency-Key'], retryKey);
});

test('a new intentional create after success receives a fresh idempotency key', async () => {
    const calls = [];
    const client = createAnalysisClient('https://example.test', async (url, options) => {
        calls.push(options);
        return { ok: true, status: 201, json: async () => record };
    });
    const input = { subject: record.subject, body: record.body };

    await client.createAnalysis(input);
    await client.createAnalysis(input);

    assert.notEqual(calls[0].headers['Idempotency-Key'], calls[1].headers['Idempotency-Key']);
});

test('patches notes and feedback without adding omitted fields', async () => {
    const patch = { notes: 'Reviewed', feedback: 'false_positive' };
    const updated = { ...record, ...patch };
    const { client, calls } = setup(200, updated);
    assert.deepEqual(await client.updateAnalysis(id, patch), updated);
    assert.equal(calls[0].method, 'PATCH');
    assert.equal(calls[0].url, 'https://example.test/api/analyses/' + id);
    assert.deepEqual(JSON.parse(calls[0].body), patch);
});

test('sends null notes to clear them', async () => {
    const { client, calls } = setup(200, record);
    await client.updateAnalysis(id, { notes: null });
    assert.deepEqual(JSON.parse(calls[0].body), { notes: null });
});

test('deletes with 204 and never parses its empty body', async () => {
    const { client, calls } = setup(204, undefined, new Error('Must not parse'));
    assert.equal(await client.deleteAnalysis(id), undefined);
    assert.equal(calls[0].method, 'DELETE');
    assert.equal(calls[0].url, 'https://example.test/api/analyses/' + id);
    assert.equal(calls[0].body, undefined);
});

for (const status of [404, 422, 503]) {
    test('preserves HTTP ' + status + ' and readable detail', async () => {
        const { client } = setup(status, { detail: 'Request unavailable' });
        await assert.rejects(client.getAnalysis(id), error => {
            assert.equal(error.status, status);
            assert.equal(error.message, 'Request unavailable');
            return true;
        });
    });
}

test('keeps a useful error for a non-JSON failure', async () => {
    const { client } = setup(503, null, new SyntaxError('Not JSON'));
    await assert.rejects(client.listAnalyses(), error => error.status === 503 && /503/.test(error.message));
});

test('handles FastAPI validation error arrays', async () => {
    const { client } = setup(422, { detail: [{ msg: 'Field required' }] });
    await assert.rejects(client.createAnalysis({}), error => error.status === 422 && /422/.test(error.message));
});

test('rejects malformed success JSON', async () => {
    const { client } = setup(200, null, new SyntaxError('Invalid JSON'));
    await assert.rejects(client.listAnalyses(), SyntaxError);
});

test('propagates network failure', async () => {
    const client = createAnalysisClient('https://example.test', async () => { throw new TypeError('Network unavailable'); });
    await assert.rejects(client.listAnalyses(), /Network unavailable/);
});

test('propagates request timeout', async () => {
    const client = createAnalysisClient('https://example.test', async () => { throw new DOMException('Request timed out', 'TimeoutError'); });
    await assert.rejects(client.listAnalyses(), { name: 'TimeoutError' });
});

for (const data of [null, {}, { items: {} }, { items: [null] }]) {
    test('rejects malformed list ' + JSON.stringify(data), async () => {
        await assert.rejects(setup(200, data).client.listAnalyses(), /Invalid/);
    });
}

for (const patch of [
    { id: 'not-a-uuid' }, { created_at: '0' }, { confidence: '0.93' },
    { confidence: 2 }, { prediction: 'unsupported' }, { risk_level: 'unknown' },
    { threat_indicators: ['link'] }
]) {
    test('rejects invalid record ' + JSON.stringify(patch), async () => {
        await assert.rejects(setup(200, { items: [{ ...record, ...patch }] }).client.listAnalyses(), /Invalid/);
    });
}

for (const field of ['body', 'notes', 'feedback', 'analysis_mode']) {
    test('requires detail field ' + field, async () => {
        const incomplete = { ...record };
        delete incomplete[field];
        await assert.rejects(setup(200, incomplete).client.getAnalysis(id), /Invalid analysis detail/);
    });
}

test('accepts nullable results and legacy unknown mode', async () => {
    const pending = { ...record, prediction: null, confidence: null, risk_level: null, explanation: null, analysis_mode: null };
    assert.deepEqual(await setup(200, pending).client.getAnalysis(id), pending);
});

test('rejects invalid IDs before making requests', async () => {
    const { client, calls } = setup(200, record);
    await assert.rejects(client.getAnalysis('../other'), /UUID/);
    assert.equal(calls.length, 0);
});

test('rejects unexpected success statuses', async () => {
    await assert.rejects(setup(200, record).client.createAnalysis({ subject: 'Test', body: 'Test' }), /Unexpected response status/);
});

for (const method of ['getAnalysis', 'createAnalysis', 'updateAnalysis']) {
    test(method + ' accepts nullable feedback without converting it', async () => {
        const data = { ...record, feedback: null };
        const { client } = setup(method === 'createAnalysis' ? 201 : 200, data);
        const result = method === 'getAnalysis' ? await client.getAnalysis(id)
            : method === 'createAnalysis' ? await client.createAnalysis({ subject: record.subject, body: record.body })
            : await client.updateAnalysis(id, { notes: 'Reviewed' });
        assert.equal(result.feedback, null);
    });
}

test('rejects unknown feedback values', async () => {
    await assert.rejects(setup(200, { ...record, feedback: 'bad' }).client.getAnalysis(id), /Invalid analysis detail/);
});

for (const method of ['listAnalyses', 'getAnalysis', 'createAnalysis']) {
    test(method + ' preserves a saved spam result', async () => {
        const spam = { ...record, prediction: 'spam', risk_level: 'medium' };
        const { client } = setup(
            method === 'createAnalysis' ? 201 : 200,
            method === 'listAnalyses' ? { items: [spam] } : spam
        );
        const result = method === 'listAnalyses' ? (await client.listAnalyses())[0]
            : method === 'getAnalysis' ? await client.getAnalysis(id)
            : await client.createAnalysis({ subject: record.subject, body: record.body });
        assert.equal(result.prediction, 'spam');
        assert.equal(result.risk_level, 'medium');
    });
}

test('sends the aligned subject and body limits without truncation', async () => {
    const input = { subject: 's'.repeat(320), body: 'b'.repeat(30000) };
    const { client, calls } = setup(201, { ...record, ...input });
    const result = await client.createAnalysis(input);
    assert.deepEqual(JSON.parse(calls[0].body), input);
    assert.equal(result.subject.length, 320);
    assert.equal(result.body.length, 30000);
});

for (const subject of [undefined, '']) {
    test('create allows an omitted or empty subject: ' + JSON.stringify(subject), async () => {
        const input = { body: 'Synthetic body' };
        if (subject !== undefined) input.subject = subject;
        const { client, calls } = setup(201, { ...record, subject: '', body: input.body });
        const result = await client.createAnalysis(input);
        assert.deepEqual(JSON.parse(calls[0].body), input);
        assert.equal(result.subject, '');
    });
}

test('reads evidence quotes and preserves provenance without inventing values', async () => {
    const data = {
        ...record,
        confidence: null,
        analysis_mode: 'real',
        threat_indicators: [{ type: 'evidence', quote: 'Account notice', detail: 'Quoted evidence' }],
        analysis_provenance: {
            model: 'synthetic-model', revision: 'synthetic-revision',
            prompt_version: 'test-v1', explanation_source: 'provider',
            input_truncated: false, windows_processed: 1
        }
    };
    assert.deepEqual(await setup(200, data).client.getAnalysis(id), data);
});

test('continues reading old indicators and nullable provenance', async () => {
    const data = { ...record, analysis_provenance: null };
    assert.deepEqual(await setup(200, data).client.getAnalysis(id), data);
});

test('rejects malformed evidence quote', async () => {
    const data = { ...record, threat_indicators: [{ type: 'evidence', quote: 123, detail: 'Reason' }] };
    await assert.rejects(setup(200, data).client.getAnalysis(id), /Invalid analysis data/);
});

for (const provenance of ['model-name', [], 123]) {
    test('rejects malformed provenance ' + JSON.stringify(provenance), async () => {
        await assert.rejects(
            setup(200, { ...record, analysis_provenance: provenance }).client.getAnalysis(id),
            /Invalid analysis detail/
        );
    });
}

test('create uses its configurable deadline and leaves reads at ten seconds', async () => {
    const originalTimeout = AbortSignal.timeout;
    const deadlines = [];
    const signal = new AbortController().signal;
    AbortSignal.timeout = milliseconds => {
        deadlines.push(milliseconds);
        return signal;
    };
    try {
        const fetchImpl = async () => ({ ok: true, status: 201, json: async () => record });
        await createAnalysisClient('https://example.test', fetchImpl).createAnalysis({ body: 'Synthetic body' });
        await createAnalysisClient('https://example.test', fetchImpl, { createTimeoutMs: 35000 })
            .createAnalysis({ body: 'Synthetic body' });
        await setup(200, record).client.getAnalysis(id);
        assert.deepEqual(deadlines, [25000, 35000, 10000]);
    } finally {
        AbortSignal.timeout = originalTimeout;
    }
});

for (const createTimeoutMs of [0, -1, NaN, Infinity, '25000', 2147483648]) {
    test('rejects invalid create timeout ' + String(createTimeoutMs), () => {
        assert.throws(
            () => createAnalysisClient('https://example.test', async () => {}, { createTimeoutMs }),
            /Create timeout/
        );
    });
}

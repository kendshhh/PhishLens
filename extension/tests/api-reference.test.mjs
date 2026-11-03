import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createAnalysisClient } from '../js/api.js';

const examples = JSON.parse(await readFile(new URL('../../docs/examples/saved-api.json', import.meta.url), 'utf8'));

test('API reference fixtures replay create, detail/list, patch and empty delete through the client', async () => {
    let saved;
    const calls = [];
    const client = createAnalysisClient('https://example.test', async (url, options) => {
        const method = options.method;
        calls.push(method + ' ' + new URL(url).pathname);
        let status = 200;
        let data;
        if (method === 'POST') {
            assert.deepEqual(JSON.parse(options.body), examples.create);
            assert.ok(options.headers['Idempotency-Key']);
            saved = structuredClone(examples.detail);
            status = 201;
            data = saved;
        } else if (method === 'PATCH') {
            assert.deepEqual(JSON.parse(options.body), examples.patch);
            Object.assign(saved, examples.patch);
            data = saved;
        } else if (method === 'DELETE') {
            status = 204;
            saved = undefined;
        } else if (url.endsWith('/api/analyses')) {
            data = structuredClone(examples.list);
        } else {
            data = saved;
        }
        return {
            ok: true, status,
            json: async () => {
                assert.notEqual(status, 204, 'A 204 response must not be parsed');
                return structuredClone(data);
            }
        };
    });
    const created = await client.createAnalysis(examples.create);
    const detail = await client.getAnalysis(created.id);
    const list = await client.listAnalyses();
    assert.deepEqual(created, examples.detail);
    assert.deepEqual(detail, examples.detail);
    assert.deepEqual(list, examples.list.items);
    assert.equal(created.subject, '');
    assert.equal(created.confidence, null);
    const updated = await client.updateAnalysis(created.id, examples.patch);
    assert.equal(updated.notes, examples.patch.notes);
    assert.equal(updated.feedback, null);
    assert.deepEqual(updated.analysis_provenance, examples.detail.analysis_provenance);
    await client.deleteAnalysis(created.id);
    assert.equal(saved, undefined);
    assert.deepEqual(calls.map(x => x.split(' ')[0]), ['POST', 'GET', 'GET', 'PATCH', 'DELETE']);
});

test('API reference saved and history errors retain their status and readable detail', async () => {
    for (const [method, data] of [['createAnalysis', examples.savedError], ['listAnalyses', examples.historyError]]) {
        const client = createAnalysisClient('https://example.test', async () => ({
            ok: false, status: 503, json: async () => structuredClone(data)
        }));
        await assert.rejects(client[method](examples.create), error =>
            error.status === 503 && error.message === data.detail);
    }
});

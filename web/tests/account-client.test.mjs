import test from 'node:test';
import assert from 'node:assert/strict';
import { createAnalysisClient } from '../../extension/js/api.js';

test('every account CRUD operation requires Neon mode and omits browser cookies without retry', async () => {
  const seen = [];
  const client = createAnalysisClient('https://web.example.test', async (url, options) => {
    seen.push({ url, ...options });
    return { ok: false, status: 503, json: async () => ({ detail: 'Required account service is unavailable' }) };
  }, { requiredAuthMode: 'neon', getAccessToken: async () => 'synthetic.jwt.token' });
  const id = '00000000-0000-0000-0000-000000000001';
  for (const action of [() => client.listAnalyses(), () => client.getAnalysis(id),
    () => client.createAnalysis({ body: 'Synthetic email' }), () => client.updateAnalysis(id, { notes: 'Test' }),
    () => client.deleteAnalysis(id)]) await assert.rejects(action(), { status: 503 });
  assert.equal(seen.length, 5);
  assert.deepEqual(seen.map(r => r.method), ['GET', 'GET', 'POST', 'PATCH', 'DELETE']);
  for (const request of seen) {
    assert.equal(request.headers['X-Require-Auth-Mode'], 'neon');
    assert.equal(request.headers.Authorization, 'Bearer synthetic.jwt.token');
    assert.equal(request.credentials, 'omit');
    assert.equal(request.redirect, 'error');
  }
});

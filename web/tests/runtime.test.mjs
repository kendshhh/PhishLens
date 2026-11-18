import test from 'node:test';
import assert from 'node:assert/strict';
import { createSessionArea, createWebRuntime, unavailableJudge } from '../runtime.js';

function memoryStorage() {
  const data = new Map();
  return { data, getItem: key => data.has(key) ? data.get(key) : null,
    setItem: (key, value) => data.set(key, String(value)), removeItem: key => data.delete(key) };
}

function setup(workflow, storage = memoryStorage()) {
  let ids = 0;
  const runtime = createWebRuntime({ workflow, area: createSessionArea(storage),
    randomUUID: () => `id-${++ids}`, now: () => new Date('2026-11-18T00:00:00Z') });
  const events = [];
  runtime.storage.onChanged.addListener((changes, area) => events.push({ changes, area }));
  return { runtime, storage, events, analysis: async () => (await runtime.storage.session.get('veriqoAnalysis')).veriqoAnalysis };
}
const flush = () => new Promise(resolve => setTimeout(resolve, 0));
const result = { valid: true, score: 0.4, workflow: { released: false } };

test('a pasted check stores loading, progress and the final result like the extension', async () => {
  const { runtime, events, analysis } = setup(async (text, { onProgress, jobId }) => {
    assert.equal(text, 'Subject: Hello');
    assert.equal(jobId, 'id-1');
    await onProgress('Local LLM judge');
    return result;
  });
  assert.deepEqual(await runtime.runtime.sendMessage({ type: 'phishlens-analyze-text', text: 'Subject: Hello' }), { ok: true });
  await flush();
  const stored = await analysis();
  assert.equal(stored.status, 'success');
  assert.equal(stored.selectedText, 'Subject: Hello');
  assert.deepEqual(stored.result, result);
  assert.equal(stored.scanId, 'id-2');
  assert.equal(stored.recordedAt, '2026-11-18T00:00:00.000Z');
  const statuses = events.map(event => event.changes.veriqoAnalysis.newValue.status);
  assert.deepEqual(statuses, ['loading', 'loading', 'success']);
  assert.ok(events.every(event => event.area === 'session'));
});

test('a failed workflow keeps the text and records an error, never a result', async () => {
  const { runtime, analysis } = setup(async () => { throw Error('Model integrity check failed.'); });
  await runtime.runtime.sendMessage({ type: 'phishlens-analyze-text', text: 'body' });
  const stored = await analysis();
  assert.equal(stored.status, 'error');
  assert.equal(stored.result, null);
  assert.equal(stored.selectedText, 'body');
  assert.match(stored.error, /integrity/);
});

test('cancel marks the check cancelled and a late result cannot overwrite it', async () => {
  let release;
  const { runtime, analysis } = setup((text, { isCurrent }) => new Promise(resolve => {
    release = () => resolve(isCurrent() ? result : Promise.reject(Error('Scan cancelled or superseded.')));
  }));
  const pending = runtime.runtime.sendMessage({ type: 'phishlens-analyze-text', text: 'body' });
  await flush();
  assert.equal((await analysis()).status, 'loading');
  assert.deepEqual(await runtime.runtime.sendMessage({ type: 'phishlens-cancel-analysis' }), { ok: true });
  release();
  await pending;
  const stored = await analysis();
  assert.equal(stored.status, 'cancelled');
  assert.equal(stored.selectedText, 'body');
});

test('clear removes the stored check', async () => {
  const { runtime, analysis, events } = setup(async () => result);
  await runtime.runtime.sendMessage({ type: 'phishlens-analyze-text', text: 'body' });
  await runtime.runtime.sendMessage({ type: 'phishlens-clear-analysis' });
  await flush();
  assert.equal(await analysis(), undefined);
  assert.equal(events.at(-1).changes.veriqoAnalysis.newValue, undefined);
});

test('the one-shot debug flag produces a controlled failure once', async () => {
  const { runtime, analysis } = setup(async () => result);
  await runtime.storage.session.set({ phishlensDebugFailNext: true });
  await runtime.runtime.sendMessage({ type: 'phishlens-analyze-text', text: 'body' });
  assert.equal((await analysis()).status, 'error');
  await runtime.runtime.sendMessage({ type: 'phishlens-analyze-text', text: 'body' });
  assert.equal((await analysis()).status, 'success');
});

test('state survives a page reload in the same tab, and an interrupted check becomes an error', async () => {
  const storage = memoryStorage();
  const first = setup(() => new Promise(() => {}), storage);
  void first.runtime.runtime.sendMessage({ type: 'phishlens-analyze-text', text: 'kept text' });
  await first.runtime.storage.session.set({ phishlensScanDraft: 'draft' });
  const reloaded = setup(async () => result, storage);
  const stored = await reloaded.analysis();
  assert.equal(stored.status, 'error');
  assert.equal(stored.selectedText, 'kept text');
  assert.match(stored.error, /interrupted/);
  assert.deepEqual(await reloaded.runtime.storage.session.get('phishlensScanDraft'), { phishlensScanDraft: 'draft' });
});

test('unavailable sessionStorage falls back to memory for the page', async () => {
  const throwing = { getItem() { throw Error('blocked'); }, setItem() { throw Error('blocked'); }, removeItem() { throw Error('blocked'); } };
  const { runtime, analysis } = setup(async () => result, throwing);
  await runtime.runtime.sendMessage({ type: 'phishlens-analyze-text', text: 'body' });
  assert.equal((await analysis()).status, 'success');
});

test('unknown messages are ignored and the hosted judge reports missing model assets', async () => {
  const { runtime } = setup(async () => result);
  assert.equal(await runtime.runtime.sendMessage({ type: 'phishlens-run-judge' }), undefined);
  assert.deepEqual(await unavailableJudge(), { ok: false, code: 'model_assets_missing' });
});

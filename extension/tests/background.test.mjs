import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const source = (await readFile(new URL('../background.js', import.meta.url), 'utf8'))
  .replace(/^import .+;$/gm, '');
const settle = () => new Promise(resolve => setImmediate(resolve));
function deferred() {
  let resolve, reject; const promise = new Promise((a, b) => { resolve = a; reject = b; });
  return { promise, resolve, reject };
}
function worker({ firstWrite } = {}) {
  let listener, clicks, writes = 0;
  const requests = [], state = { analysis: undefined, badge: '' };
  const storage = {};
  const context = vm.createContext({
    console, crypto: globalThis.crypto,
    fetch() { throw Error('Local scans must not call an HTTP API'); },
    analyzeWithReview: text => { const d = deferred(); requests.push({ ...d, text }); return d.promise; },
    cancelJudge: async () => {},
    chrome: {
      runtime: { id: 'self', onInstalled: { addListener() {} },
        onMessage: { addListener(fn) { listener = fn; } } },
      contextMenus: { onClicked: { addListener(fn) { clicks = fn; } } },
      storage: { session: {
        async get(key) { return { [key]: storage[key] }; },
        async set(value) {
          if (writes++ === 0 && firstWrite) await firstWrite.promise;
          Object.assign(storage, value); state.analysis = storage.veriqoAnalysis;
        },
        async remove(key) { delete storage[key]; state.analysis = storage.veriqoAnalysis; }
      } },
      action: { async setBadgeText({ text }) { state.badge = text; } }
    }
  });
  vm.runInContext(source, context);
  return { state, requests, storage, clicks,
    analyze: text => context.analyzeSelectedText(text),
    message: (message, sender = { id: 'self' }) => listener(message, sender, () => {}),
    clear: () => new Promise(resolve => {
      assert.equal(listener({ type: 'phishlens-clear-analysis' }, { id: 'self' }, resolve), true);
    })
  };
}
for (const outcome of ['success', 'error']) {
  test('latest scan wins over an older ' + outcome, async () => {
    const app = worker(), older = app.analyze('A'); await settle();
    const newer = app.analyze('B'); await settle();
    app.requests[1].resolve({ alert: true, workflow: { released: true } }); await newer;
    if (outcome === 'success') app.requests[0].resolve({ alert: false, workflow: { released: true } });
    else app.requests[0].reject(Error('old failure'));
    await older;
    assert.equal(app.state.analysis.selectedText, 'B'); assert.equal(app.state.badge, '!');
  });
  test('Clear invalidates in-flight ' + outcome, async () => {
    const app = worker(), pending = app.analyze('A'); await settle(); await app.clear();
    if (outcome === 'success') app.requests[0].resolve({ alert: false, workflow: { released: true } });
    else app.requests[0].reject(Error('old failure'));
    await pending; assert.equal(app.state.analysis, undefined); assert.equal(app.state.badge, '');
  });
}
test('Clear waits for a pending write without starting stale inference', async () => {
  const firstWrite = deferred(), app = worker({ firstWrite }), scan = app.analyze('A'); await settle();
  const clear = app.clear(); firstWrite.resolve(); await Promise.all([scan, clear]);
  assert.equal(app.requests.length, 0); assert.equal(app.state.analysis, undefined);
});
test('local failure is unavailable, never a safe result, and permits retry', async () => {
  const app = worker(), failed = app.analyze('A'); await settle();
  app.requests[0].reject(Error('Packaged model missing')); await failed;
  assert.equal(app.state.analysis.status, 'error'); assert.equal(app.state.analysis.result, null);
  assert.equal(app.state.badge, '?');
  const retry = app.analyze('B'); await settle(); app.requests[1].resolve({ alert: false, workflow: { released: true } }); await retry;
  assert.equal(app.state.analysis.status, 'success'); assert.equal(app.state.badge, '·');
});
test('debug failure is consumed once and requires no inference/API call', async () => {
  const app = worker(); app.storage.phishlensDebugFailNext = true; await app.analyze('A');
  assert.equal(app.requests.length, 0); assert.equal(app.storage.phishlensDebugFailNext, undefined);
  assert.match(app.state.analysis.error, /Simulated/);
});
test('other extensions cannot submit or clear scan state', async () => {
  const app = worker();
  assert.equal(app.message({ type: 'phishlens-clear-analysis' }, { id: 'stranger' }), undefined);
  assert.equal(app.message({ type: 'phishlens-analyze-text', text: 'private' }, { id: 'stranger' }), undefined);
  assert.equal(app.requests.length, 0);
});

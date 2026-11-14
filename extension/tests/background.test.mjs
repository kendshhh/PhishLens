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
function worker({ firstWrite, popupFailure = false, selectionResult, selectionFailure = false } = {}) {
  let listener, clicks, installed, sidePanelBehavior, writes = 0;
  const requests = [], popups = [], injections = [], state = { analysis: undefined, badge: '' };
  // The manifest defines no default popup; the worker sets one only for a right-click.
  const actionLog = [], popupConfig = { global: '' };
  let currentTab;
  const storage = {};
  const context = vm.createContext({
    console, crypto: globalThis.crypto,
    fetch() { throw Error('Local scans must not call an HTTP API'); },
    analyzeWithReview: text => { const d = deferred(); requests.push({ ...d, text }); return d.promise; },
    cancelJudge: async () => {},
    chrome: {
      runtime: { id: 'self', onInstalled: { addListener(fn) { installed = fn; } },
        onMessage: { addListener(fn) { listener = fn; } } },
      contextMenus: { removeAll() {}, create() {}, onClicked: { addListener(fn) { clicks = fn; } } },
      sidePanel: { async setPanelBehavior(value) { sidePanelBehavior = value; },
        open() { throw Error('Right-click must open the popup, not the side panel'); } },
      scripting: { async executeScript(options) {
        injections.push(options);
        if (selectionFailure) throw Error('Frame access denied');
        return [{ result: await selectionResult }];
      } },
      storage: { session: {
        async get(key) { return { [key]: storage[key] }; },
        async set(value) {
          if (writes++ === 0 && firstWrite) await firstWrite.promise;
          Object.assign(storage, value); state.analysis = storage.veriqoAnalysis;
        },
        async remove(key) { delete storage[key]; state.analysis = storage.veriqoAnalysis; }
      } },
      action: { async setBadgeText({ text }) { state.badge = text; },
        async setPopup({ tabId, popup }) {
          actionLog.push(['setPopup', tabId ?? 'global', popup]);
          popupConfig[tabId ?? 'global'] = popup;
        },
        async openPopup(options) {
          actionLog.push(['openPopup']);
          popups.push({ options, status: state.analysis?.status, text: state.analysis?.selectedText,
            popup: popupConfig[currentTab] ?? popupConfig.global });
          if (popupFailure) throw Error('Popup unavailable');
        } }
    }
  });
  vm.runInContext(source, context);
  return { state, requests, storage, popups, injections, actionLog, popupConfig,
    clicks: (info, tab) => { currentTab = tab?.id; return clicks(info, tab); },
    sidePanelBehavior: () => sidePanelBehavior, install: () => installed(),
    analyze: text => context.analyzeSelectedText(text),
    message: (message, sender = { id: 'self' }) => listener(message, sender, () => {}),
    clear: () => new Promise(resolve => {
      assert.equal(listener({ type: 'phishlens-clear-analysis' }, { id: 'self' }, resolve), true);
    }),
    cancel: () => new Promise(resolve => {
      assert.equal(listener({ type: 'phishlens-cancel-analysis' }, { id: 'self' }, resolve), true);
    })
  };
}
test('installation makes the toolbar button open the side panel as a secondary entry point', async () => {
  const app = worker();
  app.install();
  await settle();
  assert.equal(app.sidePanelBehavior().openPanelOnActionClick, true);
});
test('right-click opens the popup in the source window after storing the selection, before inference finishes', async () => {
  const app = worker();
  const scan = app.clicks({ menuItemId: 'phishlens-analyze-selection', selectionText: 'Selected <img src=x> text' }, { windowId: 7 });
  await settle();
  assert.equal(app.popups.length, 1);
  assert.equal(app.popups[0].options.windowId, 7);
  assert.equal(app.popups[0].status, 'loading');
  assert.equal(app.popups[0].text, 'Selected <img src=x> text');
  app.requests[0].resolve({ alert: false, workflow: { released: true } }); await scan;
  assert.equal(app.state.analysis.status, 'success');
});
test('right-click sets the popup only for its tab, opens it, then restores the toolbar side panel', async () => {
  const app = worker();
  const scan = app.clicks({ menuItemId: 'phishlens-analyze-selection', selectionText: 'Selected text' }, { id: 12, windowId: 7 });
  await settle(); await settle();
  assert.deepEqual(app.actionLog.map(entry => [...entry]), [
    ['setPopup', 12, 'popup.html?surface=popup'], ['openPopup'], ['setPopup', 12, '']
  ]);
  assert.equal(app.popups[0].popup, 'popup.html?surface=popup');
  assert.equal(app.popupConfig[12], '', 'The toolbar must open the side panel again on this tab');
  assert.equal(app.popupConfig.global, '', 'No global popup may override the side panel');
  app.requests[0].resolve({ alert: false, workflow: { released: true } }); await scan;
});
test('popup failure does not prevent selected-text analysis, lose its result or leave a popup configured', async () => {
  const app = worker({ popupFailure: true });
  const scan = app.clicks({ menuItemId: 'phishlens-analyze-selection', selectionText: 'Selected text' }, { id: 12 });
  await settle();
  app.requests[0].resolve({ alert: true, workflow: { released: true } }); await scan;
  assert.equal(app.state.analysis.selectedText, 'Selected text');
  assert.equal(app.state.analysis.status, 'success');
  assert.equal(app.popupConfig[12], '');
  assert.equal(app.popupConfig.global, '');
});
test('right-click preserves paragraph breaks, repeated spaces and tabs from the source frame', async () => {
  const original = 'Dear team,\n\n  Review\tthe agenda.\n\nRegards,\nNicole';
  const app = worker({ selectionResult: original });
  const pending = app.clicks({ menuItemId: 'phishlens-analyze-selection', frameId: 4,
    selectionText: 'Dear team, Review the agenda. Regards, Nicole' }, { id: 12, windowId: 7 });
  await settle();
  assert.equal(app.injections[0].target.tabId, 12);
  assert.equal(app.injections[0].target.frameIds[0], 4);
  assert.equal(app.state.analysis.selectedText, original);
  assert.equal(app.requests[0].text, original);
  app.requests[0].resolve({ alert: false, workflow: { released: true } }); await pending;
});
for (const options of [{ selectionResult: 'Different selection' }, { selectionFailure: true }]) {
  test('unavailable or changed source selection falls back to the original context-menu text ' + JSON.stringify(options), async () => {
    const app = worker(options);
    const pending = app.clicks({ menuItemId: 'phishlens-analyze-selection', selectionText: 'Original menu text' }, { id: 12 });
    await settle();
    assert.equal(app.requests[0].text, 'Original menu text');
    app.requests[0].resolve({ alert: false, workflow: { released: true } }); await pending;
  });
}
test('a delayed selection read cannot replace a newer scan', async () => {
  const selection = deferred(), app = worker({ selectionResult: selection.promise });
  const older = app.clicks({ menuItemId: 'phishlens-analyze-selection', selectionText: 'Old text' }, { id: 12 });
  const newer = app.analyze('New text'); await settle();
  selection.resolve('Old text'); await older;
  assert.equal(app.requests.length, 1);
  assert.equal(app.requests[0].text, 'New text');
  app.requests[0].resolve({ alert: false, workflow: { released: true } }); await newer;
});
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
for (const outcome of ['success', 'error']) {
  test('Cancel retains the original selection and rejects late ' + outcome, async () => {
    const app = worker();
    const pending = app.analyze('  Original\n\nselection  '); await settle();
    await app.cancel();
    assert.equal(app.state.analysis.status, 'cancelled');
    assert.equal(app.state.analysis.selectedText, '  Original\n\nselection  ');
    if (outcome === 'success') app.requests[0].resolve({ alert: true, workflow: { released: true } });
    else app.requests[0].reject(Error('Late failure'));
    await pending;
    assert.equal(app.state.analysis.status, 'cancelled');
    assert.equal(app.state.badge, '');
    const retry = app.analyze(app.state.analysis.selectedText); await settle();
    app.requests[1].resolve({ alert: false, workflow: { released: true } }); await retry;
    assert.equal(app.state.analysis.status, 'success');
  });
}
test('other extensions cannot submit or clear scan state', async () => {
  const app = worker();
  assert.equal(app.message({ type: 'phishlens-clear-analysis' }, { id: 'stranger' }), undefined);
  assert.equal(app.message({ type: 'phishlens-cancel-analysis' }, { id: 'stranger' }), undefined);
  assert.equal(app.message({ type: 'phishlens-analyze-text', text: 'private' }, { id: 'stranger' }), undefined);
  assert.equal(app.requests.length, 0);
});

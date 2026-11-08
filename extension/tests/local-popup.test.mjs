import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { initializePopup } from '../js/popup.js';
import { createLocalAnalyzer, MODEL_SHA256 } from '../ai/local-analyzer.mjs';
import { createReevaluator } from '../ai/reevaluators.mjs';
import { releaseWorkflow, validateJudge, quoteOptions } from '../ai/judge-contract.mjs';

const settle = () => new Promise(resolve => setImmediate(resolve));
const analyze = createLocalAnalyzer({ fetchImpl: async url => new Response(await readFile(new URL(url))) });
const primary = await analyze('Please review the project meeting agenda. Do not share your password.');
const checks = createReevaluator({ fetchImpl: async url => new Response(await readFile(new URL(url))), getBasis: () => analyze.getAssets() });
const judge = validateJudge(JSON.stringify({ audit: 'supported', evidence_id: quoteOptions(primary)[0].id,
  reason_code: 'protective_or_routine_context', missing_context: false }), primary);
const r = releaseWorkflow(primary, judge, await checks(primary));
const scan = { status: 'success', result: r, selectedText: 'Please review the project meeting agenda. Do not share your password.', scanId: 'scan-1' };
const record = { id: '29d80c39-ec0d-4db8-a6e5-87444ba2600c', subject: 'Notice <img src=x>',
  prediction: 'legitimate', confidence: null, risk_level: 'low', threat_indicators: [], explanation: 'Check independently.',
  created_at: '2026-10-29T02:00:00Z', body: scan.selectedText, notes: null, feedback: 'none', analysis_mode: 'real',
  analysis_provenance: { model_revision: MODEL_SHA256, phishing_score: r.score, alert_threshold_score: r.alert_threshold_score, assessment: r.assessment } };
class Element {
  constructor() {
    this.children = []; this.handlers = {}; this._text = ''; this.value = ''; this.checked = false;
    const classes = new Set(['hidden']);
    this.classList = { toggle: (c, yes) => yes ? classes.add(c) : classes.delete(c),
      add: c => classes.add(c), remove: c => classes.delete(c), contains: c => classes.has(c) };
  }
  set textContent(value) { this._text = value; this.children = []; }
  get textContent() { return this._text + this.children.map(c => c.textContent).join(''); }
  append(...items) { this.children.push(...items); }
  appendChild(item) { this.append(item); }
  replaceChildren(...items) { this._text = ''; this.children = items; }
  addEventListener(event, fn) { this.handlers[event] = fn; }
  setAttribute(name, value) { this[name] = value; }
  focus() { this.focused = true; }
  async fire(name) { return this.handlers[name]?.({ preventDefault() {} }); }
  async click() { return this.fire('click'); }
}
async function popup(fetchImpl = async () => { throw Error('Unexpected API call'); }, shared = { veriqoAnalysis: scan }, overrides = {}) {
  const html = await readFile(new URL('../popup.html', import.meta.url), 'utf8');
  const elements = new Map([...html.matchAll(/id="([^"]+)"/g)].map(m => [m[1], new Element()]));
  let onChanged;
  const chromeImpl = {
    storage: { session: { get: async key => ({ [key]: shared[key] }), set: async data => Object.assign(shared, data),
      remove: async key => { delete shared[key]; } },
      onChanged: { addListener(fn) { onChanged = fn; } } },
    runtime: { async sendMessage() { onChanged({ veriqoAnalysis: { newValue: undefined } }, 'session'); return { ok: true }; } }
  };
  if (overrides.sendMessage) chromeImpl.runtime.sendMessage = overrides.sendMessage;
  if (overrides.setSession) chromeImpl.storage.session.set = overrides.setSession;
  const app = initializePopup({ documentImpl: { getElementById: id => elements.get(id),
    createElement: () => new Element(), createTextNode: value => ({ textContent: value }) }, chromeImpl, fetchImpl });
  await settle(); return { app, dom: elements, shared };
}
const ok = (data, status = 200) => ({ ok: true, status, json: async () => data });
test('opening popup and showing a scan makes no network request', async () => {
  let calls = 0; const { dom } = await popup(async () => { calls++; throw Error('network'); });
  assert.equal(calls, 0); assert.equal(dom.get('result-state').classList.contains('hidden'), false);
  assert.equal(dom.has('threshold'), false);
  assert.equal(dom.has('analysis-text'), false);
  assert.equal(dom.get('coverage').textContent, '');
  assert.match(dom.get('report-save-state').textContent, /Not saved yet/);
  assert.match(dom.get('evidence').textContent, /protective|not to disclose/i);
  assert.doesNotMatch(dom.get('evidence').textContent, /undefined/);
  assert.equal(dom.get('selection-content').textContent, scan.selectedText);
  assert.equal(dom.get('selection-preview').classList.contains('hidden'), false);
  assert.equal(dom.get('selection-instructions').classList.contains('hidden'), true);
});

test('a new highlighted selection shows its original text during loading, failure and completion', async () => {
  const { app, dom } = await popup();
  const text = '  Highlighted <img src=x> email\nOriginal spacing.  ';
  for (const status of ['loading', 'error', 'success']) {
    app.render({ ...scan, selectedText: text, status, error: 'Synthetic model failure' });
    assert.equal(dom.get('selection-content').textContent, text);
    assert.equal(dom.get('selection-preview').classList.contains('hidden'), false);
  }
  assert.equal(dom.get('paste-panel').open, false);
  app.render(undefined);
  assert.equal(dom.get('selection-preview').classList.contains('hidden'), true);
  assert.equal(dom.get('selection-content').textContent, '');
});
test('report navigation explicitly loads history and returning to checking retains the draft', async () => {
  let calls = 0;
  const { dom } = await popup(async () => { calls++; return ok({ items: [] }); });
  dom.get('scan-body').value = 'Synthetic draft';
  await dom.get('show-reports').click(); await settle();
  assert.equal(calls, 1);
  assert.equal(dom.get('reports-view').classList.contains('hidden'), false);
  assert.equal(dom.get('check-view').classList.contains('hidden'), true);
  assert.equal(dom.get('show-reports')['aria-pressed'], 'true');
  await dom.get('show-check').click();
  assert.equal(dom.get('check-view').classList.contains('hidden'), false);
  assert.equal(dom.get('scan-body').value, 'Synthetic draft');
  assert.equal(calls, 1);
});

test('result summaries explain uncertainty and below-threshold outcomes without a safe verdict', async () => {
  const { app, dom } = await popup();
  app.render({ ...scan, result: { ...r, alert: false, workflow: { ...r.workflow, released: true } } });
  assert.equal(dom.get('classification').textContent, 'No strong warning signs');
  assert.match(dom.get('assessment').textContent, /does not confirm.*genuine/);
  app.render({ ...scan, result: { ...r, input_truncated: true } });
  assert.match(dom.get('coverage').textContent, /Only part.*was checked/);
  app.render({ ...scan, result: { ...r, workflow: { ...r.workflow, released: false,
    judge: { valid: false, code: 'model_assets_missing' } } } });
  assert.match(dom.get('classification').textContent, /Uncertain/);
  assert.match(dom.get('assessment').textContent, /isn’t installed.*incomplete/);
});
test('history is explicit, keeps untrusted strings as text and opens detail', async () => {
  const calls = []; const { dom } = await popup(async (url, options) => {
    calls.push([url, options]); return ok(url.endsWith(record.id) ? record : { items: [record] });
  });
  assert.equal(calls.length, 0); await dom.get('load-history').click();
  const item = dom.get('history-list').children[0];
  assert.match(item.textContent, /<img src=x>/); assert.match(item.textContent, /No strong warning signs/);
  const button = item.children[2];
  await button.click(); assert.equal(dom.get('detail-panel').classList.contains('hidden'), false);
});
test('malformed history is a visible error and does not hide local results', async () => {
  const { dom } = await popup(async () => ok({ wrong: [] }));
  await dom.get('load-history').click();
  assert.match(dom.get('crud-status').textContent, /malformed/);
  assert.equal(dom.get('result-state').classList.contains('hidden'), false);
});

for (const prediction of ['phishing', 'legitimate']) {
  test('uncertain history overrides the primary ' + prediction + ' label', async () => {
    const uncertain = { ...record, prediction, review_status: 'uncertain' };
    const { dom } = await popup(async () => ok({ items: [uncertain] }));
    await dom.get('load-history').click();
    const button = dom.get('history-list').children[0].children[1];
    assert.match(button.textContent, /Uncertain — review needed/);
    assert.doesNotMatch(button.textContent, /phishing|legitimate|below threshold/i);
  });
}
test('save requires explicit consent and blocks incompatible service without sending text', async () => {
  const calls = []; const { dom } = await popup(async (url, options) => {
    calls.push([url, options]); return ok({ provider_mode: 'gemini', accepts_tfidf_reports: false });
  });
  await dom.get('save-report').click(); assert.equal(calls.length, 0);
  assert.match(dom.get('save-status').textContent, /Report not saved\. To save it, check/);
  assert.match(dom.get('save-status').textContent, /agree to upload this email text/);
  assert.equal(dom.get('save-status').role, 'alert');
  assert.equal(dom.get('save-status').focused, true);
  dom.get('save-consent').checked = true; await dom.get('save-report').click();
  assert.equal(calls.length, 1); assert.match(calls[0][0], /model-info$/);
  assert.equal(calls[0][1].body, undefined); assert.match(dom.get('save-status').textContent, /temporarily unavailable/);
  assert.doesNotMatch(dom.get('save-status').textContent, /TF-IDF|request key/);
  assert.match(dom.get('save-status').textContent, /^Report not saved\./);
  assert.equal(dom.get('save-status').role, 'alert');
  assert.equal(dom.get('save-status').focused, true);
});
test('confirmed save retains success after refresh failure; notes and delete use contributors API', async () => {
  const calls = []; let saved = false;
  const { dom } = await popup(async (url, options) => {
    calls.push([url, options]);
    if (url.endsWith('/model-info')) return ok({ provider_mode: 'tfidf', accepts_tfidf_reports: true, accepts_local_reviews: true, model_sha256: MODEL_SHA256 });
    if (options.method === 'POST') {
      saved = true; assert.equal(options.headers['X-PhishLens-Model'], MODEL_SHA256);
      const input = JSON.parse(options.body);
      assert.equal(input.subject, ''); assert.equal(input.body, scan.selectedText);
      assert.equal(input.local_review.status, r.workflow.status); return ok(record, 201);
    }
    if (options.method === 'PATCH') { assert.deepEqual(JSON.parse(options.body), { notes: 'Observed', feedback: 'false_positive' }); return ok({ ...record, notes: 'Observed', feedback: 'false_positive' }); }
    if (options.method === 'DELETE') return ok(null, 204);
    if (saved && options.method === 'GET') throw Error('Refresh unavailable');
    return ok({ items: [] });
  });
  dom.get('save-consent').checked = true; await dom.get('save-report').click();
  assert.match(dom.get('save-status').textContent, /Report saved.*refreshes failed/);
  assert.equal(dom.get('report-save-state').classList.contains('hidden'), true);
  assert.equal(dom.get('reports-view').classList.contains('hidden'), true);
  await dom.get('view-saved-report').click();
  assert.equal(dom.get('reports-view').classList.contains('hidden'), false);
  assert.equal(dom.get('detail-panel').classList.contains('hidden'), false);
  await dom.get('save-report').click(); assert.equal(calls.filter(([, o]) => o.method === 'POST').length, 1);
  await dom.get('detail-content').children.at(-2).click();
  dom.get('edit-notes').value = 'Observed'; dom.get('edit-feedback').value = 'false_positive';
  await dom.get('edit-form').fire('submit');
  assert.equal(calls.filter(([, o]) => o.method === 'PATCH').length, 1);
  assert.match(dom.get('detail-content').textContent, /Observed/);
  await dom.get('detail-content').children.at(-1).click();
  assert.equal(calls.filter(([, o]) => o.method === 'DELETE').length, 0);
  await dom.get('cancel-delete').click();
  assert.equal(calls.filter(([, o]) => o.method === 'DELETE').length, 0);
  await dom.get('detail-content').children.at(-1).click();
  await dom.get('delete-confirm').fire('submit');
  assert.equal(calls.filter(([, o]) => o.method === 'DELETE').length, 1);
  assert.match(dom.get('save-status').textContent, /deleted/);
});
test('ambiguous create retry keeps the request key after popup reopening', async () => {
  const keys = [], shared = { veriqoAnalysis: scan };
  const fetcher = async (url, options) => {
    if (url.endsWith('/model-info')) return ok({ provider_mode: 'tfidf', accepts_tfidf_reports: true, accepts_local_reviews: true, model_sha256: MODEL_SHA256 });
    keys.push(options.headers['Idempotency-Key']); throw Error('Connection lost');
  };
  for (let i = 0; i < 2; i++) {
    const { dom } = await popup(fetcher, shared);
    if (i === 1) assert.match(dom.get('save-status').textContent, /^Save not confirmed/);
    dom.get('save-consent').checked = true; await dom.get('save-report').click();
    assert.match(dom.get('save-status').textContent, /^Save not confirmed/);
    assert.match(dom.get('report-save-state').textContent, /Save not confirmed/);
  }
  assert.equal(keys.length, 2); assert.equal(keys[0], keys[1]);
  const retryUnavailable = await popup(async () => ok({ provider_mode: 'unavailable', accepts_tfidf_reports: false }), shared);
  retryUnavailable.dom.get('save-consent').checked = true;
  await retryUnavailable.dom.get('save-report').click();
  assert.match(retryUnavailable.dom.get('save-status').textContent, /^Save not confirmed/);
  assert.doesNotMatch(retryUnavailable.dom.get('save-status').textContent, /^Report not saved/);
});
test('Clear removes the displayed scan', async () => {
  const { dom } = await popup(); await dom.get('clear-button').click();
  assert.equal(dom.get('empty-state').classList.contains('hidden'), false);
  assert.equal(dom.get('result-state').classList.contains('hidden'), true);
});

test('pasted analysis runs locally, preserves the exact draft and blocks duplicate submissions', async () => {
  const shared = {}, messages = [];
  let finish;
  const { dom } = await popup(undefined, shared, { sendMessage: message => {
    messages.push(message); return new Promise(resolve => { finish = resolve; });
  } });
  dom.get('scan-body').value = '  Synthetic pasted email\nKeep original spacing.  ';
  const running = dom.get('scan-form').fire('submit');
  await settle();
  assert.equal(dom.get('scan-button').disabled, true);
  await dom.get('scan-form').fire('submit');
  assert.deepEqual(messages, [{ type: 'phishlens-analyze-text', text: dom.get('scan-body').value }]);
  finish({ ok: true }); await running;
  assert.equal(dom.get('scan-button').disabled, false);
  const reopened = await popup(undefined, shared);
  assert.equal(reopened.dom.get('scan-body').value, dom.get('scan-body').value);
});

test('blank pasted text does not start analysis and runtime failure retains the draft', async () => {
  let calls = 0;
  const { dom } = await popup(undefined, {}, { sendMessage: async () => { calls++; throw Error('worker unavailable'); } });
  dom.get('scan-body').value = ' ';
  await dom.get('scan-form').fire('submit');
  assert.equal(calls, 0);
  dom.get('scan-body').value = 'Synthetic draft';
  await dom.get('scan-form').fire('submit');
  assert.equal(calls, 1);
  assert.equal(dom.get('scan-body').value, 'Synthetic draft');
  assert.match(dom.get('scan-status').textContent, /retained/);
  assert.equal(dom.get('scan-button').disabled, false);
});

test('retry and cancelled-check recovery reuse the exact original selection locally', async () => {
  const messages = [];
  const original = '  Original highlighted\n\n  email text.  ';
  const { app, dom } = await popup(undefined, {}, { sendMessage: async message => { messages.push(message); return { ok: true }; } });
  for (const [status, button] of [['error', 'retry-scan'], ['cancelled', 'resume-scan']]) {
    app.render({ status, selectedText: original, error: 'Synthetic failure' });
    await dom.get(button).click();
    assert.deepEqual(messages.at(-1), { type: 'phishlens-analyze-text', text: original });
  }
  assert.equal(dom.get('selection-content').textContent, original);
});

test('Cancel sends only a local cancellation message and shows retained text', async () => {
  let app;
  const messages = [];
  const setup = await popup(undefined, {}, { sendMessage: async message => {
    messages.push(message);
    app.render({ status: 'cancelled', selectedText: 'Original selection' });
    return { ok: true };
  } });
  app = setup.app;
  app.render({ status: 'loading', selectedText: 'Original selection' });
  await setup.dom.get('cancel-scan').click();
  assert.deepEqual(messages, [{ type: 'phishlens-cancel-analysis' }]);
  assert.equal(setup.dom.get('cancelled-state').classList.contains('hidden'), false);
  assert.equal(setup.dom.get('selection-content').textContent, 'Original selection');
});

test('a titled uncertain save restores the title and same request key on reopening', async () => {
  const shared = { veriqoAnalysis: scan }, keys = [];
  const fetcher = async (url, options) => {
    if (url.endsWith('/model-info')) return ok({ provider_mode: 'tfidf', accepts_tfidf_reports: true,
      accepts_local_reviews: true, model_sha256: MODEL_SHA256 });
    keys.push(options.headers['Idempotency-Key']); throw Error('Connection lost');
  };
  const first = await popup(fetcher, shared);
  first.dom.get('report-subject').value = 'My synthetic report';
  first.dom.get('save-consent').checked = true;
  await first.dom.get('save-report').click();
  const second = await popup(fetcher, shared);
  assert.equal(second.dom.get('report-subject').value, 'My synthetic report');
  assert.equal(second.dom.get('save-consent').checked, false);
  second.dom.get('save-consent').checked = true;
  await second.dom.get('save-report').click();
  assert.equal(keys.length, 2); assert.equal(keys[0], keys[1]);
});

test('a confirmed save is displayed even when persisting its local marker fails', async () => {
  const shared = { veriqoAnalysis: scan };
  const { dom } = await popup(async (url, options = {}) => {
    if (url.endsWith('/model-info')) return ok({ provider_mode: 'tfidf', accepts_tfidf_reports: true,
      accepts_local_reviews: true, model_sha256: MODEL_SHA256 });
    if (options.method === 'POST') return ok(record, 201);
    return ok(url.endsWith(record.id) ? record : { items: [record] });
  }, shared, { setSession: async data => {
    if (data.phishlensReportAttempt?.savedId) throw Error('Storage unavailable');
    Object.assign(shared, data);
  } });
  dom.get('save-consent').checked = true;
  await dom.get('save-report').click();
  assert.match(dom.get('save-status').textContent, /^Report saved\./);
  assert.match(dom.get('save-status').textContent, /marker/);
  await dom.get('view-saved-report').click();
  assert.equal(dom.get('detail-panel').classList.contains('hidden'), false);
});

test('saving a local scan blocks manual creation until the shared operation finishes', async () => {
  let releaseCapability;
  const calls = [];
  const { dom } = await popup(async (url, options = {}) => {
    calls.push([url, options]);
    if (url.endsWith('/model-info')) return new Promise(resolve => { releaseCapability = resolve; });
    if (options.method === 'POST') return ok(record, 201);
    return ok(url.endsWith(record.id) ? record : { items: [record] });
  });
  dom.get('save-consent').checked = true;
  const saving = dom.get('save-report').click();
  await settle();
  assert.equal(dom.get('create-body').disabled, true);
  assert.equal(dom.get('report-subject').disabled, true);
  assert.equal(dom.get('save-consent').disabled, true);
  dom.get('create-body').value = 'Do not submit while the scan is being saved.';
  await dom.get('create-form').fire('submit');
  assert.equal(calls.filter(([, options]) => options.method === 'POST').length, 0);
  releaseCapability(ok({ provider_mode: 'tfidf', accepts_tfidf_reports: true,
    accepts_local_reviews: true, model_sha256: MODEL_SHA256 }));
  await saving;
  assert.equal(calls.filter(([, options]) => options.method === 'POST').length, 1);
  assert.equal(dom.get('create-body').disabled, false);
  assert.equal(dom.get('report-subject').disabled, true);
  assert.equal(dom.get('save-consent').disabled, true);
  assert.equal(dom.get('save-report').disabled, true);
});

test('manual creation uses the matching model and blocks a concurrent local save', async () => {
  let releaseCreate;
  const calls = [];
  const { dom } = await popup(async (url, options = {}) => {
    calls.push([url, options]);
    if (options.method === 'POST') return new Promise(resolve => { releaseCreate = resolve; });
    return ok(url.endsWith(record.id) ? record : { items: [record] });
  });
  dom.get('create-body').value = 'Manually entered synthetic text.';
  const saving = dom.get('create-form').fire('submit');
  dom.get('save-consent').checked = true;
  await dom.get('save-report').click();
  assert.equal(calls.length, 1);
  assert.equal(calls[0][1].headers['X-PhishLens-Model'], MODEL_SHA256);
  assert.deepEqual(JSON.parse(calls[0][1].body), { subject: '', body: 'Manually entered synthetic text.' });
  releaseCreate(ok(record, 201));
  await saving;
  assert.equal(dom.get('result-state').classList.contains('hidden'), false);
  assert.equal(dom.get('save-report').disabled, false);
});

test('late history and detail reads cannot replace a newly saved local report', async () => {
  let releaseHistory, releaseDetail, histories = 0;
  const oldId = '00000000-0000-4000-8000-000000000001';
  const { app, dom } = await popup(async (url, options = {}) => {
    if (url.endsWith('/model-info')) return ok({ provider_mode: 'tfidf', accepts_tfidf_reports: true,
      accepts_local_reviews: true, model_sha256: MODEL_SHA256 });
    if (options.method === 'POST') return ok(record, 201);
    if (url.endsWith(oldId)) return new Promise(resolve => { releaseDetail = resolve; });
    if (url.endsWith('/api/analyses') && ++histories === 1) {
      return new Promise(resolve => { releaseHistory = resolve; });
    }
    return ok(url.endsWith(record.id) ? record : { items: [record] });
  });
  const oldHistory = app.loadHistory();
  const oldDetail = app.openDetail(oldId);
  dom.get('save-consent').checked = true;
  await dom.get('save-report').click();
  releaseHistory(ok({ items: [] }));
  releaseDetail(ok({ ...record, id: oldId, subject: 'Stale report' }));
  await Promise.all([oldHistory, oldDetail]);
  assert.equal(dom.get('history-list').children.length, 1);
  assert.match(dom.get('detail-content').textContent, /Notice <img src=x>/);
  assert.doesNotMatch(dom.get('detail-content').textContent, /Stale report/);
  assert.equal(dom.get('loading').classList.contains('hidden'), true);
});

test('saved detail preserves Uncertain and browser-attributed review provenance', async () => {
  const uncertain = { ...record, prediction: 'phishing', review_status: 'uncertain',
    analysis_provenance: { ...record.analysis_provenance, local_review: { status: 'uncertain' } } };
  const { app, dom } = await popup(async () => ok(uncertain));
  await app.openDetail(record.id);
  const fields = dom.get('detail-content').children;
  assert.equal(fields[3].children[1].textContent, 'Uncertain — review needed');
  assert.match(dom.get('detail-content').textContent, /local review was reported by the browser/);
  assert.doesNotMatch(dom.get('detail-content').textContent, /Alert threshold|Model revision|Research model score/);
});

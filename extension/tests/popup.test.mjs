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
  async click() { return this.handlers.click?.(); }
}
async function popup(fetchImpl = async () => { throw Error('Unexpected API call'); }, shared = { veriqoAnalysis: scan }) {
  const html = await readFile(new URL('../popup.html', import.meta.url), 'utf8');
  const elements = new Map([...html.matchAll(/id="([^"]+)"/g)].map(m => [m[1], new Element()]));
  let onChanged;
  const chromeImpl = {
    storage: { session: { get: async key => ({ [key]: shared[key] }), set: async data => Object.assign(shared, data),
      remove: async key => { delete shared[key]; } },
      onChanged: { addListener(fn) { onChanged = fn; } } },
    runtime: { async sendMessage() { onChanged({ veriqoAnalysis: { newValue: undefined } }, 'session'); return { ok: true }; } }
  };
  const app = initializePopup({ documentImpl: { getElementById: id => elements.get(id),
    createElement: () => new Element(), createTextNode: value => ({ textContent: value }) }, chromeImpl, fetchImpl });
  await settle(); return { app, dom: elements, shared };
}
const ok = (data, status = 200) => ({ ok: true, status, json: async () => data });
test('opening popup and showing a scan makes no network request', async () => {
  let calls = 0; const { dom } = await popup(async () => { calls++; throw Error('network'); });
  assert.equal(calls, 0); assert.equal(dom.get('result-state').classList.contains('hidden'), false);
  assert.match(dom.get('threshold').textContent, /88.71%/);
  assert.match(dom.get('evidence').textContent, /protective|not to disclose/i);
  assert.doesNotMatch(dom.get('evidence').textContent, /undefined/);
});
test('history is explicit, keeps untrusted strings as text and opens detail', async () => {
  const calls = []; const { dom } = await popup(async (url, options) => {
    calls.push([url, options]); return ok(url.endsWith(record.id) ? record : { items: [record] });
  });
  assert.equal(calls.length, 0); await dom.get('load-history').click();
  const button = dom.get('history-list').children[0].children[0];
  assert.match(button.textContent, /<img src=x>/); assert.match(button.textContent, /below threshold/);
  await button.click(); assert.equal(dom.get('detail-panel').classList.contains('hidden'), false);
});
test('malformed history is a visible error and does not hide local results', async () => {
  const { dom } = await popup(async () => ok({ wrong: [] }));
  await dom.get('load-history').click();
  assert.match(dom.get('error').textContent, /Invalid/);
  assert.equal(dom.get('result-state').classList.contains('hidden'), false);
});

for (const prediction of ['phishing', 'legitimate']) {
  test('uncertain history overrides the primary ' + prediction + ' label', async () => {
    const uncertain = { ...record, prediction, review_status: 'uncertain' };
    const { dom } = await popup(async () => ok({ items: [uncertain] }));
    await dom.get('load-history').click();
    const button = dom.get('history-list').children[0].children[0];
    assert.match(button.textContent, /Uncertain — local review not confirmed/);
    assert.doesNotMatch(button.textContent, /phishing|legitimate|below threshold/i);
  });
}
test('save requires explicit consent and blocks incompatible service without sending text', async () => {
  const calls = []; const { dom } = await popup(async (url, options) => {
    calls.push([url, options]); return ok({ provider_mode: 'gemini', accepts_tfidf_reports: false });
  });
  await dom.get('save-report').click(); assert.equal(calls.length, 0);
  dom.get('save-consent').checked = true; await dom.get('save-report').click();
  assert.equal(calls.length, 1); assert.match(calls[0][0], /model-info$/);
  assert.equal(calls[0][1].body, undefined); assert.match(dom.get('save-status').textContent, /disabled/);
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
  assert.match(dom.get('save-status').textContent, /Saved.*refreshes failed/);
  assert.equal(dom.get('detail-panel').classList.contains('hidden'), false);
  await dom.get('save-report').click(); assert.equal(calls.filter(([, o]) => o.method === 'POST').length, 1);
  dom.get('report-notes').value = 'Observed'; dom.get('report-feedback').value = 'false_positive';
  await dom.get('update-report').click(); assert.match(dom.get('detail-status').textContent, /saved/);
  await dom.get('delete-report').click(); assert.equal(calls.filter(([, o]) => o.method === 'DELETE').length, 0);
  dom.get('delete-consent').checked = true; await dom.get('delete-report').click();
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
    dom.get('save-consent').checked = true; await dom.get('save-report').click();
  }
  assert.equal(keys.length, 2); assert.equal(keys[0], keys[1]);
});
test('Clear removes the displayed scan', async () => {
  const { dom } = await popup(); await dom.get('clear-button').click();
  assert.equal(dom.get('empty-state').classList.contains('hidden'), false);
  assert.equal(dom.get('result-state').classList.contains('hidden'), true);
});

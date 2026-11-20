import test from 'node:test';
import assert from 'node:assert/strict';
import { initializeGhost, inspectText, moodFor } from '../js/ghost.js';

const PHISH = 'Dear customer, your account will be suspended. Kindly verify your password immediately.';

// A minimal side panel: the ghost, its bubble, the paste box and session storage.
function panel({ analysis = null } = {}) {
  const el = () => ({ dataset: {}, textContent: '', attributes: {}, listeners: {},
    classList: { names: new Set(), add(n) { this.names.add(n); }, remove(n) { this.names.delete(n); },
      toggle(n, on) { if (on) this.names.add(n); else this.names.delete(n); } },
    setAttribute(k, v) { this.attributes[k] = v; },
    addEventListener(type, fn) { this.listeners[type] = fn; } });
  const elements = { ghost: el(), 'ghost-bubble': el(), 'scan-body': Object.assign(el(), { value: '' }) };
  let onChanged;
  const chromeImpl = { storage: {
    onChanged: { addListener(fn) { onChanged = fn; } },
    session: { get: async () => ({ veriqoAnalysis: analysis }) } } };
  initializeGhost({ documentImpl: { getElementById: id => elements[id] ?? null }, chromeImpl });
  return {
    get mood() { return elements.ghost.dataset.mood; },
    type(value) { elements['scan-body'].value = value; elements['scan-body'].listeners.input(); },
    setAnalysis(value) { onChanged({ veriqoAnalysis: { newValue: value } }, 'session'); }
  };
}
const settle = async mock => { await Promise.resolve(); await Promise.resolve(); mock.timers.tick(250); };

test('the ghost stays calm for ordinary text', () => {
  assert.equal(moodFor(inspectText('Hi team, the meeting moved to 3pm tomorrow.')), 'calm');
  assert.equal(moodFor(inspectText('')), 'calm');
  assert.equal(moodFor(inspectText(undefined)), 'calm');
});

test('a single phishing cue makes the ghost curious', () => {
  const found = inspectText('Kindly see the notes below.');
  assert.deepEqual(found.cues, ['kindly']);
  assert.equal(moodFor(found), 'curious');
});

test('several cues or a red-flag request make the ghost shocked', () => {
  const phishy = inspectText('Dear customer, your account will be suspended unless you verify your account immediately.');
  assert.ok(phishy.cues.length >= 2);
  assert.equal(moodFor(phishy), 'shocked');
  const secret = inspectText('Please send me your password.');
  assert.deepEqual(secret.flags, ['sensitive']);
  assert.equal(moodFor(secret), 'shocked');
});

test('an alerting result shocks the ghost even without cues', () => {
  assert.equal(moodFor({ cues: [], flags: [] }, { alert: true }), 'shocked');
});

test('cues match whole words only', () => {
  assert.deepEqual(inspectText('The unblocked lockedin prizes').cues, []);
});

test('the ghost calms down when the pasted phishing text is deleted, even after a check', async t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const ui = panel();
  await settle(t.mock);
  ui.type(PHISH); t.mock.timers.tick(250);
  assert.equal(ui.mood, 'shocked');
  // Checking the pasted text stores the same text as the current analysis.
  ui.setAnalysis({ status: 'success', selectedText: PHISH, result: {} });
  assert.equal(ui.mood, 'shocked');
  ui.type(''); t.mock.timers.tick(250);
  assert.equal(ui.mood, 'calm');
});

test('clearing the local scan calms the ghost even though the draft text remains', async t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const ui = panel({ analysis: { status: 'success', selectedText: PHISH, result: {} } });
  await settle(t.mock);
  assert.equal(ui.mood, 'shocked');
  ui.type(PHISH); t.mock.timers.tick(250);
  ui.setAnalysis(undefined);
  assert.equal(ui.mood, 'calm');
  // Typing again resumes reacting to the text box.
  ui.type(PHISH + ' '); t.mock.timers.tick(250);
  assert.equal(ui.mood, 'shocked');
});

test('a pending keystroke cannot re-shock the ghost after the scan is cleared', async t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const ui = panel();
  await settle(t.mock);
  ui.type(PHISH);
  ui.setAnalysis(undefined);
  t.mock.timers.tick(250);
  assert.equal(ui.mood, 'calm');
});

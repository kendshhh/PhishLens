import test from 'node:test';
import assert from 'node:assert/strict';
import { clampPosition, initializeGhost, inspectText, moodFor } from '../js/ghost.js';

const PHISH = 'Dear customer, your account will be suspended. Kindly verify your password immediately.';

function element(extra = {}) {
  const listeners = {};
  return Object.assign({
    dataset: {}, style: {}, textContent: '', attributes: {}, listeners,
    classList: { names: new Set(), add(...n) { n.forEach(x => this.names.add(x)); }, remove(...n) { n.forEach(x => this.names.delete(x)); },
      toggle(n, on) { if (on) this.names.add(n); else this.names.delete(n); }, contains(n) { return this.names.has(n); } },
    setAttribute(k, v) { this.attributes[k] = v; },
    addEventListener(type, fn) { listeners[type] = fn; }
  }, extra);
}

// A minimal side panel: the ghost, its bubble, the scan editor and the result card.
function panel({ saved = null, view = { innerWidth: 360, innerHeight: 600 } } = {}) {
  const body = element({ setPointerCapture() {} });
  const ghost = element({ offsetWidth: 64, offsetHeight: 84, querySelector: s => s === '.ghost-body' ? body : null,
    getBoundingClientRect() { return { left: parseFloat(this.style.left) || 280, top: parseFloat(this.style.top) || 500 }; } });
  const result = element();
  result.classList.add('hidden');
  const elements = { ghost, 'ghost-bubble': element(), 'scan-body': element({ value: '' }),
    'scan-editor': element({ open: true }), 'result-state': result };
  const store = new Map(saved ? [['phishlensGhostPosition', JSON.stringify(saved)]] : []);
  let observe;
  const win = { ...view, addEventListener() {},
    localStorage: { getItem: k => store.get(k) ?? null, setItem: (k, v) => store.set(k, v), removeItem: k => store.delete(k) },
    MutationObserver: class { constructor(fn) { observe = fn; } observe() {} } };
  initializeGhost({ documentImpl: { getElementById: id => elements[id] ?? null }, windowImpl: win });
  const pointer = (type, x, y) => body.listeners[type]({ button: 0, pointerId: 1, clientX: x, clientY: y, preventDefault() {} });
  return {
    ghost, store,
    get mood() { return ghost.dataset.mood; },
    get bubble() { return elements['ghost-bubble'].textContent; },
    type(value) { elements['scan-body'].value = value; elements['scan-body'].listeners.input(); },
    setEditorOpen(open) { elements['scan-editor'].open = open; elements['scan-editor'].listeners.toggle(); },
    showResult(tone) { result.classList.toggle('hidden', !tone); result.dataset.tone = tone; observe(); },
    drag(from, to) { pointer('pointerdown', ...from); pointer('pointermove', ...to); pointer('pointerup', ...to); },
    doubleClick() { body.listeners.dblclick(); }
  };
}

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

test('the ghost reacts to the draft while typing and calms when it is deleted', t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const ui = panel();
  assert.equal(ui.mood, 'calm');
  ui.type(PHISH); t.mock.timers.tick(250);
  assert.equal(ui.mood, 'shocked');
  ui.type(''); t.mock.timers.tick(250);
  assert.equal(ui.mood, 'calm');
});

test('each verdict sets its own reaction', t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const ui = panel();
  ui.setEditorOpen(false);
  ui.showResult('suspicious');
  assert.equal(ui.mood, 'shocked');
  ui.showResult('uncertain');
  assert.equal(ui.mood, 'curious');
  assert.equal(ui.bubble, 'This needs a closer look.');
  ui.showResult('below');
  assert.equal(ui.mood, 'calm');
});

test('a pending keystroke cannot override a verdict that arrives first', t => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const ui = panel();
  ui.type(PHISH);
  ui.setEditorOpen(false);
  ui.showResult('below');
  t.mock.timers.tick(250);
  assert.equal(ui.mood, 'calm');
});

test('a dragged ghost stays inside the panel', () => {
  const size = { width: 64, height: 84 };
  const view = { innerWidth: 360, innerHeight: 600 };
  assert.deepEqual(clampPosition({ left: -50, top: -20 }, size, view), { left: 4, top: 4 });
  assert.deepEqual(clampPosition({ left: 999, top: 999 }, size, view), { left: 292, top: 512 });
  assert.deepEqual(clampPosition({ left: 100.4, top: 200.6 }, size, view), { left: 100, top: 201 });
});

test('dragging saves the position and a double-click resets it', () => {
  const ui = panel();
  ui.drag([300, 520], [70, 300]);
  assert.deepEqual([ui.ghost.style.left, ui.ghost.style.top], ['50px', '280px']);
  assert.ok(ui.ghost.classList.contains('bubble-right'));
  assert.deepEqual(JSON.parse(ui.store.get('phishlensGhostPosition')), { left: 50, top: 280 });
  ui.doubleClick();
  assert.deepEqual([ui.ghost.style.left, ui.ghost.style.top], ['', '']);
  assert.equal(ui.store.has('phishlensGhostPosition'), false);
});

test('a saved position is restored and kept inside a smaller panel', () => {
  const ui = panel({ saved: { left: 900, top: 40 }, view: { innerWidth: 320, innerHeight: 500 } });
  assert.deepEqual([ui.ghost.style.left, ui.ghost.style.top], ['252px', '40px']);
  assert.ok(ui.ghost.classList.contains('bubble-below'));
});

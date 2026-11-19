import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { initializeAccountUI } from '../js/account-ui.js';

class ClassList {
  constructor(value) { this.names = new Set(value.split(/\s+/).filter(Boolean)); }
  has(name) { return this.names.has(name); }
  contains(name) { return this.names.has(name); }
  add(name) { this.names.add(name); }
  remove(name) { this.names.delete(name); }
  toggle(name, force = !this.names.has(name)) { if (force) this.names.add(name); else this.names.delete(name); return force; }
}
class Element {
  constructor(classes = '') { this.classList = new ClassList(classes); this.textContent = ''; this.value = ''; this.dataset = {}; }
  addEventListener() {}
  setAttribute() {}
  removeAttribute() {}
  querySelectorAll() { return []; }
  focus() {}
}

async function render({ preview, status = 'signed-in' }) {
  const html = await readFile(new URL('../popup.html', import.meta.url), 'utf8');
  const elements = new Map([...html.matchAll(/<[^>]*\bid="([^"]+)"[^>]*>/g)].map(([tag, id]) =>
    [id, new Element(/\bclass="([^"]*)"/.exec(tag)?.[1] ?? '')]));
  const state = status === 'signed-in' ? { status, user: { name: 'Ada', email: 'ada@example.test' } } : { status };
  const accounts = { state, subscribe(fn) { fn(state); return () => {}; } };
  const doc = { getElementById: id => elements.get(id), querySelectorAll: () => [] };
  initializeAccountUI(accounts, doc, { preview });
  return elements;
}

test('the synthetic-records notice is hidden in markup until the app says it is a demo', async () => {
  const html = await readFile(new URL('../popup.html', import.meta.url), 'utf8');
  assert.match(html, /id="reports-preview-notice" class="[^"]*\bhidden\b/);
});

test('signed-in users of the real extension never see the synthetic-records notice', async () => {
  const elements = await render({ preview: false });
  assert.equal(elements.get('personal-reports').classList.has('hidden'), false);
  assert.equal(elements.get('reports-preview-notice').classList.has('hidden'), true);
});

test('the demo preview shows the synthetic-records notice', async () => {
  const elements = await render({ preview: true });
  assert.equal(elements.get('reports-preview-notice').classList.has('hidden'), false);
});

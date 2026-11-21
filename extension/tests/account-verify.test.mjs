import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { initializeAccountUI } from '../js/account-ui.js';

class ClassList {
  constructor(value) { this.names = new Set(value.split(/\s+/).filter(Boolean)); }
  contains(name) { return this.names.has(name); }
  toggle(name, force = !this.names.has(name)) { if (force) this.names.add(name); else this.names.delete(name); return force; }
}
class Element {
  constructor(classes = '') { this.classList = new ClassList(classes); this.textContent = ''; this.value = ''; this.listeners = {}; }
  addEventListener(type, fn) { this.listeners[type] = fn; }
  setAttribute() {}
  querySelectorAll() { return []; }
  focus() {}
  scrollIntoView() {}
  reportValidity() { return true; }
}

async function render(signIn) {
  const html = await readFile(new URL('../popup.html', import.meta.url), 'utf8');
  const elements = new Map([...html.matchAll(/<[^>]*\bid="([^"]+)"[^>]*>/g)].map(([tag, id]) =>
    [id, new Element(/\bclass="([^"]*)"/.exec(tag)?.[1] ?? '')]));
  const state = { status: 'signed-out' };
  const accounts = { state, signIn, subscribe(fn) { fn(state); return () => {}; } };
  initializeAccountUI(accounts, { getElementById: id => elements.get(id) });
  const $ = id => elements.get(id);
  return {
    $,
    shown: () => ['sign-in', 'sign-up', 'verify', 'recover', 'reset'].filter(name => !$('account-' + name).classList.contains('hidden')),
    async submitSignIn(email, password) {
      $('account-email').value = email; $('account-password').value = password;
      await $('account-sign-in').listeners.submit({ preventDefault() {} });
    }
  };
}

test('the sign-in screen does not offer email verification before credentials are submitted', async () => {
  const html = await readFile(new URL('../popup.html', import.meta.url), 'utf8');
  assert.doesNotMatch(html, /id="open-verify"/);
  const ui = await render(async () => true);
  ui.$('show-account').listeners.click();
  assert.deepEqual(ui.shown(), ['sign-in']);
});

test('submitting credentials for an unverified email opens verification with that email', async () => {
  const unverified = Object.assign(new Error('Verify your email before accessing saved reports.'), { status: 403 });
  const ui = await render(async () => { throw unverified; });
  await ui.submitSignIn(' casey@example.test ', 'Demo-only-123!');
  assert.deepEqual(ui.shown(), ['verify']);
  assert.equal(ui.$('verify-email').value, 'casey@example.test');
  assert.equal(ui.$('account-password').value, '');
  assert.match(ui.$('account-status').textContent, /Verify your email to finish signing in/);
});

test('other sign-in failures stay on sign-in and never ask for verification', async () => {
  const ui = await render(async () => { throw Object.assign(new Error('Email or password was not accepted. Sign in again.'), { status: 401 }); });
  await ui.submitSignIn('casey@example.test', 'wrong-password');
  assert.deepEqual(ui.shown(), ['sign-in']);
  assert.equal(ui.$('account-status').textContent, 'Email or password was not accepted. Sign in again.');
});

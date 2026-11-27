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
  constructor(classes = '', { type = '', required = false, readOnly = false } = {}) {
    this.classList = new ClassList(classes);
    this.textContent = '';
    this.value = '';
    this.listeners = {};
    this.type = type;
    this.required = required;
    this.readOnly = readOnly;
  }
  addEventListener(type, fn) { this.listeners[type] = fn; }
  setAttribute(name, value) { (this.attributes ??= {})[name] = value; }
  querySelectorAll() { return []; }
  focus() {}
  scrollIntoView() {}
  get validity() {
    if (this.readOnly) return { valid: true };
    if (this.required && !this.value) return { valid: false };
    if (this.type === 'email' && this.value && !/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(this.value)) {
      return { valid: false };
    }
    return { valid: true };
  }
  reportValidity() { return this.validity.valid; }
}

async function render(signIn, extra = {}, { editableVerificationEmail = false } = {}) {
  const html = await readFile(new URL('../popup.html', import.meta.url), 'utf8');
  const elements = new Map([...html.matchAll(/<[^>]*\bid="([^"]+)"[^>]*>/g)].map(([tag, id]) => {
    const attributes = {
      type: /\btype="([^"]+)"/.exec(tag)?.[1] ?? '',
      required: /\brequired\b/.test(tag),
      readOnly: /\breadonly\b/i.test(tag)
    };
    if (id === 'verify-email' && editableVerificationEmail) attributes.readOnly = false;
    return [id, new Element(/\bclass="([^"]*)"/.exec(tag)?.[1] ?? '', attributes)];
  }));
  const state = { status: 'signed-out' };
  const accounts = { state, signIn, ...extra, subscribe(fn) { fn(state); return () => {}; } };
  initializeAccountUI(accounts, { getElementById: id => elements.get(id) });
  const $ = id => elements.get(id);
  return {
    $,
    shown: () => ['sign-in', 'sign-up', 'verify', 'recover', 'reset'].filter(name => !$('account-' + name).classList.contains('hidden')),
    async submitVerify(email, code) {
      $('verify-email').value = email; $('verify-code').value = code;
      await $('account-verify').listeners.submit({ preventDefault() {} });
    },
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
  const unverified = Object.assign(new Error('Verify your email before signing in.'), { status: 403, code: 'EMAIL_NOT_VERIFIED' });
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

test('generic forbidden responses do not get misreported as email verification', async () => {
  const ui = await render(async () => { throw Object.assign(new Error('This account is not allowed to sign in.'), { status: 403 }); });
  await ui.submitSignIn('casey@example.test', 'password');
  assert.deepEqual(ui.shown(), ['sign-in']);
  assert.equal(ui.$('account-status').textContent, 'This account is not allowed to sign in.');
});

test('resend rejects missing and malformed emails before calling the adapter in an editable validation fixture', async () => {
  let resendCalls = 0;
  const ui = await render(async () => true, {
    resend: async () => { resendCalls += 1; }
  }, { editableVerificationEmail: true });
  const email = ui.$('verify-email');
  const originalStatus = ui.$('account-status').textContent;

  for (const invalidEmail of ['', 'not-an-email']) {
    email.value = invalidEmail;
    assert.equal(email.validity.valid, false);
    await ui.$('resend-code').listeners.click();
    assert.equal(resendCalls, 0);
    assert.equal(ui.$('account-status').textContent, originalStatus);
  }

  email.value = 'casey@example.test';
  assert.equal(email.validity.valid, true);
  await ui.$('resend-code').listeners.click();
  assert.equal(resendCalls, 1);
});

for (const [label, providerSignsIn] of [['without a session', false], ['even when the provider starts a session', true]]) {
  test(`successful verification confirms and returns to sign-in ${label}`, async () => {
    let signedOut = 0;
    const ui = await render(async () => true, {
      verifyEmail: async () => providerSignsIn,
      signOut: async () => { signedOut += 1; return true; }
    });
    await ui.submitVerify(' casey@example.test ', '123456');
    assert.deepEqual(ui.shown(), ['sign-in']);
    assert.equal(ui.$('account-email').value, 'casey@example.test');
    assert.equal(ui.$('account-status').textContent, 'Email verified successfully. Sign in with your email and password.');
    assert.equal(signedOut, providerSignsIn ? 1 : 0);
  });
}

test('if ending the provider session fails, verification is not reported as a plain success', async () => {
  let attempts = 0;
  const ui = await render(async () => true, {
    verifyEmail: async () => true,
    signOut: async () => { attempts += 1; return false; }
  });
  await ui.submitVerify('casey@example.test', '123456');
  assert.equal(attempts, 2, 'retries sign-out once');
  assert.deepEqual(ui.shown(), ['sign-in']);
  const status = ui.$('account-status');
  assert.doesNotMatch(status.textContent, /verified successfully/);
  assert.match(status.textContent, /could not end the session/);
  assert.equal(status.attributes.role, 'alert');
});

test('a sign-out that succeeds on the retry still reports success', async () => {
  let attempts = 0;
  const ui = await render(async () => true, {
    verifyEmail: async () => true,
    signOut: async () => ++attempts === 2
  });
  await ui.submitVerify('casey@example.test', '123456');
  assert.equal(attempts, 2);
  assert.equal(ui.$('account-status').textContent, 'Email verified successfully. Sign in with your email and password.');
  assert.equal(ui.$('account-status').attributes.role, 'status');
});

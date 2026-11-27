import test from 'node:test';
import assert from 'node:assert/strict';
import { createNeonAccounts } from '../js/neon-accounts.js';
import { createNeonIntegration } from '../js/neon-integration.js';
import { createAccountSession } from '../js/account-session.js';

const origin = 'https://auth.example.test';
const apiOrigin = 'https://api.example.test';
const authUrl = origin + '/test/auth';
const user = { id: 'user-a', name: 'Test A', email: 'a@example.test', emailVerified: true };
const jwt = (sub = user.id, exp = Date.now() / 1000 + 900) =>
  ['header', Buffer.from(JSON.stringify({ sub, exp })).toString('base64url'), 'signature'].join('.');
const session = token => ({ user, session: { expiresAt: new Date(Date.now() + 3600000).toISOString(), token } });

test('disabled integration does not initialize an SDK; configuration requires the API proxy permission and database', () => {
  assert.deepEqual(createNeonIntegration({ sdkFactory: () => assert.fail('SDK initialized') }), {});
  for (const config of [
    { authUrl, database: 'other', apiOrigin }, { authUrl, database: 'test', apiOrigin: 'https://wrong.test' },
    { authUrl: authUrl + '?secret=x', database: 'test', apiOrigin }
  ]) assert.throws(() => createNeonIntegration({ config: { enabled: true, ...config }, apiOrigin }), /configuration/);
});

test('actual bundled SDK uses credentialed bounded requests and injects current JWT into backend requests', async () => {
  const original = globalThis.fetch;
  const requests = [];
  let token = jwt(), active = true;
  globalThis.fetch = async (url, options = {}) => {
    const target = new URL(String(url));
    requests.push({ url: target.href, options });
    assert.equal(target.origin, apiOrigin, 'Auth and API traffic must use the same-origin backend');
    const path = target.pathname.replace('/api/auth', '');
    if (!target.pathname.startsWith('/api/auth/')) return Response.json({ items: [] });
    assert.equal(options.credentials, 'include');
    assert.equal(options.redirect, 'error');
    if (path.endsWith('/sign-out')) { active = false; return Response.json({ success: true }); }
    if (path.endsWith('/sign-in/email')) { active = true; return Response.json(session('opaque-cookie-token')); }
    if (path.endsWith('/get-session')) return Response.json(active ? session('opaque-cookie-token') : null,
      { headers: active ? { 'set-auth-jwt': token } : {} });
    if (/\/(sign-up\/email|forget-password\/email-otp|email-otp\/reset-password)$/.test(path)) {
      return Response.json({ success: true });
    }
    assert.fail('Unexpected SDK path: ' + path);
  };
  try {
    const { adapter, createClient } = createNeonIntegration({
      config: { enabled: true, authUrl, database: 'test', apiOrigin }, apiOrigin,
      hostPermissions: [origin + '/*', apiOrigin + '/*'], fetchImpl: (...args) => globalThis.fetch(...args)
    });
    const current = await adapter.restore();
    assert.equal(current.user.id, user.id);
    assert.equal('token' in current, false);
    const client = createClient(current);
    await client.listAnalyses();
    let apiCalls = requests.filter(r => new URL(r.url).pathname.startsWith('/api/analyses'));
    assert.equal(new Headers(apiCalls.at(-1).options.headers).get('Authorization'), 'Bearer ' + token);
    token = jwt(user.id, Date.now() / 1000 + 1800);
    await client.listAnalyses();
    apiCalls = requests.filter(r => new URL(r.url).pathname.startsWith('/api/analyses'));
    assert.equal(new Headers(apiCalls.at(-1).options.headers).get('Authorization'), 'Bearer ' + token);
    token = jwt('another-account');
    await assert.rejects(client.listAnalyses(), { status: 401 });
    assert.equal(requests.filter(r => new URL(r.url).pathname.startsWith('/api/analyses')).length, apiCalls.length);
    token = jwt();
    await adapter.signUp({ name: user.name, email: user.email, password: 'Synthetic-password-only' });
    assert.equal(adapter.verifyEmail, undefined);
    assert.equal(adapter.resend, undefined);
    assert.equal((await adapter.signIn({ email: user.email, password: 'Synthetic-password-only' })).user.id, user.id);
    await adapter.recover({ email: user.email });
    await adapter.resetPassword({ email: user.email, code: '123456', password: 'Synthetic-password-only' });
    assert.equal(await adapter.restore(), null);
    await adapter.signIn({ email: user.email, password: 'Synthetic-password-only' });
    await adapter.signOut();
    assert.equal(await adapter.getAccessToken(user.id), null);
    assert.equal(requests.some(r => /\/(email-otp\/verify-email|email-otp\/send-verification-otp)$/.test(new URL(r.url).pathname)), false);
  } finally { globalThis.fetch = original; }
});

test('rejects opaque, expired, or mismatched tokens without returning them', async () => {
  for (const token of ['opaque', jwt(user.id, 1), jwt('other')]) {
    const adapter = createNeonAccounts({ getSession: async () => ({ data: session(token) }) });
    if (token === 'opaque') await assert.rejects(adapter.getAccessToken(user.id), { status: 503 });
    else assert.equal(await adapter.getAccessToken(user.id), null);
  }
});

test('signup and sign-in establish sessions without an email verification code', async () => {
  let active = false;
  const unverifiedUser = { ...user, emailVerified: false };
  const sdk = {
    signUp: { email: async () => { active = true; return { data: { user: unverifiedUser } }; } },
    signIn: { email: async () => { active = true; return { data: { user: unverifiedUser } }; } },
    getSession: async () => ({ data: active ? { user: unverifiedUser,
      session: { expiresAt: new Date(Date.now() + 60000).toISOString(), token: jwt(user.id) } } : null }),
    signOut: async () => { active = false; return { data: { success: true } }; }
  };
  const adapter = createNeonAccounts(sdk);
  const created = await adapter.signUp({ name: user.name, email: user.email, password: 'synthetic-password' });
  assert.equal(created.user.emailVerified, false);
  assert.equal((await adapter.signIn({ email: user.email, password: 'synthetic-password' })).user.id, user.id);
});

test('actual SDK HTTP failures preserve safe sign-in, duplicate and recovery-code errors', async () => {
  const original = globalThis.fetch;
  const errors = [
    [401, 'INVALID_EMAIL_OR_PASSWORD', 401, /Email or password/, 'signIn'],
    [422, 'USER_ALREADY_EXISTS_USE_ANOTHER_EMAIL', 409, /Try signing in/, 'signUp'],
    [400, 'OTP_EXPIRED', 400, /This code expired/, 'resetPassword'],
    [429, 'TOO_MANY_REQUESTS', 429, /Too many attempts/, 'signIn']
  ];
  try {
    for (const [status, code, expectedStatus, message, method] of errors) {
      globalThis.fetch = async () => Response.json({ code, message: 'private-provider-value' }, { status });
      const { adapter } = createNeonIntegration({ apiOrigin,
        config: { enabled: true, authUrl, database: 'test', apiOrigin },
        hostPermissions: [origin + '/*', apiOrigin + '/*'] });
      const action = method === 'signUp'
        ? adapter.signUp({ name: user.name, email: user.email, password: 'Synthetic-password' })
        : method === 'resetPassword'
          ? adapter.resetPassword({ email: user.email, code: '123456', password: 'Synthetic-password' })
          : adapter.signIn({ email: user.email, password: 'Synthetic-password' });
      await assert.rejects(action, error =>
        error.status === expectedStatus && message.test(error.message) && !error.message.includes('private-provider-value'));
    }
  } finally { globalThis.fetch = original; }
});

test('service errors are sanitized and bounded; rate limits retain useful status', async () => {
  const adapter = createNeonAccounts({ getSession: async () => ({ error: { status: 429, message: 'secret token' } }) });
  await assert.rejects(adapter.restore(), error => error.status === 429 && !error.message.includes('secret'));
  const stalled = createNeonAccounts({ getSession: () => new Promise(() => {}) }, { timeoutMs: 5 });
  await assert.rejects(stalled.restore(), { status: 503 });
});

test('sign-out invalidates late restoration even if remote logout fails', async () => {
  let finish;
  const adapter = createNeonAccounts({ getSession: () => new Promise(resolve => { finish = resolve; }),
    signOut: async () => { throw new Error('private upstream error'); } });
  const pending = adapter.restore();
  await assert.rejects(adapter.signOut(), { status: 503 });
  finish({ data: session(jwt()) });
  assert.equal(await pending, null);
  assert.equal(await adapter.getAccessToken(user.id), null);
});

test('failed remote logout blocks restoration in a new popup until explicit sign-in', async () => {
  const values = new Map();
  const storage = {
    async get(key) { return { [key]: values.get(key) }; },
    async set(items) { for (const [key, value] of Object.entries(items)) values.set(key, value); },
    async remove(key) { values.delete(key); }
  };
  let reads = 0;
  const sdk = {
    async getSession() { reads++; return { data: session(jwt()) }; },
    async signOut() { return { error: { status: 503 } }; },
    signIn: { async email() { return { data: {} }; } }
  };
  const openPopup = () => createNeonIntegration({
    config: { enabled: true, authUrl, database: 'test', apiOrigin }, apiOrigin,
    hostPermissions: [origin + '/*', apiOrigin + '/*'], storage, sdkFactory: () => sdk
  }).adapter;
  const first = openPopup();
  assert.ok(await first.restore());
  await assert.rejects(first.signOut(), { status: 503 });
  assert.deepEqual([...values.values()], [true]);
  const reopened = openPopup();
  assert.equal(await reopened.restore(), null);
  assert.equal(await reopened.getAccessToken(user.id), null);
  assert.equal(reads, 1);
  await assert.rejects(reopened.signIn({ email: 'other@example.test', password: 'Synthetic-password' }), { status: 401 });
  assert.equal(await reopened.restore(), null);
  assert.ok(await reopened.signIn({ email: user.email, password: 'Synthetic-password' }));
  assert.equal(values.size, 0);
  assert.ok(await openPopup().restore());
});

test('a reopened popup keeps reports blocked until an unconfirmed sign-out is retried', async t => {
  let providerSession = true;
  let providerUnavailable = true;
  let localStorageUnavailable = true;
  let sessionReads = 0;
  let signInCalls = 0;
  const sdk = {
    async getSession() { sessionReads++; return { data: providerSession ? session(jwt()) : null }; },
    signIn: { async email() { signInCalls++; providerSession = true; return { data: {} }; } },
    async signOut() {
      if (providerUnavailable) return { error: { status: 503 } };
      providerSession = false;
      return { data: { success: true } };
    }
  };
  const local = {};
  const browserSession = {};
  const storage = {
    async get(key) { return { [key]: local[key] }; },
    async set(items) {
      if (localStorageUnavailable) throw new Error('Local storage unavailable');
      Object.assign(local, items);
    },
    async remove(key) { delete local[key]; }
  };
  const browserSessionStorage = {
    async get(key) { return { [key]: browserSession[key] }; },
    async set(items) { Object.assign(browserSession, items); },
    async remove(key) { delete browserSession[key]; }
  };
  const openPopup = () => {
    const { adapter, createClient } = createNeonIntegration({
      config: { enabled: true, authUrl, database: 'test', apiOrigin }, apiOrigin,
      hostPermissions: [apiOrigin + '/*'], storage, browserSessionStorage, sdkFactory: () => sdk
    });
    const accounts = createAccountSession({
      adapter, createClient,
      schedule: () => 0,
      cancel() {}
    });
    t.after(() => accounts.dispose());
    return accounts;
  };

  const first = openPopup();
  await first.ready;
  const states = [];
  first.subscribe(state => states.push(state.status));
  await first.signOut();

  assert.deepEqual(states, ['signed-in', 'signing-out', 'sign-out-unconfirmed']);
  assert.match(first.state.message, /session may still be active/);
  await assert.rejects(first.client.listAnalyses(), { code: 'session_required' });
  first.dispose();

  assert.deepEqual(Object.keys(local), []);
  assert.deepEqual(Object.values(browserSession), [true]);
  const reopened = openPopup();
  await reopened.ready;
  assert.equal(reopened.state.status, 'sign-out-unconfirmed');
  assert.match(reopened.state.message, /session may still be active/);
  assert.equal(sessionReads, 1);
  await assert.rejects(reopened.client.listAnalyses(), { code: 'session_required' });
  await assert.rejects(reopened.signIn({ email: user.email, password: 'Synthetic-password' }),
    { code: 'signout_unconfirmed' });
  assert.equal(signInCalls, 0);
  assert.equal(reopened.state.status, 'sign-out-unconfirmed');

  localStorageUnavailable = false;
  await reopened.signOut();
  assert.equal(reopened.state.status, 'sign-out-unconfirmed');
  assert.deepEqual(Object.values(browserSession), [true]);

  providerUnavailable = false;
  await reopened.signOut();
  assert.equal(reopened.state.status, 'signed-out');
  assert.deepEqual(Object.keys(browserSession), []);
  assert.equal(providerSession, false);
  const afterRetry = openPopup();
  await afterRetry.ready;
  assert.equal(afterRetry.state.status, 'signed-out');
  assert.ok(await afterRetry.signIn({ email: user.email, password: 'Synthetic-password' }));
});

test('invalid registration stays local and duplicate errors are sanitized', async () => {
  let signUps = 0;
  const adapter = createNeonAccounts({
    signUp: { async email() {
      signUps++;
      return { error: { status: 422, code: 'USER_ALREADY_EXISTS_USE_ANOTHER_EMAIL', message: 'private provider details' } };
    } }
  });
  const valid = { name: 'Test A', email: user.email, password: 'Synthetic-password' };
  for (const input of [{ name: '   ' }, { email: 'invalid' }, { password: 'short' }]) {
    await assert.rejects(adapter.signUp({ ...valid, ...input }), { status: 400 });
  }
  assert.equal(signUps, 0);
  await assert.rejects(adapter.signUp(valid), { status: 409, message: /Try signing in/ });
});

test('provider session renewal preserves reports and updates the expiry timer', async () => {
  let next = { user, expiresAt: 2000 }, delay;
  const changes = [];
  const accounts = createAccountSession({ adapter: { restore: async () => next }, createClient: () => ({}),
    onChange: id => changes.push(id), now: () => 1000, schedule: (_, ms) => { delay = ms; }, cancel() {} });
  await accounts.ready;
  next = { user, expiresAt: 5000 };
  await accounts.refresh();
  assert.equal(delay, 4000);
  assert.deepEqual(changes, [user.id]);
  accounts.dispose();
});

test('sign-in without a retained session is explicit', async () => {
  const ok = async () => ({ data: { success: true } });
  const adapter = createNeonAccounts({ signIn: { email: ok },
    getSession: async () => ({ data: null }) });
  await assert.rejects(adapter.signIn({ email: user.email, password: 'synthetic' }), /cookie permissions/);
});

test('provider account change clears reports and rejects an outstanding old-account read', async () => {
  let next = { user, expiresAt: 5000 }, finish;
  const accounts = createAccountSession({ adapter: { restore: async () => next },
    createClient: () => ({ listAnalyses: () => new Promise(resolve => { finish = resolve; }) }),
    now: () => 1000, schedule() {}, cancel() {} });
  await accounts.ready;
  const pending = accounts.client.listAnalyses();
  next = { user: { ...user, id: 'user-b' }, expiresAt: 5000 };
  await accounts.refresh();
  finish(['private-old-report']);
  await assert.rejects(pending, { status: 401 });
  assert.equal(accounts.state.status, 'expired');
  assert.equal(accounts.state.user, null);
  accounts.dispose();
});

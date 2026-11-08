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

test('disabled integration does not initialize an SDK; configuration requires exact origin permission and database', () => {
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
    assert.ok([origin, apiOrigin].includes(target.origin), 'unexpected network origin');
    if (target.origin === apiOrigin) return Response.json({ items: [] });
    assert.equal(options.credentials, 'include');
    assert.equal(options.redirect, 'error');
    const path = target.pathname;
    if (path.endsWith('/sign-out')) { active = false; return Response.json({ success: true }); }
    if (path.endsWith('/sign-in/email')) { active = true; return Response.json(session('opaque-cookie-token')); }
    if (path.endsWith('/get-session')) return Response.json(active ? session('opaque-cookie-token') : null,
      { headers: active ? { 'set-auth-jwt': token } : {} });
    if (/\/(sign-up\/email|email-otp\/verify-email|email-otp\/send-verification-otp|forget-password\/email-otp|email-otp\/reset-password)$/.test(path)) {
      return Response.json({ success: true });
    }
    assert.fail('Unexpected SDK path: ' + path);
  };
  try {
    const { adapter, createClient } = createNeonIntegration({
      config: { enabled: true, authUrl, database: 'test', apiOrigin }, apiOrigin,
      hostPermissions: [origin + '/*'], fetchImpl: (...args) => globalThis.fetch(...args)
    });
    const current = await adapter.restore();
    assert.equal(current.user.id, user.id);
    assert.equal('token' in current, false);
    const client = createClient(current);
    await client.listAnalyses();
    let apiCalls = requests.filter(r => r.url.startsWith(apiOrigin));
    assert.equal(new Headers(apiCalls.at(-1).options.headers).get('Authorization'), 'Bearer ' + token);
    token = jwt(user.id, Date.now() / 1000 + 1800);
    await client.listAnalyses();
    apiCalls = requests.filter(r => r.url.startsWith(apiOrigin));
    assert.equal(new Headers(apiCalls.at(-1).options.headers).get('Authorization'), 'Bearer ' + token);
    token = jwt('another-account');
    await assert.rejects(client.listAnalyses(), { status: 401 });
    assert.equal(requests.filter(r => r.url.startsWith(apiOrigin)).length, apiCalls.length);
    token = jwt();
    await adapter.signUp({ name: user.name, email: user.email, password: 'Synthetic-password-only' });
    await adapter.resend({ email: user.email });
    await adapter.verifyEmail({ email: user.email, code: '123456' });
    assert.equal((await adapter.signIn({ email: user.email, password: 'Synthetic-password-only' })).user.id, user.id);
    await adapter.recover({ email: user.email });
    await adapter.resetPassword({ email: user.email, code: '123456', password: 'Synthetic-password-only' });
    assert.equal(await adapter.restore(), null);
    await adapter.signIn({ email: user.email, password: 'Synthetic-password-only' });
    await adapter.signOut();
    assert.equal(await adapter.getAccessToken(user.id), null);
    assert.ok(requests.some(r => r.url.endsWith('/email-otp/verify-email') && JSON.parse(r.options.body).otp === '123456'));
  } finally { globalThis.fetch = original; }
});

test('rejects opaque, expired, or mismatched tokens without returning them', async () => {
  for (const token of ['opaque', jwt(user.id, 1), jwt('other')]) {
    const adapter = createNeonAccounts({ getSession: async () => ({ data: session(token) }) });
    if (token === 'opaque') await assert.rejects(adapter.getAccessToken(user.id), { status: 503 });
    else assert.equal(await adapter.getAccessToken(user.id), null);
  }
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

test('verification may succeed without a session; sign-in without a retained session is explicit', async () => {
  const ok = async () => ({ data: { success: true } });
  const adapter = createNeonAccounts({ emailOtp: { verifyEmail: ok }, signIn: { email: ok },
    getSession: async () => ({ data: null }) });
  assert.equal(await adapter.verifyEmail({ email: user.email, code: '123456' }), null);
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

import test from 'node:test';
import assert from 'node:assert/strict';
import { createAccountSession, unavailableAccounts } from '../js/account-session.js';
import { createMockAccounts } from '../../preview/mock-accounts.mjs';

const user = id => ({ user: { id, email: `${id}@example.test`, name: id, emailVerified: true }, expiresAt: 1000 });
function setup(overrides = {}) {
  let time = 0, expire;
  const changes = [], calls = [];
  const adapter = { ...unavailableAccounts, async signIn({ email }) { return user(email.split('@')[0]); }, ...overrides.adapter };
  const accounts = createAccountSession({ adapter, now: () => time,
    schedule: fn => { expire = fn; return 1; }, cancel() {},
    onChange: async id => { changes.push(id); },
    createClient: session => Object.fromEntries(['listAnalyses', 'getAnalysis', 'createAnalysis', 'updateAnalysis', 'deleteAnalysis'].map(method =>
      [method, async () => { calls.push([session.user.id, method]); return [session.user.id]; }])),
    ...overrides, adapter
  });
  return { accounts, changes, calls, expire() { time = 1001; expire(); } };
}

test('signed-out account boundary denies every saved-report operation without calling a client', async () => {
  const { accounts, calls } = setup(); await accounts.ready;
  for (const method of Object.keys(accounts.client)) await assert.rejects(accounts.client[method](), { status: 401 });
  assert.deepEqual(calls, []); accounts.dispose();
});

test('restores a verified unexpired session and clears account state before exposing it', async () => {
  const { accounts, changes } = setup({ adapter: { async restore() { return user('ada'); } } });
  await accounts.ready;
  assert.equal(accounts.state.user.id, 'ada');
  assert.deepEqual(changes, ['ada']);
  assert.deepEqual(await accounts.client.listAnalyses(), ['ada']); accounts.dispose();
});

test('expired and unverified restored sessions cannot load reports', async () => {
  for (const session of [{ ...user('ada'), expiresAt: 0 }, { ...user('ada'), user: { ...user('ada').user, emailVerified: false } }]) {
    const { accounts, calls } = setup({ adapter: { async restore() { return session; } } });
    await accounts.ready; assert.equal(accounts.state.status, 'expired');
    await assert.rejects(accounts.client.listAnalyses(), { status: 401 });
    assert.deepEqual(calls, []); accounts.dispose();
  }
});

test('sign-out and switching accounts clear the previous account before any next-account request', async () => {
  const { accounts, changes, calls } = setup(); await accounts.ready;
  await accounts.signIn({ email: 'ada@example.test' });
  await accounts.client.listAnalyses();
  await accounts.signOut();
  await assert.rejects(accounts.client.listAnalyses(), { status: 401 });
  await accounts.signIn({ email: 'bea@example.test' });
  assert.deepEqual(await accounts.client.listAnalyses(), ['bea']);
  assert.deepEqual(changes, [null, 'ada', null, null, 'bea']);
  assert.deepEqual(calls, [['ada', 'listAnalyses'], ['bea', 'listAnalyses']]); accounts.dispose();
});

test('late report reads and writes from the previous account are rejected', async () => {
  for (const method of ['listAnalyses', 'getAnalysis', 'createAnalysis', 'updateAnalysis', 'deleteAnalysis']) {
    let release;
    const { accounts } = setup({ createClient: () => ({ [method]: () => new Promise(resolve => { release = resolve; }) }) });
    await accounts.ready; await accounts.signIn({ email: 'ada@example.test' });
    const pending = accounts.client[method]();
    await accounts.signOut();
    release({ subject: 'Previous account report' });
    await assert.rejects(pending, /account changed/); accounts.dispose();
  }
});

test('late restoration cannot sign in again after sign-out', async () => {
  let restore;
  const { accounts } = setup({ adapter: { restore: () => new Promise(resolve => { restore = resolve; }) } });
  await accounts.signOut(); restore(user('ada')); await accounts.ready;
  assert.equal(accounts.state.status, 'signed-out'); accounts.dispose();
});

test('expiry clears the user and reports, with an explicit sign-in-again message', async () => {
  const { accounts, changes, expire } = setup(); await accounts.ready;
  await accounts.signIn({ email: 'ada@example.test' }); expire();
  assert.equal(accounts.state.status, 'expired'); assert.equal(accounts.state.user, null);
  assert.match(accounts.state.message, /expired.*Sign in again/);
  await assert.rejects(accounts.client.listAnalyses(), { status: 401 });
  assert.equal(changes.at(-1), null); accounts.dispose();
});

test('server 401 expires the session while 403 does not pretend the user is signed out', async () => {
  for (const status of [401, 403]) {
    const { accounts } = setup({ createClient: () => ({ async listAnalyses() { throw Object.assign(new Error('Denied'), { status }); } }) });
    await accounts.ready; await accounts.signIn({ email: 'ada@example.test' });
    await assert.rejects(accounts.client.listAnalyses(), { status });
    assert.equal(accounts.state.status, status === 401 ? 'expired' : 'signed-in'); accounts.dispose();
  }
});

test('failed remote sign-out still removes local access and shows the limitation', async () => {
  const { accounts } = setup({ adapter: { async signOut() { throw Error('Offline'); } } });
  await accounts.ready; await accounts.signIn({ email: 'ada@example.test' }); await accounts.signOut();
  assert.equal(accounts.state.user, null); assert.match(accounts.state.message, /could not confirm/); accounts.dispose();
});

test('demo signup, verification, recovery and restoration remain local and reject real email domains', async () => {
  const values = new Map();
  const storage = { getItem: key => values.get(key), setItem: (key, value) => values.set(key, value), removeItem: key => values.delete(key) };
  const adapter = createMockAccounts(storage);
  await assert.rejects(adapter.signUp({ name: 'Demo', email: 'someone@gmail.com', password: 'Demo-only-123!' }), /fictional/);
  await adapter.signUp({ name: '<img src=x>', email: 'new@example.test', password: 'Demo-only-123!' });
  await assert.rejects(adapter.signIn({ email: 'new@example.test', password: 'Demo-only-123!' }), /Verify/);
  await adapter.resend({ email: 'new@example.test' });
  await assert.rejects(adapter.verifyEmail({ email: 'new@example.test', code: '000000' }), /incorrect/);
  const session = await adapter.verifyEmail({ email: 'new@example.test', code: '123456' });
  assert.equal(session.user.emailVerified, true);
  assert.deepEqual(await adapter.restore(), session);
  assert.doesNotMatch([...values.values()].join(''), /password|Demo-only/);
  await adapter.signOut(); assert.equal(await adapter.restore(), null);
  await adapter.recover({ email: 'new@example.test' });
  await adapter.resetPassword({ email: 'new@example.test', code: '123456', password: 'Different-demo-123!' });
  await assert.rejects(adapter.signIn({ email: 'new@example.test', password: 'Demo-only-123!' }), /incorrect/);
  assert.ok(await adapter.signIn({ email: 'new@example.test', password: 'Different-demo-123!' }));
});

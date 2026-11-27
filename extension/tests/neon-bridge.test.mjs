import test from 'node:test';
import assert from 'node:assert/strict';
import { createNeonBridgeClient } from '../js/neon-bridge-client.js';
import { createNeonIntegration } from '../js/neon-integration.js';

const bridgeUrl = 'https://api.example.test/auth/bridge';
const authUrl = 'https://auth.example.test/neondb/auth';

function fixture(timeoutMs = 1000) {
  const events = new Map(), frameEvents = new Map(), requests = [];
  let removed = false;
  const frame = { setAttribute() {}, addEventListener: (name, callback) => frameEvents.set(name, callback),
    contentWindow: { postMessage: (data, origin) => requests.push({ data, origin }) },
    remove: () => { removed = true; } };
  const win = { addEventListener: (name, callback) => events.set(name, callback),
    removeEventListener: name => events.delete(name) };
  const doc = { defaultView: win, createElement: () => frame, body: { append() {} } };
  const sdk = createNeonBridgeClient({ bridgeUrl, authUrl, documentImpl: doc, timeoutMs });
  return { sdk, requests, frame, events, load: () => frameEvents.get('load')(),
    reply(request, changes = {}) { events.get('message')({ source: frame.contentWindow,
      origin: 'https://api.example.test', data: { type: 'phishlens-auth-result',
        channel: request.channel, id: request.id, result: { data: null } }, ...changes }); },
    get removed() { return removed; } };
}

test('bridge waits for its frame and accepts only the expected source, origin, channel and request', async () => {
  const f = fixture();
  try {
    let settled = false;
    const result = f.sdk.getSession().then(value => { settled = true; return value; });
    assert.equal(f.requests.length, 0);
    f.load();
    await Promise.resolve();
    const { data, origin } = f.requests[0];
    assert.equal(origin, 'https://api.example.test');
    assert.equal(data.authUrl, authUrl);
    f.reply(data, { origin: 'https://attacker.example' });
    f.reply(data, { source: {} });
    f.reply(data, { data: { type: 'phishlens-auth-result', channel: 'other', id: data.id } });
    f.reply(data, { data: { type: 'phishlens-auth-result', channel: data.channel, id: data.id + 1 } });
    await Promise.resolve();
    assert.equal(settled, false);
    f.reply(data);
    assert.deepEqual(await result, { data: null });
  } finally { f.sdk.dispose(); }
});

test('a frame that loads after timeout never receives the expired password request', async () => {
  const f = fixture(5);
  const result = await f.sdk.signIn.email({ email: 'a@example.test', password: 'Synthetic-password' });
  assert.deepEqual(result, { error: { status: 503 } });
  f.load();
  await Promise.resolve();
  assert.equal(f.requests.length, 0);
  f.sdk.dispose();
});

test('email verification RPCs expose only the fixed verification purpose and code fields', async () => {
  const f = fixture();
  try {
    f.load();
    const sending = f.sdk.emailOtp.sendVerificationOtp({ email: 'a@example.test', type: 'email-verification' });
    await Promise.resolve();
    assert.deepEqual(f.requests[0].data, {
      type: 'phishlens-auth-request', channel: f.requests[0].data.channel,
      id: 1, method: 'resend', input: { email: 'a@example.test' }, authUrl
    });
    f.reply(f.requests[0].data, { data: { type: 'phishlens-auth-result', channel: f.requests[0].data.channel,
      id: f.requests[0].data.id, result: { data: { success: true } } } });
    assert.deepEqual(await sending, { data: { success: true } });

    const verifying = f.sdk.emailOtp.verifyEmail({ email: 'a@example.test', otp: '123456' });
    await Promise.resolve();
    assert.equal(f.requests[1].data.method, 'verifyEmail');
    assert.deepEqual(f.requests[1].data.input, { email: 'a@example.test', code: '123456' });
    f.reply(f.requests[1].data, { data: { type: 'phishlens-auth-result', channel: f.requests[1].data.channel,
      id: f.requests[1].data.id, result: { data: { success: true } } } });
    assert.deepEqual(await verifying, { data: { success: true } });
  } finally { f.sdk.dispose(); }
});

test('closing the page rejects outstanding work and removes the bridge and listeners', async () => {
  const f = fixture();
  const pending = f.sdk.getSession();
  f.events.get('pagehide')();
  assert.deepEqual(await pending, { error: { status: 503 } });
  assert.equal(f.removed, true);
  assert.equal(f.events.size, 0);
  assert.deepEqual(await f.sdk.getSession(), { error: { status: 503 } });
});

test('integration binds the bridge to its API and rejects other paths and origins before initialization', () => {
  const config = { enabled: true, authUrl, database: 'neondb', apiOrigin: 'https://api.example.test',
    transport: 'https-bridge', bridgeUrl };
  const options = { config, apiOrigin: config.apiOrigin,
    hostPermissions: ['https://api.example.test/*', 'https://auth.example.test/*'],
    sdkFactory: () => assert.fail('direct SDK used') };
  let initialized = 0;
  const result = createNeonIntegration({ ...options, bridgeFactory: input => {
    initialized++;
    assert.deepEqual(input, { bridgeUrl, authUrl });
    return {};
  } });
  assert.equal(typeof result.adapter.restore, 'function');
  assert.equal(initialized, 1);
  for (const bridge of ['https://attacker.example/auth/bridge', bridgeUrl + '?url=other',
    bridgeUrl + '/other', 'http://api.example.test/auth/bridge']) {
    assert.throws(() => createNeonIntegration({ ...options, config: { ...config, bridgeUrl: bridge },
      bridgeFactory: () => assert.fail('invalid bridge initialized') }), /bridge configuration/);
  }
});

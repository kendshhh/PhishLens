import test from 'node:test';
import assert from 'node:assert/strict';
import { createNeonBridgeClient } from '../js/neon-bridge-client.js';
import { createNeonIntegration } from '../js/neon-integration.js';

const bridgeUrl = 'https://api.example.test/auth/bridge';
const authUrl = 'https://auth.example.test/neondb/auth';

const bridgePage = () => new Response('<script type="module" src="/auth/bridge/client.js"></script>', {
  headers: { 'content-type': 'text/html' },
});
const settle = () => new Promise(resolve => setImmediate(resolve));

function fixture(options = {}) {
  const events = new Map(), frames = [], requests = [];
  const win = { addEventListener: (name, callback) => events.set(name, callback),
    removeEventListener: name => events.delete(name) };
  const doc = {
    defaultView: win,
    createElement() {
      const handlers = new Map();
      const frame = { setAttribute() {}, addEventListener: (name, callback) => handlers.set(name, callback),
        load() { handlers.get('load')?.(); },
        contentWindow: { postMessage: (data, origin) => requests.push({ data, origin }) },
        remove() { frame.removed = true; } };
      frames.push(frame);
      return frame;
    },
    body: { append(frame) { frame.appended = true; } },
  };
  const sdk = createNeonBridgeClient({ bridgeUrl, authUrl, documentImpl: doc, timeoutMs: 1000,
    fetchImpl: async () => bridgePage(), ...options });
  return { sdk, frames, requests, events, get frame() { return frames.at(-1); },
    async load() { await settle(); assert.ok(frames.at(-1)?.appended); frames.at(-1).load(); await settle(); },
    reply(request, changes = {}) { events.get('message')({ source: frames.at(-1).contentWindow,
      origin: 'https://api.example.test', data: { type: 'phishlens-auth-result',
        channel: request.channel, id: request.id, result: { data: null } }, ...changes }); },
    get removed() { return frames.at(-1)?.removed; } };
}

test('bridge waits for its frame and accepts only the expected source, origin, channel and request', async () => {
  const f = fixture();
  try {
    let settled = false;
    const result = f.sdk.getSession().then(value => { settled = true; return value; });
    assert.equal(f.requests.length, 0);
    await f.load();
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

test('Render warm-up consumes a separate budget, and never receives credentials', async () => {
  let attempts = 0;
  const f = fixture({ timeoutMs: 10, startupMs: 500, retryDelayMs: 15, fetchImpl: async (url, request) => {
    assert.equal(url, bridgeUrl);
    assert.equal(request.credentials, 'omit');
    assert.equal(request.body, undefined);
    assert.equal(request.method, undefined);
    if (++attempts === 1) return new Response('<html>Render loading page</html>', {
      headers: { 'content-type': 'text/html' },
    });
    return bridgePage();
  } });
  try {
    const signIn = f.sdk.signIn.email({ email: 'a@example.test', password: 'Synthetic-password' });
    await new Promise(resolve => setTimeout(resolve, 35));
    assert.equal(attempts, 2);
    assert.equal(f.requests.length, 0);
    await f.load();
    assert.equal(f.requests.length, 1);
    f.reply(f.requests[0].data);
    assert.deepEqual(await signIn, { data: null });
  } finally { f.sdk.dispose(); }
});

test('a frame that loads after startup expires never receives the expired password request', async () => {
  const f = fixture({ startupMs: 10 });
  try {
    const result = await f.sdk.signIn.email({ email: 'a@example.test', password: 'Synthetic-password' });
    assert.deepEqual(result, { error: { status: 503 } });
    f.frame.load();
    await settle();
    assert.equal(f.requests.length, 0);
    assert.equal(f.removed, true);
  } finally { f.sdk.dispose(); }
});

test('a timed-out dispatched request is never replayed; the next action opens a fresh frame', async () => {
  const f = fixture({ timeoutMs: 30 });
  try {
    const original = f.sdk.signIn.email({ email: 'a@example.test', password: 'Synthetic-password' });
    await f.load();
    assert.deepEqual(await original, { error: { status: 503 } });
    assert.equal(f.removed, true);
    const retry = f.sdk.getSession();
    await f.load();
    assert.deepEqual(f.requests.map(entry => entry.data.method), ['signIn', 'getSession']);
    assert.notEqual(f.requests[0].data.channel, f.requests[1].data.channel);
    f.reply(f.requests[1].data);
    assert.deepEqual(await retry, { data: null });
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

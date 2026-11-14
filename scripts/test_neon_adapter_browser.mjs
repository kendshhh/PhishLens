import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { chromium } from 'playwright';

const server = spawn(process.env.PYTHON || 'python3', ['scripts/preview_accounts.py'], {
  env: { ...process.env, ACCOUNT_PREVIEW_PORT: '0' }, stdio: ['ignore', 'pipe', 'pipe']
});
server.stderr.on('data', () => {});
let browser;
try {
  const origin = await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(Error('Local fixture server did not start')), 10000);
    server.once('error', reject);
    server.stdout.on('data', data => {
      const match = String(data).match(/http:\/\/127\.0\.0\.1:\d+/);
      if (match) { clearTimeout(timeout); resolve(match[0]); }
    });
  });
  browser = await chromium.launch({ headless: true, channel: process.env.BROWSER_CHANNEL || 'chrome' });
  const page = await browser.newPage();
  const errors = [], unexpected = [];
  page.on('pageerror', error => errors.push(error.message));
  let active = true, revision = 0;
  const token = () => ['header', Buffer.from(JSON.stringify({ sub: 'sdk-test-user', exp: Math.floor(Date.now() / 1000) + 900, revision })).toString('base64url'), 'signature'].join('.');
  await page.route('**/*', async route => {
    const request = route.request(), url = new URL(request.url());
    if (url.origin === origin) return route.continue();
    if (!['https://auth.example.test', 'https://api.example.test'].includes(url.origin)) {
      unexpected.push(url.origin); return route.abort();
    }
    const headers = { 'access-control-allow-origin': origin, 'access-control-allow-credentials': 'true',
      'access-control-allow-methods': 'GET,POST,OPTIONS', 'access-control-allow-headers': request.headers()['access-control-request-headers'] || 'content-type',
      'access-control-expose-headers': 'set-auth-jwt', 'content-type': 'application/json' };
    if (request.method() === 'OPTIONS') return route.fulfill({ status: 204, headers });
    if (url.origin === 'https://api.example.test') {
      assert.equal(request.headers().authorization, 'Bearer ' + token());
      return route.fulfill({ status: 200, headers, body: JSON.stringify({ items: [] }) });
    }
    if (url.pathname.endsWith('/sign-out')) active = false;
    if (url.pathname.endsWith('/sign-in/email')) { active = true; revision++; }
    const state = { user: { id: 'sdk-test-user', email: 'sdk@example.test', name: 'SDK Test', emailVerified: true },
      session: { token: 'opaque-cookie-value', expiresAt: new Date(Date.now() + 3600000).toISOString() } };
    if (active) headers['set-auth-jwt'] = token();
    const body = url.pathname.endsWith('/get-session') ? (active ? state : null) : state;
    return route.fulfill({ status: 200, headers, body: JSON.stringify(body) });
  });
  await page.goto(origin + '/account-preview');
  const result = await page.evaluate(async () => {
    const { createNeonIntegration } = await import('/extension/js/neon-integration.js');
    const { adapter, createClient } = createNeonIntegration({ apiOrigin: 'https://api.example.test',
      config: { enabled: true, authUrl: 'https://auth.example.test/test/auth', database: 'test', apiOrigin: 'https://api.example.test' },
      hostPermissions: ['https://auth.example.test/*'] });
    const session = await adapter.signIn({ email: 'sdk@example.test', password: 'Synthetic-test-password' });
    await createClient(session).listAnalyses();
    await adapter.resend({ email: 'sdk@example.test' });
    await adapter.verifyEmail({ email: 'sdk@example.test', code: '123456' });
    await adapter.signOut();
    return { signedOut: await adapter.restore() === null,
      localStorageKeys: Object.keys(localStorage), sessionStorageKeys: Object.keys(sessionStorage) };
  });
  assert.equal(result.signedOut, true);
  assert.deepEqual(result.localStorageKeys, []);
  assert.deepEqual(result.sessionStorageKeys, []);
  assert.deepEqual(errors, []);
  assert.deepEqual(unexpected, []);
  console.log(JSON.stringify({ result: 'passed', browser: browser.version(), scope: 'real bundled SDK, intercepted synthetic HTTP only',
    noPersistentSessionStorage: true, unexpectedOrigins: 0, pageErrors: 0 }));
} finally {
  await browser?.close(); server.kill();
  if (server.exitCode === null) await once(server, 'exit');
}

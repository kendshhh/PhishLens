// One-off local browser/database evidence. Auth SDK/provider is a substitute.
// Every external request is intercepted or rejected. Never use hosted targets.
import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { once } from 'node:events';
import { execFileSync } from 'node:child_process';
import { chromium } from './source/node_modules/playwright/index.mjs';
import { createPreviewServer } from './source/scripts/serve_web.mjs';

const source = new URL('./source/', import.meta.url);
const fixture = JSON.parse(await readFile(new URL('./web-fixture.private.json', import.meta.url)));
const expectedModel = 'a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c';
assert.match(fixture.apiOrigin, /^http:\/\/127\.0\.0\.1:\d+$/);
execFileSync(process.execPath, ['scripts/build_web.mjs'], { cwd: source, windowsHide: true,
  env: { ...process.env, PHISHLENS_WEB_ENV: 'development', PHISHLENS_WEB_API_ORIGIN: fixture.apiOrigin,
    PHISHLENS_WEB_AUTH_URL: 'https://auth.example.test/test/auth', PHISHLENS_WEB_BACKEND_SHA: fixture.sourceSha } });
const routing = JSON.parse(await readFile(new URL('./source/web/.build-routing.json', import.meta.url)));
const server = createPreviewServer(routing).listen(0, '127.0.0.1');
await once(server, 'listening');
const base = `http://127.0.0.1:${server.address().port}`;
const evidence = { source_sha: fixture.sourceSha, scope: 'Loopback web + real FastAPI/TF-IDF/PostgreSQL; substituted Auth SDK/provider/key retrieval. No hosted Auth, cookie, OTP or Vercel acceptance.',
  tests: [], network: [], blocked_external_requests: [], result: 'failed' };
let browser;
async function check(name, action) { await action(); evidence.tests.push({ name, result: 'passed' }); }
async function eventually(action) {
  let failure;
  for (let i = 0; i < 60; i++) { try { return await action(); } catch (error) { failure = error; await new Promise(r => setTimeout(r, 100)); } }
  throw failure;
}
try {
  browser = await chromium.launch({ channel: 'msedge', headless: true });
  evidence.browser = browser.version();
  const contexts = [];
  for (const identity of fixture.identities) {
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    let providerSession = null, failedLogout = false;
    const sdkStub = `export const BetterAuthVanillaAdapter = value => value;
      export function createAuthClient() {
        const call = (path, body) => fetch('https://auth.example.test/test/auth/local-test/' + path,
          {method: 'POST', credentials: 'include', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body || {})}).then(r => r.json());
        return { getSession: () => call('session'), signIn: {email: body => call('signin', body)}, signOut: () => call('signout') };
      }`;
    await context.route('**/*', async route => {
      const url = new URL(route.request().url());
      if (url.origin === base && url.pathname === '/vendor/neon/sdk.mjs') {
        return route.fulfill({ contentType: 'text/javascript', body: sdkStub });
      }
      if (url.origin === 'https://auth.example.test') {
        const path = url.pathname.split('/').at(-1);
        const headers = { 'Access-Control-Allow-Origin': base, 'Access-Control-Allow-Credentials': 'true',
          'Access-Control-Allow-Headers': 'content-type', 'Access-Control-Allow-Methods': 'POST, OPTIONS' };
        if (route.request().method() === 'OPTIONS') return route.fulfill({ status: 204, headers });
        let data = null, error;
        if (path === 'signin') {
          const input = route.request().postDataJSON();
          assert.equal(input.email, identity.email);
          providerSession = { user: { id: identity.sub, email: identity.email, name: identity.name, emailVerified: true },
            session: { expiresAt: fixture.expiresAt, token: identity.token } };
          data = {};
        } else if (path === 'session') data = providerSession;
        else if (path === 'signout') {
          if (failedLogout) error = { status: 503 }; else providerSession = null;
        } else throw Error('Unexpected test Auth action');
        return route.fulfill({ headers, contentType: 'application/json', body: JSON.stringify({ data, error }) });
      }
      if (url.origin === base) return route.continue();
      evidence.blocked_external_requests.push(url.origin + url.pathname);
      return route.abort();
    });
    const page = await context.newPage();
    page.on('response', response => {
      if (new URL(response.url()).pathname.startsWith('/api/')) evidence.network.push({ method: response.request().method(), path: new URL(response.url()).pathname, status: response.status() });
    });
    await page.goto(base);
    if (contexts.length === 0) await check('real browser local scan stays local and survives tab reload as Uncertain', async () => {
      const posts = () => evidence.network.filter(r => r.method === 'POST').length;
      const before = posts();
      await page.locator('#scan-body').fill('Subject: Account verification\nYour account will be suspended. Verify your password at https://example.test/login');
      await page.locator('#scan-button').click();
      await page.locator('#classification').waitFor({ state: 'visible' });
      assert.match(await page.locator('#classification').innerText(), /Uncertain/i);
      assert.equal(posts(), before);
      await page.reload();
      await page.locator('#classification').waitFor({ state: 'visible' });
      assert.match(await page.locator('#classification').innerText(), /Uncertain/i);
      assert.match(await page.locator('#scan-body').inputValue(), /Account verification/);
    });
    await page.locator('#show-account').click();
    await page.locator('#account-email').fill(identity.email);
    await page.locator('#account-password').fill('Synthetic-local-test-password');
    await page.locator('#account-sign-in button[type=submit]').click();
    await eventually(async () => assert.equal(await page.locator('#account-identity').innerText(), identity.name));
    await page.locator('#close-account').click();
    contexts.push({ context, page, identity, failLogout: () => { failedLogout = true; } });
  }
  const [a, b] = contexts;
  const records = [];
  const body = 'Subject: Account verification\nYour account will be suspended. Verify your password immediately at https://account-check.example.test/login';
  for (const { page, identity } of contexts) {
    await check(identity.name + ': server TF-IDF save and provenance', async () => {
      await page.locator('#show-reports').click();
      await page.locator('#server-create summary').click();
      await page.locator('#create-subject').fill(identity.name + ' synthetic report');
      await page.locator('#create-body').fill(body);
      const created = page.waitForResponse(r => new URL(r.url()).pathname === '/api/analyses' && r.request().method() === 'POST');
      await page.locator('#create-button').click();
      const response = await created;
      const report = await response.json();
      assert.equal(response.status(), 201, JSON.stringify(report));
      assert.equal(report.analysis_provenance.provider_mode, 'tfidf');
      assert.equal(report.analysis_provenance.model_revision, expectedModel);
      assert.equal(report.body, body);
      records.push(report);
      await page.getByText('About this result', { exact: true }).click();
      await eventually(async () => assert.match(await page.locator('#detail-content').innerText(), /TF-IDF/i));
    });
  }
  const api = (who, id, method = 'GET', data) => who.page.evaluate(async ({ id, method, data, token }) => {
    const response = await fetch('/api/analyses' + (id ? '/' + id : ''), { method,
      credentials: 'omit', headers: { Authorization: 'Bearer ' + token, 'X-Require-Auth-Mode': 'neon',
        ...(data ? { 'Content-Type': 'application/json' } : {}) }, body: data ? JSON.stringify(data) : undefined });
    return { status: response.status, data: response.status === 204 ? null : await response.json() };
  }, { id, method, data, token: who.identity.token });
  await check('two-account list/detail/PATCH/DELETE isolation against PostgreSQL', async () => {
    for (const [who, own, foreign] of [[a, records[0], records[1]], [b, records[1], records[0]]]) {
      assert.deepEqual((await api(who)).data.items.map(r => r.id), [own.id]);
      for (const method of ['GET', 'PATCH', 'DELETE']) assert.equal((await api(who, foreign.id, method,
        method === 'PATCH' ? { notes: 'forbidden' } : undefined)).status, 404);
    }
  });
  await check('notes persist after a fresh page and same-account read', async () => {
    await a.page.getByRole('button', { name: 'Edit notes', exact: true }).click();
    await a.page.locator('#edit-notes').fill('Verified synthetic follow-up');
    await a.page.locator('#save-edit').click();
    await eventually(async () => assert.equal((await api(a, records[0].id)).data.notes, 'Verified synthetic follow-up'));
    await a.page.reload();
    await eventually(async () => assert.equal(await a.page.locator('#account-identity').innerText(), a.identity.name));
    await a.page.locator('#show-reports').click();
    await eventually(async () => assert.match(await a.page.locator('#history-list').innerText(), /synthetic report/));
    assert.equal((await api(a, records[0].id)).data.notes, 'Verified synthetic follow-up');
    await a.page.screenshot({ path: new URL('./web-persistence.png', import.meta.url).pathname.replace(/^\/(\w:)/, '$1'), fullPage: true });
  });
  await check('provider failure cannot restore a signed-out account after reload', async () => {
    a.failLogout();
    await a.page.locator('#show-account').click();
    await a.page.locator('#account-sign-out').click();
    await eventually(async () => assert.equal(await a.page.locator('#account-identity').innerText(), 'Keep scanning without an account'));
    await a.page.reload();
    await eventually(async () => assert.equal(await a.page.locator('#account-identity').innerText(), 'Keep scanning without an account'));
    assert.equal(await a.page.locator('#personal-reports').isVisible(), false);
  });
  await check('record cleanup and final 404s', async () => {
    for (const [index, who] of contexts.entries()) {
      assert.equal((await api(who, records[index].id, 'DELETE')).status, 204);
      assert.equal((await api(who, records[index].id)).status, 404);
      assert.deepEqual((await api(who)).data.items, []);
    }
  });
  await check('phone layout and visible keyboard focus', async () => {
    await b.page.setViewportSize({ width: 390, height: 844 });
    await b.page.locator('#show-check').click();
    assert.equal(await b.page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await b.page.locator('#scan-body').focus();
    await b.page.keyboard.press('Tab');
    assert.equal(await b.page.evaluate(() => document.activeElement.id), 'scan-button');
    assert.equal(await b.page.locator('#scan-button').evaluate(el => getComputedStyle(el).outlineStyle !== 'none'), true);
  });
  assert.deepEqual(evidence.blocked_external_requests, []);
  evidence.result = 'passed';
} finally {
  await browser?.close();
  server.closeAllConnections(); server.close();
  await writeFile(new URL('./web-browser-result.json', import.meta.url), JSON.stringify(evidence, null, 2) + '\n');
}
console.log(JSON.stringify({ result: evidence.result, checks: evidence.tests.length, browser: evidence.browser }));

// Installed Chrome -> HTTPS bridge -> bundled Neon SDK -> synthetic Auth,
// then signed JWT -> real FastAPI -> disposable local PostgreSQL.
import assert from 'node:assert/strict';
import { createHash, generateKeyPairSync, randomUUID, sign } from 'node:crypto';
import { execFileSync, spawn } from 'node:child_process';
import { once } from 'node:events';
import { request as httpRequest } from 'node:http';
import { cp, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { chromium } from 'playwright';

const database = process.env.PHISHLENS_AUTH_TEST_DATABASE_URL;
const databaseUrl = new URL(database || 'https://invalid');
assert.ok(['postgresql:', 'postgres:'].includes(databaseUrl.protocol) &&
  ['127.0.0.1', 'localhost'].includes(databaseUrl.hostname) &&
  /^\/phishlens_auth_test_[a-z0-9_]+$/.test(databaseUrl.pathname),
'Set PHISHLENS_AUTH_TEST_DATABASE_URL to a disposable local phishlens_auth_test_* database');
const python = process.env.PHISHLENS_PYTHON || 'python3';
let apiOrigin = 'https://bridge-api.example.test';
let authOrigin = 'https://bridge-auth.example.test';
let authUrl = authOrigin + '/neondb/auth';
const archive = process.env.PHISHLENS_AUTH_TEST_ARCHIVE;
let archiveHash, sourceCommit;
const { privateKey, publicKey } = generateKeyPairSync('ed25519');
const publicJwk = publicKey.export({ format: 'jwk' });
const temporary = await mkdtemp(path.join(os.tmpdir(), 'phishlens-auth-bridge-'));
const checks = [];
const runId = randomUUID();
let context, server, page;
try {
  const extension = path.join(temporary, 'extension');
  if (archive) {
    execFileSync(python, ['-c', `
from pathlib import Path
from zipfile import ZipFile
import sys
target = Path(sys.argv[2]).resolve()
with ZipFile(sys.argv[1]) as package:
    for name in package.namelist():
        if not (target / name).resolve().is_relative_to(target):
            raise ValueError("Archive path escapes test profile")
    package.extractall(target)
`, archive, extension]);
    const configSource = await readFile(path.join(extension, 'js/auth-config.js'), 'utf8');
    const config = configSource.startsWith('export const AUTH_CONFIGS = Object.freeze(')
      ? JSON.parse(configSource.split('\n')[0].slice('export const AUTH_CONFIGS = Object.freeze('.length, -2)).staging
      : JSON.parse(configSource.replace(/^export const AUTH_CONFIG = /, '').replace(/;\s*$/, ''));
    assert.equal(config.transport, 'https-bridge');
    apiOrigin = config.apiOrigin;
    assert.equal(apiOrigin, 'https://phishlens-staging.onrender.com');
    assert.equal(config.bridgeUrl, apiOrigin + '/auth/bridge');
    authUrl = config.authUrl;
    authOrigin = new URL(authUrl).origin;
    archiveHash = createHash('sha256').update(await readFile(archive)).digest('hex');
    sourceCommit = JSON.parse(await readFile(path.join(extension, 'phishlens-build-evidence.json'), 'utf8')).source_commit;
  } else {
    await cp('extension', extension, { recursive: true, filter: source =>
    !source.includes('/model-assets') && !source.includes('/tests') });
  const manifest = JSON.parse(await readFile(path.join(extension, 'manifest.json'), 'utf8'));
  manifest.host_permissions = [apiOrigin + '/*', authOrigin + '/*'];
  await writeFile(path.join(extension, 'manifest.json'), JSON.stringify(manifest));
  await writeFile(path.join(extension, 'js/config.js'), `export const API_BASE_URL = ${JSON.stringify(apiOrigin)};\nexport const API_BASE_URLS = { production: ${JSON.stringify(apiOrigin)}, staging: ${JSON.stringify(apiOrigin)} };\n`);
  const syntheticAuthConfig = {
    enabled: true, authUrl, database: 'neondb', apiOrigin, transport: 'https-bridge',
    bridgeUrl: apiOrigin + '/auth/bridge'
  };
  await writeFile(path.join(extension, 'js/auth-config.js'),
    'export const AUTH_CONFIGS = Object.freeze({ production: ' + JSON.stringify(syntheticAuthConfig) +
    ', staging: ' + JSON.stringify(syntheticAuthConfig) + ' });\n' +
    'export const AUTH_CONFIG = AUTH_CONFIGS.production;\n');
  }
  // Supply only a generated test public key. Real JWT parsing, claims, owner
  // mapping, inference and SQL persistence all use the product implementation.
  const serverSource = `
import json, os
from types import SimpleNamespace
import jwt, uvicorn
from backend.app import auth
from backend.app.main import app
key = jwt.PyJWK.from_dict(json.loads(os.environ["TEST_PUBLIC_JWK"]))
auth.jwks_client = lambda base: SimpleNamespace(get_signing_key_from_jwt=lambda token: key)
uvicorn.run(app, host="127.0.0.1", port=0, log_level="info")
`;
  server = spawn(python, ['-c', serverSource], { env: {
    ...process.env, DATABASE_URL: database, REPORT_AUTH_MODE: 'neon', AI_MODE: 'tfidf',
    NEON_AUTH_BASE_URL: authUrl, AUTH_BRIDGE_ORIGIN: apiOrigin, TEST_PUBLIC_JWK: JSON.stringify(publicJwk)
  }, stdio: ['ignore', 'pipe', 'pipe'] });
  const localOrigin = await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(Error('Local backend did not start')), 15000);
    server.once('error', error => { clearTimeout(timer); reject(error); });
    server.once('exit', () => { clearTimeout(timer); reject(Error('Local backend exited before startup')); });
    server.stderr.on('data', data => {
      const match = String(data).match(/http:\/\/127\.0\.0\.1:\d+/);
      if (match) { clearTimeout(timer); resolve(match[0]); }
    });
  });
  context = await chromium.launchPersistentContext(path.join(temporary, 'profile'), {
    executablePath: process.env.PHISHLENS_CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: true, ignoreDefaultArgs: ['--disable-extensions'],
    args: ['--enable-unsafe-extension-debugging', '--disable-background-networking', '--no-first-run']
  });
  const cdp = await context.browser().newBrowserCDPSession();
  const { id } = await cdp.send('Extensions.loadUnpacked', { path: extension });
  assert.equal(id, 'ceneonaedddlkdocdapimkfggbjcchlb');
  const users = new Map();
  let failLogout = false;
  let authRequests = 0, apiRequests = 0;
  const apiStatuses = [];
  const unknownOrigins = [], pageErrors = [];
  function token(user) {
    const now = Math.floor(Date.now() / 1000);
    const header = Buffer.from(JSON.stringify({ alg: 'EdDSA', typ: 'JWT', kid: 'local-test' })).toString('base64url');
    const payload = Buffer.from(JSON.stringify({ sub: user.id, email: user.email, name: user.name,
      emailVerified: user.emailVerified, banned: false, iat: now, exp: now + 900,
      iss: authOrigin, aud: authOrigin })).toString('base64url');
    const unsigned = header + '.' + payload;
    return unsigned + '.' + sign(null, Buffer.from(unsigned), privateKey).toString('base64url');
  }
  await context.route(/^https?:\/\//, async route => {
    const request = route.request(), url = new URL(request.url());
    if (url.origin === apiOrigin) {
      apiRequests++;
      const response = await new Promise((resolve, reject) => {
        const forwarded = httpRequest(localOrigin + url.pathname + url.search, {
          method: request.method(), headers: { ...request.headers(), host: new URL(apiOrigin).host,
            'x-forwarded-proto': 'https' }
        }, incoming => {
          const chunks = [];
          incoming.on('data', chunk => chunks.push(chunk));
          incoming.on('end', () => resolve({ status: incoming.statusCode, headers: incoming.headers,
            body: Buffer.concat(chunks) }));
        });
        forwarded.on('error', reject);
        forwarded.end(request.postDataBuffer());
      });
      if (url.pathname.startsWith('/api/')) apiStatuses.push({ method: request.method(), status: response.status });
      return route.fulfill(response);
    }
    if (url.origin !== authOrigin) { unknownOrigins.push(url.origin); return route.abort(); }
    authRequests++;
    // This assertion catches any regression back to chrome-extension:// Origin.
    assert.equal(request.headers().origin, apiOrigin);
    const headers = { 'access-control-allow-origin': apiOrigin, 'access-control-allow-credentials': 'true',
      'access-control-allow-methods': 'GET,POST,OPTIONS', 'access-control-allow-headers':
        request.headers()['access-control-request-headers'] || 'content-type',
      'access-control-expose-headers': 'set-auth-jwt', 'content-type': 'application/json' };
    if (request.method() === 'OPTIONS') return route.fulfill({ status: 204, headers });
    const input = request.postData() ? request.postDataJSON() : {};
    const currentId = request.headers().cookie?.match(/fixture-session=([^;]+)/)?.[1];
    const current = [...users.values()].find(user => user.id === currentId);
    const error = (status, code) => route.fulfill({ status, headers, body: JSON.stringify({ code,
      message: 'PRIVATE PROVIDER DETAIL must never reach the UI' }) });
    const session = user => ({ user: { ...user, password: undefined }, session: {
      token: 'opaque-cookie-secret', expiresAt: new Date(Date.now() + 3600000).toISOString() } });
    const setCookie = user => { headers['set-cookie'] = 'fixture-session=' + user.id +
      '; Path=/neondb/auth; Secure; HttpOnly; SameSite=None; Partitioned; Max-Age=3600'; };
    let data = { success: true };
    const method = url.pathname.slice('/neondb/auth/'.length);
    if (method === 'sign-up/email') {
      if (users.has(input.email)) return error(422, 'USER_ALREADY_EXISTS_USE_ANOTHER_EMAIL');
      const user = { id: runId + '-' + (users.size + 1), email: input.email,
        name: input.name, password: input.password, emailVerified: false };
      users.set(input.email, user);
      setCookie(user);
    } else if (method === 'sign-in/email') {
      const user = users.get(input.email);
      if (!user || user.password !== input.password) return error(401, 'INVALID_EMAIL_OR_PASSWORD');
      setCookie(user);
    } else if (method === 'get-session') {
      data = current ? session(current) : null;
      if (current) headers['set-auth-jwt'] = token(current);
    } else if (method === 'sign-out') {
      if (failLogout) return error(503, 'SERVICE_UNAVAILABLE');
      headers['set-cookie'] = 'fixture-session=; Max-Age=0; Path=/neondb/auth; Secure; HttpOnly; SameSite=None; Partitioned';
    } else if (method === 'email-otp/reset-password') {
      const user = users.get(input.email);
      if (!user || input.otp !== '123456') return error(400, 'INVALID_OTP');
      user.password = input.password;
    } else if (method !== 'forget-password/email-otp') {
      assert.fail('Unexpected Auth SDK endpoint ' + method);
    }
    return route.fulfill({ status: 200, headers, body: JSON.stringify(data) });
  });
  page = await context.newPage();
  page.on('requestfailed', request => console.error('Failed request:', new URL(request.url()).pathname, request.failure()?.errorText));
  page.on('pageerror', error => pageErrors.push(error.message));
  const popupUrl = `chrome-extension://${id}/popup.html?environment=staging`;
  await page.goto(popupUrl);
  await page.locator('#show-account').waitFor({ state: 'visible' });
  await page.locator('#show-account').click();
  try { await page.locator('#account-panel').waitFor({ state: 'visible', timeout: 5000 }); }
  catch (error) {
    console.error({ accountStatus: await page.locator('#account-status').innerText(), pageErrors,
      popupUrl: page.url(), panelClass: await page.locator('#account-panel').getAttribute('class') });
    throw error;
  }
  await page.locator('#account-sign-in').waitFor({ state: 'visible' });
  const emailA = `bridge-a-${runId}@example.test`, emailB = `bridge-b-${runId}@example.test`;
  const password = 'Synthetic-password-123';
  async function register(email) {
    await page.locator('#account-panel').waitFor({ state: 'visible' });
    await page.locator('#account-sign-in').waitFor({ state: 'visible' });
    await page.locator('#open-sign-up').click();
    await page.locator('#signup-name').fill('Synthetic account');
    await page.locator('#signup-email').fill(email);
    await page.locator('#signup-password').fill(password);
    await page.locator('#account-sign-up button[type=submit]').click();
    await page.locator('#account-sign-out').waitFor({ state: 'visible', timeout: 15000 });
  }
  async function signIn(email, secret = password) {
    await page.locator('#account-email').fill(email);
    await page.locator('#account-password').fill(secret);
    await page.locator('#account-sign-in button[type=submit]').click();
  }
  await register(emailA);
  await page.locator('#account-sign-out').click();
  await page.locator('#account-sign-in').waitFor({ state: 'visible' });
  await signIn(emailA, 'Wrong-password');
  await page.getByText('Email or password was not accepted. Sign in again.', { exact: true }).waitFor();
  await signIn(emailA);
  await page.locator('#account-sign-out').waitFor({ state: 'visible' });
  checks.push('unverified signup and password sign-in succeed without an email code');
  const beforeProtocolChecks = authRequests;
  const protocol = await page.evaluate(async ({ apiOrigin, authUrl }) => {
    const frame = document.createElement('iframe');
    frame.hidden = true;
    const loaded = new Promise(resolve => frame.addEventListener('load', resolve, { once: true }));
    frame.src = apiOrigin + '/auth/bridge';
    document.body.append(frame);
    await loaded;
    const channel = crypto.randomUUID();
    async function attempt(id, method, input) {
      return new Promise(resolve => {
        const listen = event => {
          if (event.source === frame.contentWindow && event.origin === apiOrigin &&
              event.data?.channel === channel && event.data.id === id) {
            globalThis.removeEventListener('message', listen);
            resolve(event.data.result.error.status);
          }
        };
        globalThis.addEventListener('message', listen);
        frame.contentWindow.postMessage({ type: 'phishlens-auth-request', id, channel, method, input, authUrl }, apiOrigin);
      });
    }
    const results = [await attempt(1, '$fetch', { url: 'https://attacker.example.test' }),
      await attempt(2, 'getSession', { arbitrary: 'not allowed' }),
      await attempt(3, 'verifyEmail', { email: 'a@example.test', otp: '123456' }),
      await attempt(4, 'resend', { email: 'a@example.test', type: 'email-verification' })];
    frame.remove();
    return results;
  }, { apiOrigin, authUrl });
  assert.deepEqual(protocol, [400, 400, 400, 400]);
  assert.equal(authRequests, beforeProtocolChecks);
  checks.push('bridge rejects arbitrary SDK calls, extra fields and removed signup-verification OTP operations');
  await page.reload();
  await page.locator('#show-account').click();
  await page.locator('#account-sign-out').waitFor({ state: 'visible' });
  checks.push('wrong password sanitized; cookie session restored after popup reload');
  await page.locator('#close-account').click();
  await page.locator('#paste-panel > summary').click();
  await page.locator('#scan-body').fill('Synthetic pasted email. Please review the meeting agenda.');
  await page.locator('#scan-button').click();
  await page.locator('#result-state').waitFor({ state: 'visible', timeout: 30000 });
  await page.locator('#report-subject').fill('Saved from the actual Save report button');
  await page.locator('#save-consent').check();
  await page.locator('#save-report').click();
  await page.locator('#view-saved-report').waitFor({ state: 'visible', timeout: 30000 });
  await page.locator('#view-saved-report').click();
  await page.locator('#detail-panel').waitFor({ state: 'visible' });
  await page.locator('#detail-content details').first().locator('summary').click();
  assert.match(await page.locator('#detail-content').innerText(), /Synthetic pasted email/);
  await page.locator('#detail-content').getByRole('button', { name: 'Edit notes', exact: true }).click();
  await page.locator('#edit-notes').fill('Synthetic note persisted through the HTTPS Auth bridge.');
  await page.locator('#save-edit').click();
  await page.getByText('Synthetic note persisted through the HTTPS Auth bridge.', { exact: true }).waitFor();
  await page.locator('#detail-content').getByRole('button', { name: 'Delete report', exact: true }).click();
  await page.locator('#confirm-delete').click();
  await page.locator('#detail-panel').waitFor({ state: 'hidden' });
  checks.push('actual Save report, detail, edit and deletion persisted through FastAPI to PostgreSQL');
  await page.locator('#show-reports').click();
  await page.locator('#server-create').evaluate(element => { element.open = true; });
  await page.locator('#create-subject').fill('Bridge synthetic report');
  await page.locator('#create-body').fill('Please review the synthetic meeting agenda for tomorrow.');
  await page.locator('#create-button').click();
  await page.locator('#detail-panel').waitFor({ state: 'visible', timeout: 30000 });
  const reportId = await page.evaluate(async ({ apiOrigin }) => {
    const { createNeonIntegration } = await import('./js/neon-integration.js');
    const { AUTH_CONFIG, AUTH_CONFIGS } = await import('./js/auth-config.js');
    const integration = createNeonIntegration({ config: AUTH_CONFIGS?.staging ?? AUTH_CONFIG, apiOrigin });
    const session = await integration.adapter.restore();
    const reports = await integration.createClient(session).listAnalyses();
    return reports[0].id;
  }, { apiOrigin });
  checks.push('actual extension Analyze and save reached signed-JWT backend and local PostgreSQL');
  await page.locator('#show-account').click();
  await page.locator('#account-sign-out').click();
  await page.locator('#account-sign-in').waitFor({ state: 'visible' });
  await register(emailB);
  await page.locator('#account-sign-out').click();
  await page.locator('#account-sign-in').waitFor({ state: 'visible' });
  await signIn(emailB);
  await page.locator('#account-sign-out').waitFor({ state: 'visible' });
  const isolation = await page.evaluate(async ({ apiOrigin, reportId }) => {
    const { createNeonIntegration } = await import('./js/neon-integration.js');
    const { AUTH_CONFIG, AUTH_CONFIGS } = await import('./js/auth-config.js');
    const integration = createNeonIntegration({ config: AUTH_CONFIGS?.staging ?? AUTH_CONFIG, apiOrigin });
    const session = await integration.adapter.restore();
    const client = integration.createClient(session);
    const statuses = [];
    for (const action of [() => client.getAnalysis(reportId), () => client.updateAnalysis(reportId, { notes: 'denied' }),
      () => client.deleteAnalysis(reportId)]) {
      try { await action(); statuses.push(200); } catch (error) { statuses.push(error.status); }
    }
    return { count: (await client.listAnalyses()).length, statuses };
  }, { apiOrigin, reportId });
  assert.deepEqual(isolation, { count: 0, statuses: [404, 404, 404] });
  checks.push('second account cannot list, read, edit or delete first account report');
  failLogout = true;
  await page.locator('#account-sign-out').click();
  await page.getByText(/could not confirm sign-out/).waitFor();
  await page.reload();
  await page.locator('#show-account').click();
  await page.locator('#account-sign-in').waitFor({ state: 'visible' });
  failLogout = false;
  await signIn(emailA);
  await page.locator('#account-sign-out').waitFor({ state: 'visible' });
  checks.push('failed remote logout stays signed out after reload until explicit sign-in');
  await page.locator('#account-sign-out').click();
  await page.locator('#account-sign-in').waitFor({ state: 'visible' });
  await page.locator('#open-sign-up').click();
  await page.locator('#signup-name').fill('Duplicate synthetic');
  await page.locator('#signup-email').fill(emailA);
  await page.locator('#signup-password').fill(password);
  await page.locator('#account-sign-up button[type=submit]').click();
  await page.getByText(/Try signing in instead/).waitFor();
  await page.locator('#open-sign-in').click();
  await page.locator('#open-recover').click();
  await page.locator('#recovery-email').fill(emailA);
  await page.locator('#account-recover button[type=submit]').click();
  await page.locator('#account-reset').waitFor({ state: 'visible' });
  await page.locator('#reset-code').fill('123456');
  await page.locator('#reset-password').fill('Updated-synthetic-password');
  await page.locator('#account-reset button[type=submit]').click();
  await page.locator('#account-sign-in').waitFor({ state: 'visible' });
  await signIn(emailA, 'Updated-synthetic-password');
  await page.locator('#account-sign-out').waitFor({ state: 'visible' });
  checks.push('duplicate signup sanitized; password recovery and reset require renewed sign-in');
  assert.equal((await page.locator('body').innerText()).includes('PRIVATE PROVIDER DETAIL'), false);
  assert.deepEqual(await page.evaluate(() => [...Object.keys(localStorage), ...Object.keys(sessionStorage)]), []);
  for (const frame of page.frames().filter(frame => frame.url().startsWith(apiOrigin + '/auth/bridge'))) {
    assert.deepEqual(await frame.evaluate(() => [...Object.keys(localStorage), ...Object.keys(sessionStorage)]), []);
  }
  assert.deepEqual(unknownOrigins, []);
  assert.deepEqual(pageErrors, []);
  assert.ok(apiStatuses.some(entry => entry.method === 'POST' && entry.status === 201));
  console.log(JSON.stringify({ result: 'passed', browser: context.browser().version(),
    source_commit: sourceCommit, archive_sha256: archiveHash,
    scope: 'installed extension, bundled SDK and synthetic Auth; real FastAPI/TF-IDF and disposable local PostgreSQL',
    checks, authRequests, apiRequests, unknownOrigins: 0, pageErrors: 0, noPersistentBrowserTokens: true }, null, 2));
} catch (error) {
  if (page) console.error({ accountStatus: await page.locator('#account-status').innerText(), checks });
  throw error;
} finally {
  await context?.close();
  if (server && server.exitCode === null) { server.kill(); await once(server, 'exit'); }
  await rm(temporary, { recursive: true, force: true });
}

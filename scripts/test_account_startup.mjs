import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, writeFile } from 'node:fs/promises';
import { chromium } from 'playwright';

const server = spawn(process.env.PYTHON || (process.platform === 'win32' ? 'py' : 'python3'),
  ['scripts/preview_accounts.py'], {
    env: { ...process.env, ACCOUNT_PREVIEW_PORT: '0' }, stdio: ['ignore', 'pipe', 'pipe']
  });
let browser;
try {
  const origin = await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(Error('Local fixture server did not start')), 10000);
    server.once('error', error => { clearTimeout(timer); reject(error); });
    server.once('exit', code => { clearTimeout(timer); reject(Error(`Fixture server exited: ${code}`)); });
    server.stdout.on('data', data => {
      const match = String(data).match(/http:\/\/127\.0\.0\.1:\d+/);
      if (match) { clearTimeout(timer); resolve(match[0]); }
    });
  });
  browser = await chromium.launch({ headless: true,
    ...(process.env.BROWSER_CHANNEL ? { channel: process.env.BROWSER_CHANNEL } : {}) });
  const results = [];
  for (const scenario of ['disabled', 'invalid-url', 'missing-permission', 'wrong-api', 'sdk-failure']) {
    const context = await browser.newContext({ viewport: { width: 380, height: 600 } });
    const page = await context.newPage();
    page.setDefaultTimeout(5000);
    const errors = [], external = [];
    page.on('pageerror', error => errors.push(error.message));
    const config = scenario === 'disabled' ? null : {
      enabled: true, authUrl: scenario === 'invalid-url' ? 'not a URL' : 'https://auth.example.test/test/auth',
      database: 'test', apiOrigin: scenario === 'wrong-api' ? 'https://wrong.example.test' : 'https://api.example.test'
    };
    await page.route('**/*', async route => {
      const url = new URL(route.request().url());
      if (url.origin !== origin) { external.push(url.origin); return route.abort(); }
      if (url.pathname === '/extension/js/auth-config.js') {
        return route.fulfill({ contentType: 'text/javascript', body: `export const AUTH_CONFIG = ${JSON.stringify(config)};` });
      }
      if (url.pathname === '/extension/js/config.js') {
        return route.fulfill({ contentType: 'text/javascript', body: 'export const API_BASE_URL = "https://api.example.test";' });
      }
      if (scenario === 'sdk-failure' && url.pathname === '/extension/vendor/neon/sdk.mjs') {
        return route.fulfill({ contentType: 'text/javascript', body:
          'export function createAuthClient() { throw Error("private SDK diagnostic"); } export function BetterAuthVanillaAdapter() { return {}; }' });
      }
      return route.continue();
    });
    await page.addInitScript(({ scenario }) => {
      const values = {};
      globalThis.scanRequests = [];
      globalThis.chrome = {
        runtime: {
          getManifest: () => ({ host_permissions: scenario === 'missing-permission' ? [] : ['https://auth.example.test/*'] }),
          async sendMessage(request) {
            globalThis.scanRequests.push(request);
            return { ok: false, error: 'Synthetic scanner unavailable' };
          }
        },
        storage: {
          session: {
            async get(key) { return { [key]: values[key] }; },
            async set(items) { Object.assign(values, items); },
            async remove(key) { delete values[key]; }
          },
          onChanged: { addListener() {} }
        }
      };
    }, { scenario });
    await page.goto(origin + '/extension/popup.html');
    await page.getByRole('heading', { name: 'Highlight. Right-click. Check.', exact: true }).waitFor();
    if (scenario !== 'disabled') {
      await page.locator('#show-account').click();
      await page.getByText('Accounts are unavailable in this build. Local scanning is still available.', { exact: true }).waitFor();
      await page.locator('#close-account').click();
    }
    await page.getByRole('button', { name: 'Saved reports', exact: true }).click();
    await page.locator('#reports-account-gate').waitFor({ state: 'visible' });
    assert.equal(await page.locator('#personal-reports').isVisible(), false);
    await page.getByRole('button', { name: 'Check email', exact: true }).click();
    await page.getByText('Or paste email text', { exact: true }).click();
    await page.locator('#scan-body').fill('Synthetic meeting reminder only.');
    await page.getByRole('button', { name: 'Check this email', exact: true }).click();
    assert.deepEqual(await page.evaluate(() => scanRequests.filter(r => r.type === 'phishlens-analyze-text')),
      [{ type: 'phishlens-analyze-text', text: 'Synthetic meeting reminder only.' }]);
    assert.equal(await page.locator('#scan-body').inputValue(), 'Synthetic meeting reminder only.');
    assert.deepEqual(errors, []);
    assert.deepEqual(external, []);
    if (scenario === 'sdk-failure') {
      assert.doesNotMatch(await page.locator('body').innerText(), /private SDK diagnostic/);
      await mkdir('output/account-startup', { recursive: true });
      await page.screenshot({ path: 'output/account-startup/unavailable.png', fullPage: true });
    }
    results.push({ scenario, localScanDispatched: true, reportsGated: true, pageErrors: 0, externalRequests: 0 });
    await context.close();
  }
  await mkdir('output/account-startup', { recursive: true });
  const evidence = { scope: 'local browser with synthetic Chrome and SDK boundaries; no live Auth or backend',
    browser: browser.version(), results };
  await writeFile('output/account-startup/results.json', JSON.stringify(evidence, null, 2) + '\n');
  console.log(JSON.stringify(evidence));
} finally {
  await browser?.close();
  server.kill();
  if (server.exitCode === null) await once(server, 'exit');
}

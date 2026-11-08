import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import { once } from 'node:events';
import { chromium } from 'playwright';

const python = process.env.PYTHON || (process.platform === 'win32' ? 'py' : 'python3');
const server = spawn(python, ['scripts/preview_accounts.py'], { env: { ...process.env, ACCOUNT_PREVIEW_PORT: '0' }, stdio: ['ignore', 'pipe', 'pipe'] });
let browser;
const errors = [], externalRequests = [], checks = [];
try {
  const origin = await new Promise((resolve, reject) => {
    const deadline = setTimeout(() => reject(new Error('Preview server did not start')), 10000);
    server.once('error', error => { clearTimeout(deadline); reject(error); });
    server.once('exit', code => { clearTimeout(deadline); reject(new Error(`Preview exited: ${code}`)); });
    server.stdout.on('data', chunk => {
      const match = chunk.toString().match(/http:\/\/127\.0\.0\.1:\d+\/account-preview/);
      if (match) { clearTimeout(deadline); resolve(match[0]); }
    });
    server.stderr.on('data', chunk => process.stderr.write(chunk));
  });
  browser = await chromium.launch({ headless: true, ...(process.env.BROWSER_CHANNEL ? { channel: process.env.BROWSER_CHANNEL } : {}) });
  const context = await browser.newContext({ viewport: { width: 380, height: 680 } });
  await context.route('**/*', route => {
    if (new URL(route.request().url()).origin === new URL(origin).origin) return route.continue();
    externalRequests.push(route.request().url()); return route.abort();
  });
  const page = await context.newPage();
  page.setDefaultTimeout(5000);
  page.on('pageerror', error => errors.push(error.message));
  await mkdir('output/account-ui', { recursive: true });
  await page.goto(origin);
  async function assertAccountHeadingVisible(id) {
    const position = await page.locator('#' + id).evaluate(heading => {
      const nav = document.querySelector('.view-nav').getBoundingClientRect();
      const rect = heading.getBoundingClientRect();
      const point = document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2);
      return { top: rect.top, bottom: rect.bottom, navBottom: nav.bottom,
        viewport: innerHeight, uncovered: point === heading || heading.contains(point) };
    });
    assert.ok(position.top >= position.navBottom, `${id} overlaps sticky navigation: ${JSON.stringify(position)}`);
    assert.ok(position.bottom <= position.viewport && position.uncovered, `${id} is not fully visible`);
  }
  await page.getByRole('button', { name: 'Saved reports', exact: true }).click();
  await page.locator('#reports-account-gate').waitFor({ state: 'visible' });
  assert.equal(await page.locator('#personal-reports').isVisible(), false);
  await page.getByRole('button', { name: 'Check email', exact: true }).click();
  await page.getByRole('heading', { name: 'Highlight. Right-click. Check.', exact: true }).waitFor();
  checks.push('guest report gate and right-click-first local scanning instructions');
  await page.getByRole('button', { name: 'Create an account', exact: true }).click();
  await assertAccountHeadingVisible('account-sign-up-heading');
  await page.getByRole('textbox', { name: 'Name', exact: true }).fill('<img src=x> Demo');
  await page.getByRole('textbox', { name: 'Email', exact: true }).fill('casey@example.test');
  await page.getByRole('textbox', { name: 'Password', exact: true }).fill('Demo-only-123!');
  await page.getByRole('button', { name: 'Create account', exact: true }).click();
  await page.getByRole('heading', { name: 'Verify your email', exact: true }).waitFor();
  await assertAccountHeadingVisible('account-verify-heading');
  await page.getByRole('button', { name: 'Close account', exact: true }).click();
  await page.locator('#show-account').click();
  await assertAccountHeadingVisible('account-sign-in-heading');
  await page.locator('#account-email').fill('casey@example.test');
  await page.locator('#account-password').fill('Demo-only-123!');
  await page.locator('#account-sign-in').getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('alert').getByText('Verify your email before signing in.').waitFor();
  await page.locator('#open-verify').click();
  await assertAccountHeadingVisible('account-verify-heading');
  assert.equal(await page.locator('#verify-email').inputValue(), 'casey@example.test');
  await page.getByRole('button', { name: 'Back to sign in', exact: true }).click();
  await page.locator('#open-verify').click();
  await page.getByRole('button', { name: 'Resend code', exact: true }).click();
  await page.getByRole('textbox', { name: 'Verification code', exact: true }).fill('000000');
  await page.getByRole('button', { name: 'Verify email', exact: true }).click();
  await page.getByRole('alert').getByText('The demo verification code is incorrect.').waitFor();
  await page.getByRole('textbox', { name: 'Verification code', exact: true }).fill('123456');
  await page.getByRole('button', { name: 'Verify email', exact: true }).click();
  await page.getByText('Email verified. You are signed in.', { exact: true }).waitFor();
  assert.equal(await page.locator('#signup-password').inputValue(), '');
  checks.push('signup, blocked unverified login, reopened verification, OTP resend/retry and cleared password fields');
  await page.getByRole('button', { name: 'Saved reports', exact: true }).click();
  await page.locator('#history-list li').waitFor();
  assert.match(await page.locator('#history-list').textContent(), /<img src=x> Demo/);
  assert.equal(await page.locator('#account-identity img').count(), 0);
  await page.reload();
  await page.getByRole('button', { name: 'Account', exact: true }).waitFor();
  assert.equal(await page.locator('#account-sign-in').isVisible(), false);
  checks.push('session restoration and safe account name rendering');
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  assert.equal(await page.locator('#history-list').textContent(), '');
  assert.equal(await page.locator('#detail-content').textContent(), '');
  await page.getByRole('textbox', { name: 'Email', exact: true }).fill('bea@example.test');
  await page.getByRole('textbox', { name: 'Password', exact: true }).fill('Demo-only-123!');
  await page.locator('#account-sign-in').getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByText('Signed in to the demo account. No live account was used.', { exact: true }).waitFor();
  await page.getByRole('button', { name: 'Saved reports', exact: true }).click();
  await page.locator('#history-list li').waitFor();
  assert.match(await page.locator('#history-list').textContent(), /Bea Demo/);
  assert.doesNotMatch(await page.locator('#history-list').textContent(), /<img src=x> Demo/);
  checks.push('sign-out removes old reports; switched account sees only its synthetic reports');
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await page.getByRole('button', { name: 'Forgot password?', exact: true }).click();
  await assertAccountHeadingVisible('account-recover-heading');
  await page.getByRole('button', { name: 'Back to sign in', exact: true }).click();
  await page.getByRole('button', { name: 'Forgot password?', exact: true }).click();
  await page.getByRole('textbox', { name: 'Email', exact: true }).fill('bea@example.test');
  await page.getByRole('button', { name: 'Send recovery instructions', exact: true }).click();
  await assertAccountHeadingVisible('account-reset-heading');
  await page.getByRole('textbox', { name: 'Recovery code', exact: true }).fill('123456');
  await page.getByRole('textbox', { name: 'New password', exact: true }).fill('Different-demo-123!');
  await page.getByRole('button', { name: 'Update password', exact: true }).click();
  await page.getByText('Password updated. Sign in with your new password.', { exact: true }).waitFor();
  await assertAccountHeadingVisible('account-sign-in-heading');
  await page.locator('#account-email').fill('bea@example.test');
  await page.locator('#account-password').fill('Different-demo-123!');
  await page.locator('#account-sign-in').getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('button', { name: 'Account', exact: true }).waitFor();
  checks.push('password recovery and sign-in with changed demo password');
  await page.evaluate(() => {
    const session = JSON.parse(sessionStorage.getItem('phishlens-demo-session'));
    session.expiresAt = 0;
    sessionStorage.setItem('phishlens-demo-session', JSON.stringify(session));
  });
  await page.reload();
  await page.getByText('Your session expired. Sign in again.', { exact: true }).waitFor();
  assert.equal(await page.locator('#personal-reports').isVisible(), false);
  assert.equal(await page.locator('#history-list').textContent(), '');
  checks.push('expired restored session shows a clear message and no report data');
  await assertAccountHeadingVisible('account-sign-in-heading');
  for (const [width, height] of [[380, 600], [320, 500]]) {
    await page.setViewportSize({ width, height });
    for (const [button, heading] of [
      ['#open-sign-up', 'account-sign-up-heading'],
      ['#open-verify', 'account-verify-heading'],
      ['#open-recover', 'account-recover-heading']
    ]) {
      await page.locator('#close-account').click();
      await page.locator('#show-account').click();
      await page.locator(button).click();
      await assertAccountHeadingVisible(heading);
    }
  }
  checks.push('focused account headings remain below sticky navigation at 380px and 320px widths');
  await page.screenshot({ path: 'output/account-ui/account-preview.png', fullPage: true });
  assert.deepEqual(errors, []); assert.deepEqual(externalRequests, []);
  await writeFile('output/account-ui/results.json', JSON.stringify({ scope: 'local mocked accounts, no live auth', browser: browser.version(), checks, errors, externalRequests }, null, 2) + '\n');
  console.log(JSON.stringify({ result: 'passed', checks, externalRequests: 0 }));
} finally {
  if (browser) await browser.close();
  server.kill();
  if (server.exitCode === null) await once(server, 'exit');
}

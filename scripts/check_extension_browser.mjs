// Installed-extension integration smoke test. All API responses are intercepted;
// this is software verification, not a new accuracy or latency benchmark.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdtemp, rm, mkdir, readFile, writeFile } from 'node:fs/promises';
import { pathToFileURL, fileURLToPath } from 'node:url';
import os from 'node:os';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const chromePath = process.env.PHISHLENS_CHROME;
const playwrightPath = process.env.PHISHLENS_PLAYWRIGHT;
if (!chromePath || !playwrightPath) throw Error('Set PHISHLENS_CHROME and PHISHLENS_PLAYWRIGHT to existing local runtimes.');
const { chromium } = await import(pathToFileURL(playwrightPath).href);
const profile = await mkdtemp(path.join(os.tmpdir(), 'phishlens-browser-'));
let context;
const evidence = { scope: 'installed unpacked extension and side-panel page software smoke; intercepted API, no database',
  recorded_at: new Date().toISOString(), platform: os.platform(), os_release: os.release(),
  checks: [], accuracy_test: false, database_persistence_tested: false };
const check = name => evidence.checks.push(name);
try {
  const packageIdentity = JSON.parse(await readFile(path.join(root, 'output/extension/evidence.json'), 'utf8'));
  const archive = await readFile(path.join(root, 'output/extension/PhishLens-Extension.zip'));
  assert.equal(createHash('sha256').update(archive).digest('hex'), packageIdentity.archive_sha256);
  assert.equal(packageIdentity.runtime_or_packaging_changes, false,
    'The installed Chrome smoke must use package inputs from a clean revision');
  const manifest = JSON.parse(await readFile(path.join(root, 'extension/manifest.json'), 'utf8'));
  assert.equal(manifest.version, packageIdentity.extension_version);
  for (const [asset, expected] of Object.entries(packageIdentity.files_sha256)) {
    const content = await readFile(path.join(root, 'extension', asset));
    assert.equal(createHash('sha256').update(content).digest('hex'), expected,
      `The Chrome smoke source differs from the packaged asset: ${asset}`);
  }
  evidence.source_commit = packageIdentity.source_commit;
  evidence.extension_version = packageIdentity.extension_version;
  evidence.package_sha256 = packageIdentity.archive_sha256;
  check('Chrome smoke source files match the exact clean packaged revision');
  context = await chromium.launchPersistentContext(profile, {
    executablePath: chromePath, headless: true, ignoreDefaultArgs: ['--disable-extensions'],
    args: ['--enable-unsafe-extension-debugging', '--disable-background-networking', '--no-first-run']
  });
  evidence.chrome = context.browser()?.version();
  const session = await context.browser().newBrowserCDPSession();
  const { id } = await session.send('Extensions.loadUnpacked', { path: path.join(root, 'extension') });
  check('Actual unpacked extension loaded in isolated Chrome profile');
  const requests = [];
  const sha = 'a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c';
  let saved = false, deleted = false;
  let record = { id: '29d80c39-ec0d-4db8-a6e5-87444ba2600c', subject: 'Software smoke <script>alert(1)</script>',
    prediction: 'legitimate', confidence: null, risk_level: 'low', threat_indicators: [],
    explanation: 'Fixture response, not database evidence.', created_at: '2026-10-29T02:00:00Z',
    body: 'Please review the meeting agenda. Do not share your password.', notes: null, feedback: 'none',
    analysis_mode: 'real', analysis_provenance: { model: 'word_plus_char_wb_C1p0', model_revision: sha } };
  // No request is allowed to reach a remote API, even on unexpected code paths.
  await context.route(/^https?:\/\//, async route => {
    const request = route.request(); const url = new URL(request.url());
    requests.push({ path: url.pathname, method: request.method() });
    let body;
    if (url.pathname === '/model-info') body = { provider_mode: 'tfidf', model_sha256: sha,
      accepts_tfidf_reports: true, accepts_local_reviews: true };
    else if (url.pathname === '/api/analyses' && request.method() === 'POST') {
      assert.equal(request.headers()['x-phishlens-model'], sha);
      assert.ok(request.headers()['idempotency-key']); saved = true;
      record = { ...record, ...request.postDataJSON() }; body = record;
    } else if (url.pathname === '/api/analyses') body = { items: saved && !deleted ? [record] : [] };
    else if (url.pathname.endsWith(record.id) && request.method() === 'PATCH') {
      record = { ...record, ...request.postDataJSON() }; body = record;
    } else if (url.pathname.endsWith(record.id) && request.method() === 'DELETE') {
      deleted = true; await route.fulfill({ status: 204 }); return;
    } else if (url.pathname.endsWith(record.id)) body = record;
    else { await route.abort(); return; }
    await route.fulfill({ status: request.method() === 'POST' ? 201 : 200,
      contentType: 'application/json', body: JSON.stringify(body) });
  });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  // Issue #146: the release package must show no console errors or permission warnings.
  const consoleIssues = [];
  page.on('console', message => {
    if (message.type() === 'error' || (message.type() === 'warning' && /permission/i.test(message.text()))) {
      consoleIssues.push(`${message.type()}: ${message.text()}`);
    }
  });
  context.on('weberror', webError => consoleIssues.push(`weberror: ${webError.error().message}`));
  await page.goto('chrome-extension://' + id + '/popup.html');
  await page.locator('#empty-state').waitFor({ state: 'visible' });
  const manifestPermissions = JSON.parse(await readFile(path.join(root, 'extension/manifest.json'), 'utf8'));
  const granted = await page.evaluate(() => chrome.permissions.getAll());
  assert.deepEqual([...granted.permissions].sort(), [...manifestPermissions.permissions].sort(),
    'Chrome must grant exactly the manifest permissions');
  assert.deepEqual([...granted.origins].sort(), [...manifestPermissions.host_permissions].sort(),
    'Chrome must grant exactly the manifest host permissions');
  evidence.granted_permissions = { permissions: [...granted.permissions].sort(), origins: [...granted.origins].sort() };
  check('Actual Chrome grants exactly the manifest permissions and host permissions');
  const panelBehavior = await page.evaluate(() => chrome.sidePanel.getPanelBehavior());
  assert.equal(panelBehavior.openPanelOnActionClick, true);
  // A configured popup takes priority over openPanelOnActionClick, so none may be set.
  assert.equal(await page.evaluate(() => chrome.action.getPopup({})), '');
  check('Actual Chrome reports no toolbar popup and openPanelOnActionClick, so the toolbar opens the side panel');
  assert.equal(requests.length, 0); check('Side-panel page opens without API or text-upload requests');
  await page.evaluate(async text => {
    await chrome.runtime.sendMessage({ type: 'phishlens-analyze-text', text });
  }, record.body);
  await page.locator('#result-state').waitFor({ state: 'visible' });
  assert.equal(requests.length, 0);
  assert.match(await page.locator('#classification').innerText(), /Suspicious — review before acting|No strong warning signs|Uncertain — check before acting/);
  assert.doesNotMatch(await page.locator('#result-state').innerText(), /undefined|NaN/);
  check('Actual service worker scans locally and the side-panel page displays a labeled result');
  const out = path.join(root, 'output/tfidf-integration-20261029');
  await mkdir(out, { recursive: true });
  await page.screenshot({ path: path.join(out, 'extension-scan.png'), fullPage: true });
  // This smoke loads the real source folder without a test session, so personal report saving
  // must stay unavailable. Saved-report CRUD is covered by npm run test:browser with a mock session.
  assert.equal(await page.locator('#save-report').isDisabled(), true);
  assert.equal(await page.locator('#save-consent').isDisabled(), true);
  assert.equal(requests.length, 0);
  check('Report saving stays disabled and uploads nothing while signed out');
  assert.equal(await page.locator('script:not([src])').count(), 0);
  check('No inline script is present in the rendered side-panel page');
  await page.evaluate(async () => { await chrome.storage.session.set({ phishlensDebugFailNext: true });
    await chrome.runtime.sendMessage({ type: 'phishlens-analyze-text', text: 'Meeting agenda' }); });
  await page.locator('#error-state').waitFor({ state: 'visible' });
  await page.locator('#result-state').waitFor({ state: 'hidden' });
  check('Simulated model failure shows Unable to assess with no released verdict');
  await page.evaluate(async () => { await chrome.runtime.sendMessage({ type: 'phishlens-analyze-text', text: 'Meeting agenda for the team.' }); });
  await page.locator('#result-state').waitFor({ state: 'visible' });
  await page.click('#clear-button'); await page.locator('#empty-state').waitFor({ state: 'visible' });
  check('Retry and Clear work in the installed extension');

  // Keyboard-only checks in installed Chrome (Issue #136): no clicks or programmatic focus.
  const describeFocus = () => page.evaluate(() => {
    const element = document.activeElement;
    if (!element || element === document.body) return null;
    const box = element.getBoundingClientRect();
    const style = getComputedStyle(element);
    const parentStyle = element.parentElement ? getComputedStyle(element.parentElement) : null;
    const labelled = element.getAttribute('aria-labelledby')
      ?.split(/\s+/).map(labelId => document.getElementById(labelId)?.textContent ?? '').join(' ');
    const name = (element.getAttribute('aria-label') || labelled || element.labels?.[0]?.textContent
      || element.textContent || element.getAttribute('title') || '').replace(/\s+/g, ' ').trim();
    const outlined = value => value && value.outlineStyle !== 'none' && parseFloat(value.outlineWidth) > 0;
    return { id: element.id, tag: element.tagName.toLowerCase(), name,
      visible: box.width > 0 && box.height > 0 && style.visibility !== 'hidden',
      indicator: Boolean(outlined(style) || outlined(parentStyle)) };
  });
  const tabUntil = async (matches, limit = 60) => {
    for (let step = 0; step < limit; step++) {
      await page.keyboard.press('Tab');
      const focused = await describeFocus();
      if (focused && matches(focused)) return focused;
    }
    throw Error('Keyboard focus did not reach the expected control');
  };
  // Walk the full Tab cycle (wrapping past the end of the page) and stop when a control repeats.
  const tabCycle = async view => {
    const seen = [];
    let outsidePage = 0;
    for (let step = 0; step < 80; step++) {
      await page.keyboard.press('Tab');
      const focused = await describeFocus();
      if (!focused) { if (++outsidePage > 3) break; continue; }
      const key = `${focused.tag}#${focused.id}:${focused.name}`;
      if (seen.includes(key)) break;
      seen.push(key);
      assert.ok(focused.visible, `${view}: keyboard focus reached a hidden control (${key})`);
      assert.ok(focused.name, `${view}: focused control has no accessible name (${key})`);
      assert.ok(focused.indicator, `${view}: focused control has no visible focus indicator (${key})`);
    }
    assert.ok(seen.length >= 3, `${view}: Tab must reach the page controls`);
    return seen;
  };
  evidence.keyboard_tab_order = { check_email: await tabCycle('Check email view') };
  await tabUntil(focused => focused.id === 'scan-body');
  await page.keyboard.type('Synthetic keyboard check: please review the attached agenda before Friday.');
  await tabUntil(focused => focused.id === 'scan-button');
  await page.keyboard.press('Enter');
  await page.locator('#result-state').waitFor({ state: 'visible' });
  assert.match(await page.locator('#classification').innerText(), /Suspicious — review before acting|No strong warning signs|Uncertain — check before acting/);
  assert.doesNotMatch(await page.locator('#classification').innerText(), /\b(safe|genuine|legitimate)\b/i,
    'A local result must never be presented as a safe verdict');
  assert.equal(requests.length, 0);
  check('Keyboard-only paste and Check this email shows a labeled result without a safe verdict');
  await tabUntil(focused => focused.id === 'show-reports');
  await page.keyboard.press('Enter');
  await page.locator('#reports-view').waitFor({ state: 'visible' });
  await page.locator('#reports-account-gate').waitFor({ state: 'visible' });
  assert.equal(await page.locator('#show-reports').getAttribute('aria-pressed'), 'true');
  evidence.keyboard_tab_order.saved_reports_signed_out = await tabCycle('Saved reports view (signed out)');
  assert.ok(evidence.keyboard_tab_order.saved_reports_signed_out.some(key => key.includes('reports-sign-in')),
    'Signed out, Tab must reach the sign-in action for saved reports');
  check('Keyboard Tab cycles reach only visible, named controls with a focus indicator in both views');
  assert.equal(requests.length, 0);

  assert.deepEqual(errors, []); check('No side-panel page JavaScript errors observed');
  evidence.console_issues = consoleIssues;
  assert.deepEqual(consoleIssues, [], 'The page must log no console errors or permission warnings');
  check('No console errors or permission warnings observed');
  evidence.api_requests_intercepted = requests.length;
  evidence.installed_extension = true; evidence.success = true;
} catch (error) {
  evidence.success = false; evidence.failure = error.message;
  process.exitCode = 1;
} finally {
  if (context) await context.close();
  // Only remove the exact disposable profile created by this script.
  const absolute = path.resolve(profile);
  if (path.dirname(absolute) !== path.resolve(os.tmpdir()) || !path.basename(absolute).startsWith('phishlens-browser-')) {
    throw Error('Unexpected temporary profile path; refusing cleanup');
  }
  await rm(absolute, { recursive: true, force: true });
  evidence.temporary_profile_removed = true;
  const out = path.join(root, 'output/tfidf-integration-20261029'); await mkdir(out, { recursive: true });
  await writeFile(path.join(out, 'browser-verification.json'), JSON.stringify(evidence, null, 2) + '\n');
  console.log(JSON.stringify(evidence, null, 2));
}

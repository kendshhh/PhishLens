// Installed-extension integration smoke test. All API responses are intercepted;
// this is software verification, not a new accuracy or latency benchmark.
import assert from 'node:assert/strict';
import { mkdtemp, rm, mkdir, writeFile } from 'node:fs/promises';
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
const evidence = { scope: 'installed-extension software smoke; intercepted API, no database',
  recorded_at: new Date().toISOString(), platform: os.platform(), os_release: os.release(),
  checks: [], accuracy_test: false, database_persistence_tested: false };
const check = name => evidence.checks.push(name);
try {
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
  await page.goto('chrome-extension://' + id + '/popup.html');
  await page.locator('#empty-state').waitFor({ state: 'visible' });
  assert.equal(requests.length, 0); check('Popup opens without API or text-upload requests');
  await page.evaluate(async text => {
    await chrome.runtime.sendMessage({ type: 'phishlens-analyze-text', text });
  }, record.body);
  await page.locator('#result-state').waitFor({ state: 'visible' });
  assert.equal(requests.length, 0);
  assert.match(await page.locator('#threshold').innerText(), /88.71%/);
  assert.doesNotMatch(await page.locator('#evidence').innerText(), /undefined/);
  check('Actual service worker scans locally and popup displays verified English insights');
  const out = path.join(root, 'output/tfidf-integration-20261029');
  await mkdir(out, { recursive: true });
  await page.screenshot({ path: path.join(out, 'extension-scan.png'), fullPage: true });
  await page.click('#save-report'); assert.equal(requests.length, 0);
  check('Save requires explicit upload consent');
  await page.fill('#report-subject', 'Software smoke <script>alert(1)</script>');
  await page.check('#save-consent'); await page.click('#save-report');
  await page.getByText('Saved and reread successfully.', { exact: true }).waitFor();
  assert.equal(requests.filter(r => r.method === 'POST').length, 1);
  check('Save, fresh detail reread and history refresh use the contributors API contract (intercepted)');
  assert.equal(await page.locator('script:not([src])').count(), 0);
  await page.fill('#report-notes', 'Smoke test feedback');
  await page.selectOption('#report-feedback', 'false_positive'); await page.click('#update-report');
  await page.getByText('Notes and feedback saved. Feedback does not retrain the model.', { exact: true }).waitFor();
  assert.equal(record.feedback, 'false_positive'); check('Notes and feedback update without changing model weights');
  await page.check('#delete-consent'); await page.click('#delete-report');
  await page.locator('#detail-panel').waitFor({ state: 'hidden' });
  assert.equal(deleted, true); check('Explicit delete and empty history rendering work');
  await page.evaluate(async () => { await chrome.storage.session.set({ phishlensDebugFailNext: true });
    await chrome.runtime.sendMessage({ type: 'phishlens-analyze-text', text: 'Meeting agenda' }); });
  await page.locator('#error-state').waitFor({ state: 'visible' });
  await page.locator('#result-state').waitFor({ state: 'hidden' });
  check('Simulated model failure shows Unable to assess with no released verdict');
  await page.evaluate(async () => { await chrome.runtime.sendMessage({ type: 'phishlens-analyze-text', text: 'Meeting agenda for the team.' }); });
  await page.locator('#result-state').waitFor({ state: 'visible' });
  await page.click('#clear-button'); await page.locator('#empty-state').waitFor({ state: 'visible' });
  check('Retry and Clear work in the installed extension');
  assert.deepEqual(errors, []); check('No popup JavaScript errors observed');
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

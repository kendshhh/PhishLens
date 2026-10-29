// Actual local LLM inference on one clearly identified software fixture.
// This is an integration check, not an accuracy benchmark or held-out scoring.
import { mkdtemp, rm, mkdir, writeFile } from 'node:fs/promises';
import { pathToFileURL, fileURLToPath } from 'node:url';
import path from 'node:path';
import os from 'node:os';
import assert from 'node:assert/strict';

const root = fileURLToPath(new URL('../', import.meta.url));
const { chromium } = await import(pathToFileURL(process.env.PHISHLENS_PLAYWRIGHT).href);
const profile = await mkdtemp(path.join(os.tmpdir(), 'phishlens-live-'));
let context, polling;
const record = { purpose: 'one software fixture, actual local LLM; not a new benchmark',
  recorded_at: new Date().toISOString(), checks: [], reserved_records_opened: 0 };
try {
  context = await chromium.launchPersistentContext(profile, { executablePath: process.env.PHISHLENS_CHROME,
    headless: true, ignoreDefaultArgs: ['--disable-extensions'],
    args: ['--enable-unsafe-extension-debugging', '--disable-background-networking', '--no-first-run'] });
  record.chrome = context.browser().version();
  const session = await context.browser().newBrowserCDPSession();
  const { id } = await session.send('Extensions.loadUnpacked', { path: path.join(root, 'extension') });
  const page = await context.newPage(); await page.setViewportSize({ width: 440, height: 900 });
  const errors = [], requests = [], apiRequests = [];
  const sha = 'a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c';
  let saved = false, deleted = false;
  let detail = { id: '29d80c39-ec0d-4db8-a6e5-87444ba2600c', subject: 'Software fixture',
    prediction: 'legitimate', confidence: null, risk_level: 'low', threat_indicators: [],
    explanation: 'Intercepted software response; not database evidence.', created_at: '2026-10-29T02:00:00Z',
    body: '', notes: null, feedback: 'none', analysis_mode: 'real', analysis_provenance: {} };
  context.on('console', message => { if (message.type() === 'error') errors.push(message.text().slice(0, 300)); });
  await context.route(/^https?:\/\//, async route => {
    const request = route.request(), url = new URL(request.url());
    let body;
    if (url.pathname === '/model-info') body = { provider_mode: 'tfidf', model_sha256: sha,
      accepts_tfidf_reports: true, accepts_local_reviews: true };
    else if (url.pathname === '/api/analyses' && request.method() === 'POST') {
      const payload = request.postDataJSON();
      assert.equal(request.headers()['x-phishlens-model'], sha);
      assert.ok(request.headers()['idempotency-key']);
      assert.equal(payload.local_review.reevaluators.length, 3);
      assert.equal(payload.local_review.judge.valid, true);
      detail = { ...detail, subject: payload.subject, body: payload.body,
        review_status: payload.local_review.status,
        analysis_provenance: { model_revision: sha, local_review: payload.local_review } };
      saved = true; body = detail;
    } else if (url.pathname === '/api/analyses') body = { items: saved && !deleted ? [detail] : [] };
    else if (url.pathname.endsWith(detail.id) && request.method() === 'PATCH') {
      detail = { ...detail, ...request.postDataJSON() }; body = detail;
    } else if (url.pathname.endsWith(detail.id) && request.method() === 'DELETE') {
      apiRequests.push({ path: url.pathname, method: request.method() });
      deleted = true; await route.fulfill({ status: 204 }); return;
    } else if (url.pathname.endsWith(detail.id)) body = detail;
    else { requests.push(url.hostname); await route.abort(); return; }
    apiRequests.push({ path: url.pathname, method: request.method() });
    await route.fulfill({ status: request.method() === 'POST' ? 201 : 200,
      contentType: 'application/json', body: JSON.stringify(body) });
  });
  await page.goto('chrome-extension://' + id + '/popup.html');
  await page.evaluate(async () => chrome.storage.session.set({ phishlensDebug: true }));
  record.checks.push('Unpacked extension with offscreen permission loaded');
  const stages = [];
  polling = setInterval(async () => {
    try {
      const s = await page.evaluate(async () => (await chrome.storage.session.get('veriqoAnalysis')).veriqoAnalysis);
      const label = s?.stage || s?.status;
      if (label && stages.at(-1) !== label) { stages.push(label); console.log(JSON.stringify({ stage: label })); }
    } catch { /* browser shutdown is recorded below */ }
  }, 1000);
  record.stages_observed = stages;
  await page.evaluate(async () => chrome.runtime.sendMessage({ type: 'phishlens-analyze-text',
    text: 'Team meeting tomorrow at ten. Please review the project agenda. Thank you.' }));
  const state = await page.evaluate(async () => (await chrome.storage.session.get('veriqoAnalysis')).veriqoAnalysis);
  record.scan_status = state.status;
  record.workflow = state.result?.workflow;
  record.primary_score = state.result?.score;
  record.error = state.error;
  record.runtime_diagnostic = await page.evaluate(async () => (await chrome.storage.session.get('phishlensLastJudgeDiagnostic')).phishlensLastJudgeDiagnostic);
  record.external_request_hosts = requests;
  record.console_errors = errors;
  const out = path.join(root, 'implementation/live_review/results'); await mkdir(out, { recursive: true });
  await page.screenshot({ path: path.join(root, 'output/tfidf-integration-20261029/live-workflow.png'), fullPage: true });
  record.actual_judge_output_valid = state.result?.workflow?.judge?.valid === true;
  record.all_three_reevaluators = state.result?.workflow?.reevaluators?.length === 3;
  record.full_workflow_completed = record.actual_judge_output_valid && record.all_three_reevaluators;
  if (record.full_workflow_completed) {
    assert.equal(apiRequests.length, 0);
    await page.evaluate(async () => chrome.runtime.sendMessage({ type: 'phishlens-analyze-text',
      text: 'Team meeting tomorrow at ten. Please review the project agenda. Thank you.' }));
    const warm = await page.evaluate(async () => (await chrome.storage.session.get('veriqoAnalysis')).veriqoAnalysis);
    record.warm_software_check = { status: warm.result?.workflow?.status,
      judge_valid: warm.result?.workflow?.judge?.valid, generated_tokens: warm.result?.workflow?.judge?.generated_tokens,
      elapsed_ms: warm.result?.workflow?.elapsed_ms, reevaluators: warm.result?.workflow?.reevaluators?.length };
    if (!record.warm_software_check.judge_valid) process.exitCode = 1;
    assert.equal(apiRequests.length, 0);
    await page.click('#save-report'); assert.equal(apiRequests.length, 0);
    await page.fill('#report-subject', 'Software fixture <script>alert(1)</script>');
    await page.check('#save-consent'); await page.click('#save-report');
    await page.getByText('Saved and reread successfully.', { exact: true }).waitFor();
    assert.equal(apiRequests.filter(r => r.method === 'POST').length, 1);
    await page.fill('#report-notes', 'Software check only');
    await page.selectOption('#report-feedback', 'false_positive'); await page.click('#update-report');
    await page.getByText('Notes and feedback saved. Feedback does not retrain the model.', { exact: true }).waitFor();
    assert.equal(detail.feedback, 'false_positive');
    await page.check('#delete-consent'); await page.click('#delete-report');
    await page.locator('#detail-panel').waitFor({ state: 'hidden' }); assert.equal(deleted, true);
    assert.equal(await page.locator('script:not([src])').count(), 0);
    record.intercepted_api_software_check = { explicit_consent: true, create_reread_history: true,
      notes_feedback_delete: true, review_metadata: true, database_persistence_tested: false };
    await page.evaluate(() => { void chrome.runtime.sendMessage({ type: 'phishlens-analyze-text', text: 'Another team meeting tomorrow.' }); });
    await page.locator('#loading-state').waitFor({ state: 'visible' });
    await page.click('#clear-button');
    await page.locator('#empty-state').waitFor({ state: 'visible' });
    await page.waitForTimeout(500);
    const cleared = await page.evaluate(async () => (await chrome.storage.session.get('veriqoAnalysis')).veriqoAnalysis);
    record.cancel_cleared_active_review = cleared === undefined;
    if (!record.cancel_cleared_active_review) process.exitCode = 1;
  }
  if (!record.full_workflow_completed) process.exitCode = 1;
} catch (error) { record.failure = error.message; process.exitCode = 1; }
finally {
  clearInterval(polling);
  if (context) await context.close();
  if (path.dirname(path.resolve(profile)) !== path.resolve(os.tmpdir()) || !path.basename(profile).startsWith('phishlens-live-')) throw Error('Unsafe profile cleanup path');
  try {
    await rm(profile, { recursive: true, force: true, maxRetries: 10, retryDelay: 250 });
    record.temporary_profile_removed = true;
  } catch { record.temporary_profile_removed = false; record.cleanup_pending_profile = profile; }
  const out = path.join(root, 'implementation/live_review/results'); await mkdir(out, { recursive: true });
  await writeFile(path.join(out, 'browser-software-check.json'), JSON.stringify(record, null, 2) + '\n');
  console.log(JSON.stringify(record, null, 2));
}

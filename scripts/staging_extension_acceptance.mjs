import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { chromium } from 'playwright';

const execFileAsync = promisify(execFile);
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const STAGING_ORIGIN = 'https://phishlens-staging.onrender.com';
const PRODUCTION_ORIGIN = 'https://phishlens-api-ocvt.onrender.com';
const SHA40 = /^[0-9a-f]{40}$/;
const SHA256 = /^[0-9a-f]{64}$/;
const evidence = {
  format: 'phishlens-staging-product-acceptance-v1',
  status: 'blocked',
  phase: 'preflight',
  environment: 'staging',
  production_requests: 0,
  production_writes: 0,
  production_auth_requests: 0,
  product: {},
  user_experience: {},
  ai_acceptance: { status: 'blocked' },
};
let context;
let page;
let activeAccount = null;
let productionAuthOrigin = null;
const accessTokens = new Map();
const createdIds = new Map();
const createdAnalysisEvidence = new Map();

function required(name) {
  const value = process.env[name]?.trim();
  assert.ok(value, `Missing protected staging setting ${name}`);
  return value;
}

function sha256(data) {
  return createHash('sha256').update(data).digest('hex');
}

function subjectHash(subject) {
  return sha256(`phishlens-staging-subject-v1:${subject}`);
}

async function readJson(file) {
  const value = JSON.parse(await readFile(file, 'utf8'));
  assert.ok(value && typeof value === 'object' && !Array.isArray(value));
  return value;
}

async function verifyPreflight() {
  assert.equal(process.env.STAGING_ACCEPTANCE_ENABLED, 'true', 'Live staging acceptance is not enabled');
  assert.equal(process.env.STAGING_BASE_URL, STAGING_ORIGIN, 'Only the approved staging API origin is allowed');
  const sourceSha = required('RELEASE_SOURCE_SHA');
  const backendSha = required('STAGING_EXPECTED_BACKEND_SHA');
  const imageDigest = required('STAGING_EXPECTED_IMAGE_DIGEST');
  assert.match(sourceSha, SHA40);
  assert.equal(backendSha, sourceSha, 'Staging backend and release source SHA differ');
  assert.match(imageDigest, /^sha256:[0-9a-f]{64}$/);

  const packagePath = path.resolve(required('RELEASE_EXTENSION_ZIP'));
  const packageEvidencePath = path.resolve(required('RELEASE_EXTENSION_EVIDENCE'));
  const aiApproval = JSON.parse(required('STAGING_AI_APPROVAL_JSON'));
  const packageEvidence = await readJson(packageEvidencePath);
  const archiveDigest = sha256(await readFile(packagePath));
  assert.equal(packageEvidence.archive_sha256, archiveDigest);
  assert.equal(packageEvidence.source_commit, sourceSha);
  assert.equal(packageEvidence.format, 'phishlens-release-extension-v1');
  assert.equal(packageEvidence.production_default, true);
  assert.equal(packageEvidence.auth_enabled, true);
  assert.equal(packageEvidence.api_origins?.staging, STAGING_ORIGIN);
  assert.equal(packageEvidence.api_origins?.production, PRODUCTION_ORIGIN);
  assert.equal(packageEvidence.staging_selection, 'popup.html?environment=staging');
  productionAuthOrigin = new URL(packageEvidence.auth_configs?.production?.authUrl || '').origin;
  assert.ok(productionAuthOrigin.startsWith('https://'), 'Production Auth origin is missing from the release sidecar');
  assert.equal(required('STAGING_AUTH_URL'), packageEvidence.auth_configs?.staging?.authUrl);
  assert.equal(required('STAGING_AUTH_DATABASE'), packageEvidence.auth_configs?.staging?.database);

  const extensionOrigin = `chrome-extension://${packageEvidence.chrome_extension_id}`;
  assert.equal(required('STAGING_AUTH_TRUSTED_CHROME_ORIGIN'), extensionOrigin,
    'The staging Neon Auth trusted-origin setting must match this exact package ID');
  assert.equal(required('STAGING_NEON_BRANCH_KIND'), 'schema-only');
  assert.equal(required('STAGING_NEON_PARENT_ID'), '', 'The staging Neon branch must be an independent root');
  const branchId = required('STAGING_NEON_BRANCH_ID');
  assert.match(branchId, /^br-[a-z0-9-]+$/);
  assert.notEqual(branchId, required('PRODUCTION_NEON_BRANCH_ID'));
  assert.equal(required('STAGING_NEON_PRODUCTION_ROWS_PRESENT'), 'false');

  const modelApproval = validateModelApproval(aiApproval);
  evidence.source_sha = sourceSha;
  evidence.backend_source_sha = backendSha;
  evidence.backend_image_digest = imageDigest;
  evidence.extension_zip_sha256 = archiveDigest;
  evidence.extension_version = packageEvidence.extension_version;
  evidence.extension_id = packageEvidence.chrome_extension_id;
  evidence.staging_api_origin = STAGING_ORIGIN;
  evidence.database = {
    project_id: required('STAGING_NEON_PROJECT_ID'),
    branch_id: branchId,
    production_branch_id: process.env.PRODUCTION_NEON_BRANCH_ID,
    branch_kind: 'schema-only',
    parent_id: null,
    production_rows_present: false,
    migration_revision: required('STAGING_MIGRATION_REVISION'),
  };
  evidence.auth = { mode: 'neon-auth', enabled: true };
  assert.match(required('STAGING_MIGRATION_REVISION'), /^[A-Za-z0-9_]+$/);
  evidence.ai_acceptance = modelApproval;
  return { packagePath, packageEvidence, sourceSha, backendSha, imageDigest, branchId, modelApproval };
}

function validateModelApproval(report) {
  assert.equal(report.approved, true, 'AI evaluation is not approved');
  assert.equal(report.cohort?.kind, 'held-out-representative', 'AI evaluation is not a held-out cohort');
  assert.ok(Number.isInteger(report.cohort?.phishing_families) && report.cohort.phishing_families >= 100);
  assert.ok(Number.isInteger(report.cohort?.legitimate_families) && report.cohort.legitimate_families >= 200);
  assert.ok(Number.isInteger(report.cohort?.spam_families) && report.cohort.spam_families >= 100);
  assert.equal(report.valid_results, report.attempted_results);
  assert.ok(Number.isInteger(report.attempted_results) && report.attempted_results >= 400);
  assert.ok(Number.isFinite(report.metrics?.phishing_recall));
  assert.ok(Number.isFinite(report.metrics?.legitimate_false_positive_rate));
  assert.ok(Number.isFinite(report.thresholds?.phishing_recall_min));
  assert.ok(Number.isFinite(report.thresholds?.legitimate_false_positive_rate_max));
  assert.ok(report.metrics.phishing_recall >= report.thresholds.phishing_recall_min);
  assert.ok(report.metrics.legitimate_false_positive_rate <= report.thresholds.legitimate_false_positive_rate_max);
  assert.match(report.evaluation_sha256 || '', SHA256);
  assert.match(report.model_revision || '', /^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$/,
    'Model revision must be an exact immutable model identifier, not a moving alias');
  assert.doesNotMatch(report.model_revision, /^(latest|stable|default)$/i);
  assert.ok(report.provider && !['disabled', 'mock'].includes(String(report.provider).toLowerCase()));
  assert.ok(typeof report.reviewer === 'string' && report.reviewer.trim());
  return {
    status: 'passed',
    approved: true,
    provider: report.provider,
    model_revision: report.model_revision,
    evaluation_sha256: report.evaluation_sha256,
    cohort_sha256: report.cohort_sha256,
    cohort: report.cohort,
    metrics: report.metrics,
    thresholds: report.thresholds,
    reviewer: report.reviewer,
  };
}

async function getJson(url) {
  const response = await fetch(url, { redirect: 'error', cache: 'no-store', signal: AbortSignal.timeout(15000) });
  assert.equal(response.status, 200, `Staging preflight endpoint failed: ${new URL(url).pathname}`);
  return response.json();
}

async function verifyService(modelApproval, sourceSha, imageDigest) {
  const [version, health, ready, model] = await Promise.all([
    getJson(STAGING_ORIGIN + '/version'),
    getJson(STAGING_ORIGIN + '/health'),
    getJson(STAGING_ORIGIN + '/ready'),
    getJson(STAGING_ORIGIN + '/model-info'),
  ]);
  assert.equal(version.environment, 'staging');
  assert.equal(version.commit, sourceSha);
  assert.equal(health.status, 'ok');
  assert.equal(ready.status, 'ready');
  assert.equal(ready.database, 'connected');
  assert.equal(model.provider_mode, modelApproval.provider);
  assert.notEqual(model.provider_mode, 'disabled');
  assert.notEqual(model.provider_mode, 'unavailable');
  assert.notEqual(model.provider_mode, 'mock');
  if (model.provider_mode === 'tfidf') assert.equal(model.model_sha256, modelApproval.model_revision);
  if (model.model && typeof model.model === 'string') assert.equal(model.model, modelApproval.model_revision);
  if (modelApproval.provider === 'gemini') assert.equal(model.spend_guard_enabled, true);
  evidence.service = {
    version, health: { status: health.status }, ready,
    model_info: model.provider_mode === 'tfidf'
      ? { provider_mode: model.provider_mode, model_sha256: model.model_sha256 }
      : { provider_mode: model.provider_mode, model: model.model },
  };
  evidence.backend_image_digest = imageDigest;
  return model;
}

async function extractExtension(archivePath, destination) {
  await mkdir(destination, { recursive: true });
  await execFileAsync('python', ['-c',
    'import sys,zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])',
    archivePath, destination,
  ]);
}

async function launchExtension(archivePath, extensionId) {
  const { mkdtemp } = await import('node:fs/promises');
  const profile = await mkdtemp(path.join(os.tmpdir(), 'phishlens-release-'));
  const unpacked = path.join(profile, 'extension');
  await extractExtension(archivePath, unpacked);
  try {
    context = await chromium.launchPersistentContext(profile, {
      headless: true,
      viewport: { width: 440, height: 760 },
      ignoreDefaultArgs: ['--disable-extensions'],
      args: [`--disable-extensions-except=${unpacked}`, `--load-extension=${unpacked}`],
    });
  } catch (error) {
    await rm(profile, { recursive: true, force: true });
    throw error;
  }
  const worker = context.serviceWorkers()[0] ?? await context.waitForEvent('serviceworker', { timeout: 30000 });
  assert.equal(new URL(worker.url()).host, extensionId);
  page = await context.newPage();
  observePage(page);
  await page.goto(`chrome-extension://${extensionId}/popup.html?environment=staging`);
  await page.locator('#show-account').waitFor();
  return profile;
}

function observePage(observedPage) {
  observedPage.on('request', async request => {
    const requestUrl = new URL(request.url());
    const requestOrigin = requestUrl.origin;
    if (requestOrigin === PRODUCTION_ORIGIN) {
      evidence.production_requests++;
      if (request.method() !== 'GET' && !['OPTIONS', 'HEAD'].includes(request.method())) {
        evidence.production_writes++;
      }
    }
    if (productionAuthOrigin && requestOrigin === productionAuthOrigin) {
      evidence.production_auth_requests++;
    }
    if (requestOrigin === STAGING_ORIGIN && requestUrl.pathname.startsWith('/api/')) {
      const auth = (await request.allHeaders()).authorization;
      if (auth?.startsWith('Bearer ') && activeAccount) accessTokens.set(activeAccount, auth.slice(7));
    }
  });
  observedPage.on('request', request => { void getCreatedResponse(request); });
}

async function signIn(account, email, password, { invalid = false } = {}) {
  activeAccount = account;
  if (!(await page.locator('#account-panel').isVisible())) await page.locator('#show-account').click();
  await page.locator('#account-sign-in').waitFor({ state: 'visible' });
  await page.locator('#account-email').fill(email);
  await page.locator('#account-password').fill(password);
  await page.locator('#account-sign-in button[type="submit"]').click();
  if (invalid) {
    await page.locator('#account-status[role="alert"]').waitFor({ state: 'visible', timeout: 20000 });
    assert.match(await page.locator('#account-status').textContent(), /invalid|incorrect|not accepted|temporarily unavailable|try again|password|credentials/i);
    evidence.user_experience.authentication_failure = true;
    return;
  }
  await page.locator('#account-sign-out').waitFor({ state: 'visible', timeout: 30000 });
  assert.match(await page.locator('#account-status').textContent(), /signed in/i);
  evidence.product.sign_in = true;
}

async function enterReports() {
  await page.locator('#show-reports').click();
  await page.locator('#personal-reports:not(.hidden)').waitFor({ state: 'visible' });
  await page.locator('#loading').waitFor({ state: 'hidden' });
}

async function waitForAccountToken(account) {
  for (let attempt = 0; attempt < 50 && !accessTokens.has(account); attempt++) {
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  assert.ok(accessTokens.has(account), 'Authenticated staging report request did not expose a session token in memory');
}

async function createReport(subject, owner) {
  await page.locator('#server-create > summary').click();
  await page.locator('#create-subject').fill(subject);
  await page.locator('#create-body').fill(`Synthetic release acceptance message ${owner}. No personal data, credentials, or live message content.`);
  await page.locator('#create-button').click();
  await page.locator('#detail-panel').waitFor({ state: 'visible', timeout: 60000 });
  for (let attempt = 0; attempt < 50 && !createdIds.has(owner); attempt++) {
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  assert.equal(await page.locator('#detail-heading').textContent(), subject);
  await page.locator('#detail-content').getByText(/Automated analysis recorded when saved/i).waitFor({ state: 'visible' });
  assert.ok(createdIds.has(owner), 'Real staging API create response was not observed');
  const analysis = createdAnalysisEvidence.get(owner);
  assert.equal(analysis?.analysis_mode, 'real', 'A mock or unverified model result cannot pass acceptance');
  assert.equal(analysis?.provider_mode, evidence.ai_acceptance.provider);
  assert.equal(analysis?.model_revision, evidence.ai_acceptance.model_revision);
  evidence.user_experience.success = true;
  return createdIds.get(owner);
}

async function getCreatedResponse(request) {
  const requestUrl = new URL(request.url());
  if (request.method() !== 'POST' || requestUrl.origin !== STAGING_ORIGIN
      || requestUrl.pathname !== '/api/analyses') return;
  const response = await request.response().catch(() => null);
  if (!response || response.status() !== 201 || !activeAccount) return;
  try {
    const body = await response.json();
    if (typeof body.id === 'string') {
      createdIds.set(activeAccount, body.id);
      createdAnalysisEvidence.set(activeAccount, {
        analysis_mode: body.analysis_mode,
        provider_mode: body.analysis_provenance?.provider_mode,
        model_revision: body.analysis_provenance?.model_revision,
      });
    }
  } catch { /* response bodies are never copied to evidence */ }
}

async function checkCrossAccountOwnership(accountAId) {
  const bearer = accessTokens.get('b');
  assert.ok(bearer, 'Account B API token was not observed in memory');
  for (const [method, path, data] of [
    ['GET', `/api/analyses/${accountAId}`],
    ['PATCH', `/api/analyses/${accountAId}`, { notes: 'forbidden synthetic cross-account edit' }],
    ['DELETE', `/api/analyses/${accountAId}`],
  ]) {
    const response = await context.request.fetch(STAGING_ORIGIN + path, {
      method,
      headers: { authorization: `Bearer ${bearer}`, ...(data ? { 'content-type': 'application/json' } : {}) },
      data,
      maxRedirects: 0,
      timeout: 15000,
    });
    assert.equal(response.status(), 404, `Cross-account ${method} must return not found`);
  }
  evidence.product.ownership_checks = true;
}

async function testFaultStates() {
  const historyUrl = STAGING_ORIGIN + '/api/analyses';
  await page.route(historyUrl, async route => {
    await new Promise(resolve => setTimeout(resolve, 800));
    await route.continue();
  }, { times: 1 });
  const refresh = page.locator('#load-history').click();
  await page.locator('#loading').waitFor({ state: 'visible' });
  await refresh;
  evidence.user_experience.loading = true;

  await page.route(historyUrl, route => route.fulfill({
    status: 503,
    contentType: 'application/json',
    body: JSON.stringify({ detail: 'Acceptance-only injected service failure' }),
  }), { times: 1 });
  await page.locator('#load-history').click();
  await page.getByText(/Saved reports are temporarily unavailable/i).waitFor({ state: 'visible' });
  evidence.user_experience.api_error = true;

  await page.route(historyUrl, route => route.abort('timedout'), { times: 1 });
  const previousStatus = await page.locator('#crud-status').textContent();
  await page.locator('#load-history').click();
  await page.waitForFunction(previous => {
    const status = document.querySelector('#crud-status');
    return status?.getAttribute('role') === 'alert' && status.textContent !== previous;
  }, previousStatus);
  assert.match(await page.locator('#crud-status').textContent(), /unavailable|failed|network|fetch/i);
  evidence.user_experience.timeout = true;
}

async function deleteCurrentReport(subject) {
  const item = page.locator('#history-list > li').filter({ hasText: subject });
  await item.getByRole('button', { name: `View ${subject}` }).click();
  await page.locator('#detail-panel').waitFor({ state: 'visible' });
  await page.locator('#detail-content').getByRole('button', { name: 'Delete report' }).click();
  await page.locator('#confirm-delete').click();
  await page.getByText('Report deleted.').waitFor();
}

async function cleanupUnfinished() {
  const bearerByAccount = new Map(accessTokens);
  for (const [owner, id] of createdIds) {
    const bearer = bearerByAccount.get(owner);
    if (!bearer) continue;
    await context?.request.delete(`${STAGING_ORIGIN}/api/analyses/${id}`, {
      headers: { authorization: `Bearer ${bearer}` }, maxRedirects: 0, timeout: 10000,
    }).catch(() => {});
  }
}

async function run() {
  let profile;
  try {
    const preflight = await verifyPreflight();
    const aiApproval = preflight.modelApproval;
    const aiApprovalDigest = sha256(Buffer.from(required('STAGING_AI_APPROVAL_JSON')));
    evidence.ai_acceptance.approval_record_sha256 = aiApprovalDigest;
    const model = await verifyService(aiApproval, preflight.sourceSha, preflight.imageDigest);
    const reportProvider = model.provider_mode;
    const reportRevision = model.model_sha256 || model.model;
    assert.equal(reportProvider, aiApproval.provider);
    assert.equal(reportRevision, aiApproval.model_revision);
    evidence.ai_acceptance.provider = reportProvider;
    evidence.ai_acceptance.model_revision = reportRevision;

    profile = await launchExtension(preflight.packagePath, preflight.packageEvidence.chrome_extension_id);
    evidence.phase = 'account-a-auth';
    const emailA = required('STAGING_AUTH_USER_A_EMAIL');
    const passwordA = required('STAGING_AUTH_USER_A_PASSWORD');
    const emailB = required('STAGING_AUTH_USER_B_EMAIL');
    const passwordB = required('STAGING_AUTH_USER_B_PASSWORD');
    await signIn('a', emailA, passwordA + '-incorrect-once', { invalid: true });
    await signIn('a', emailA, passwordA);
    evidence.account_subject_sha256 = { a: subjectHash(emailA.toLowerCase()) };
    await enterReports();
    await waitForAccountToken('a');
    await page.locator('#empty').waitFor({ state: 'visible' });
    const idA = await createReport(`Synthetic release acceptance A ${preflight.sourceSha.slice(0, 8)}`, 'a');
    evidence.product.create = true;
    evidence.product.read = true;
    await page.locator('#back-to-reports').click();
    await page.locator('#history-list').getByText(`Synthetic release acceptance A ${preflight.sourceSha.slice(0, 8)}`).waitFor();
    evidence.product.list = true;
    await page.locator('#history-list').getByRole('button', { name: `View Synthetic release acceptance A ${preflight.sourceSha.slice(0, 8)}` }).click();
    await page.locator('#detail-panel').waitFor({ state: 'visible' });
    await page.locator('#detail-content').getByRole('button', { name: 'Edit notes' }).click();
    await page.locator('#edit-notes').fill('Synthetic verified staging note');
    await page.locator('#save-edit').click();
    await page.getByText('Changes saved successfully.').waitFor();
    evidence.product.update = true;
    await page.close();

    page = await context.newPage();
    observePage(page);
    await page.goto(`chrome-extension://${preflight.packageEvidence.chrome_extension_id}/popup.html?environment=staging`);
    activeAccount = 'a';
    await page.locator('#account-sign-out').waitFor({ state: 'visible' });
    await enterReports();
    await waitForAccountToken('a');
    await page.locator('#history-list').getByText(`Synthetic release acceptance A ${preflight.sourceSha.slice(0, 8)}`).waitFor();
    await page.locator('#history-list').getByRole('button', { name: `View Synthetic release acceptance A ${preflight.sourceSha.slice(0, 8)}` }).click();
    await page.locator('#detail-content').getByText('Synthetic verified staging note', { exact: true }).waitFor();
    evidence.product.persistence_after_reload = true;
    const screenshotPath = path.join(path.dirname(required('STAGING_ACCEPTANCE_OUTPUT')), 'staging-extension-report.png');
    await mkdir(path.dirname(screenshotPath), { recursive: true });
    await page.screenshot({
      path: screenshotPath,
      fullPage: true,
      mask: [page.locator('#account-identity')],
    });

    evidence.phase = 'account-isolation';
    await page.locator('#account-sign-out').click();
    await page.locator('#account-sign-out').waitFor({ state: 'hidden' });
    await signIn('b', emailB, passwordB);
    evidence.account_subject_sha256.b = subjectHash(emailB.toLowerCase());
    assert.notEqual(evidence.account_subject_sha256.a, evidence.account_subject_sha256.b);
    await enterReports();
    await waitForAccountToken('b');
    await page.locator('#empty').waitFor({ state: 'visible' });
    await checkCrossAccountOwnership(idA);
    await page.locator('#history-list').getByText(`Synthetic release acceptance A ${preflight.sourceSha.slice(0, 8)}`).waitFor({ state: 'hidden' });
    evidence.product.user_isolation = true;
    const idB = await createReport(`Synthetic release acceptance B ${preflight.sourceSha.slice(0, 8)}`, 'b');
    await page.locator('#back-to-reports').click();
    await deleteCurrentReport(`Synthetic release acceptance B ${preflight.sourceSha.slice(0, 8)}`);
    evidence.product.delete = true;
    createdIds.delete('b');

    await page.locator('#account-sign-out').click();
    await page.locator('#account-sign-out').waitFor({ state: 'hidden' });
    await signIn('a', emailA, passwordA);
    await enterReports();
    await page.locator('#history-list').getByText(`Synthetic release acceptance A ${preflight.sourceSha.slice(0, 8)}`).waitFor();
    await deleteCurrentReport(`Synthetic release acceptance A ${preflight.sourceSha.slice(0, 8)}`);
    createdIds.delete('a');
    await page.locator('#empty').waitFor({ state: 'visible' });
    evidence.product.cleanup = true;

    evidence.phase = 'fault-injection-ux';
    await testFaultStates();
    assert.equal(evidence.production_requests, 0);
    assert.equal(evidence.production_writes, 0);
    assert.equal(evidence.production_auth_requests, 0);
    evidence.phase = 'complete';
    evidence.status = 'passed';
  } catch {
    evidence.status = 'blocked';
    evidence.failure_code = 'staging_acceptance_incomplete';
  } finally {
    await cleanupUnfinished();
    await context?.close().catch(() => {});
    if (profile) await rm(profile, { recursive: true, force: true }).catch(() => {});
    const output = path.resolve(required('STAGING_ACCEPTANCE_OUTPUT'));
    await mkdir(path.dirname(output), { recursive: true });
    evidence.evidence_path = output;
    await writeFile(output, JSON.stringify(evidence, null, 2) + '\n', { mode: 0o600 });
  }
  if (evidence.status !== 'passed') {
    console.error(`Staging release acceptance blocked at phase ${evidence.phase}. No production data was requested or written.`);
    process.exitCode = 1;
    return;
  }
  console.log(JSON.stringify({
    status: evidence.status,
    source_sha: evidence.source_sha,
    backend_image_digest: evidence.backend_image_digest,
    extension_zip_sha256: evidence.extension_zip_sha256,
    branch_id: evidence.database.branch_id,
    production_requests: evidence.production_requests,
    production_writes: evidence.production_writes,
  }));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) await run();

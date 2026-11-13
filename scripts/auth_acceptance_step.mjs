// One explicitly selected request at a time; planning is the default.
import assert from 'node:assert/strict';
import { mkdir, open, readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const hash = /^[0-9a-f]{64}$/;
export const steps = [
  'list-a-before', 'list-b-before', 'create-a', 'read-a', 'list-a',
  'replay-a', 'list-a-replay', 'conflict-a', 'list-a-conflict',
  'create-b', 'read-b', 'list-b', 'cross-read', 'cross-patch-a', 'cross-delete-a',
  'cross-patch-b', 'cross-delete-b', 'read-a-after-cross',
  'patch-a', 'patch-b', 'read-a-after-patch', 'read-b-after-patch', 'delete-a', 'delete-b',
  'missing-a', 'missing-b', 'list-a-after', 'list-b-after'
];

export function requestSpec(plan, step, executing = false) {
  assert.ok(steps.includes(step), 'Unknown checklist step');
  assert.ok(uuid.test(plan.run_id), 'Set one UUID run_id before planning');
  const cross = /^cross-(read|patch|delete)(?:-([ab]))?$/.exec(step);
  const recordAccount = cross ? (cross[2] || 'a') : step.includes('-b') ? 'b' : 'a';
  const account = cross ? (recordAccount === 'a' ? 'b' : 'a') : recordAccount;
  const id = plan.accounts?.[recordAccount]?.report_id;
  const input = {
    subject: `Synthetic Auth acceptance ${plan.run_id} ${account}`,
    body: 'Synthetic verification message. No personal content or credentials.'
  };
  let method = 'GET', suffix = '', body, status = 200;
  const key = `auth-acceptance-${plan.run_id}`;
  if (/^(create|replay|conflict)-/.test(step)) {
    method = 'POST'; body = input; status = step === 'conflict-a' ? 409 : 201;
    if (step === 'conflict-a') body = { ...input, body: input.body + ' Changed payload.' };
  } else if (!step.startsWith('list-')) {
    if (executing) assert.ok(uuid.test(id || ''), 'Record the exact report ID first');
    suffix = '/' + (id || `{{report_${recordAccount}_id}}`);
    if (step.startsWith('patch-') || step.startsWith('cross-patch-')) {
      assert.equal(plan.include_updates, true, 'PATCH needs explicit inclusion in the approved scope');
      method = 'PATCH'; body = { notes: 'Synthetic acceptance note', feedback: 'false_positive' };
    }
    if (step.startsWith('delete-') || step.startsWith('cross-delete-')) { method = 'DELETE'; status = step.startsWith('cross-') ? 404 : 204; }
    if (step.startsWith('missing-') || step === 'cross-read' || step.startsWith('cross-patch-')) status = 404;
  }
  if (executing && step.startsWith('create-')) assert.equal(id, null, 'Initial save already has a recorded ID');
  return { step, account, method, route: '/api/analyses' + suffix, body,
    idempotency_key: method === 'POST' ? key : undefined, expected_status: status };
}

async function diskJournal(directory, step, initial) {
  assert.ok(path.isAbsolute(directory || ''), 'Use an absolute private evidence directory');
  const relative = path.relative(root, path.resolve(directory));
  assert.ok(relative.startsWith('..' + path.sep) || path.isAbsolute(relative), 'Evidence must be outside the repository');
  await mkdir(directory, { recursive: true, mode: 0o700 });
  const handle = await open(path.join(directory, step + '.json'), 'wx', 0o600);
  const write = async value => {
    await handle.truncate(0);
    await handle.write(JSON.stringify(value, null, 2) + '\n', 0, 'utf8');
    await handle.sync();
  };
  await write(initial);
  return { finish: async value => { try { await write(value); } finally { await handle.close(); } } };
}

export async function runStep(plan, step, { execute = false, allowWrites = false,
  fetchImpl = globalThis.fetch, readToken = file => readFile(file, 'utf8'), journal = diskJournal } = {}) {
  const spec = requestSpec(plan, step, execute);
  if (!execute) return { mode: 'plan-only', ...spec };
  assert.equal(allowWrites, true, 'Execution requires explicit --allow-writes, including authenticated reads');
  assert.ok(plan.authorization_reference?.trim(), 'Record the actual approved scope reference first');
  const start = Date.parse(plan.window_start), end = Date.parse(plan.window_end), now = Date.now();
  assert.ok(Number.isFinite(start) && Number.isFinite(end) && start <= now && now <= end,
    'Outside the explicitly approved execution window');
  assert.ok(plan.target_confirmation_reference?.trim(), 'Record verified Render-to-Neon mapping first');
  assert.ok(plan.application_mappings_preverified === true || plan.allow_mapping_creation === true,
    'Authenticated access can create application mappings; settle that scope first');
  assert.equal(plan.base_url, 'https://phishlens-staging.onrender.com', 'Only the agreed staging origin is permitted');
  assert.ok(/^[0-9a-f]{40}$/.test(plan.backend_sha || ''), 'Pin the full backend SHA');
  assert.ok(hash.test(plan.model_sha || ''), 'Pin the full model hash');
  const a = plan.accounts?.a, b = plan.accounts?.b;
  assert.ok(a?.auth_subject && b?.auth_subject && a.auth_subject !== b.auth_subject,
    'Record two distinct synthetic Auth subjects privately');
  if (step === 'create-b') assert.ok(uuid.test(a.report_id || ''), 'Record account A report before creating B');
  const record = { ...spec, backend_sha: plan.backend_sha, started_at: new Date().toISOString(), outcome: 'pending' };
  // An existing receipt blocks repeating a step, even when its earlier result is uncertain.
  const receipt = await journal(plan.evidence_directory, step, record);
  const request = async (route, init = {}) => {
    const response = await fetchImpl(plan.base_url + route,
      { ...init, redirect: 'error', signal: AbortSignal.timeout(25000), cache: 'no-store' });
    return { status: response.status, body: response.status === 204 ? null : await response.json() };
  };
  let sent = false;
  try {
    const version = await request('/version');
    assert.equal(version.status, 200); assert.equal(version.body.environment, 'staging');
    assert.equal(version.body.commit, plan.backend_sha, 'Deployment changed; stop');
    const ready = await request('/ready');
    assert.equal(ready.status, 200); assert.equal(ready.body.status, 'ready');
    assert.equal(ready.body.database, 'connected');
    const model = await request('/model-info');
    assert.equal(model.status, 200); assert.equal(model.body.provider_mode, 'tfidf');
    assert.equal(model.body.accepts_tfidf_reports, true); assert.equal(model.body.model_sha256, plan.model_sha);
    const anonymous = await request('/api/analyses');
    assert.equal(anonymous.status, 401, 'Auth mode not established; stop before token use');
    const account = plan.accounts[spec.account];
    const token = (await readToken(account.token_file)).trim();
    // This is an account-selection check only. The backend verifies the signature.
    const claims = JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString());
    assert.equal(claims.sub, account.auth_subject, 'Token belongs to a different planned account');
    const headers = { Authorization: 'Bearer ' + token };
    if (spec.body) headers['Content-Type'] = 'application/json';
    if (spec.method === 'POST') {
      headers['Idempotency-Key'] = spec.idempotency_key;
      headers['X-PhishLens-Model'] = plan.model_sha;
    }
    sent = true;
    const response = await request(spec.route, { method: spec.method, headers,
      body: spec.body ? JSON.stringify(spec.body) : undefined });
    record.response = response;
    assert.equal(response.status, spec.expected_status);
    if (/^(create|replay)-/.test(step)) {
      assert.ok(uuid.test(response.body.id || ''));
      assert.equal(response.body.subject, spec.body.subject);
      assert.equal(response.body.analysis_mode, 'real');
      assert.equal(response.body.analysis_provenance?.provider_mode, 'tfidf');
      assert.equal(response.body.analysis_provenance?.model_revision, plan.model_sha);
      if (step === 'replay-a') assert.equal(response.body.id, a.report_id);
      if (step === 'create-b') assert.notEqual(response.body.id, a.report_id);
    }
    if (step === 'conflict-a') assert.equal(response.body.code, 'idempotency_conflict');
    if (step.startsWith('list-')) {
      assert.ok(Array.isArray(response.body.items));
      const expected = /-(before|after)$/.test(step) ? [] : [account.report_id];
      assert.deepEqual(response.body.items.map(x => x.id).sort(), expected.sort());
    }
    if (/^(read|patch)-/.test(step) && !step.startsWith('cross-')) {
      assert.equal(response.body.id, account.report_id);
      if (step.startsWith('patch-')) {
        assert.equal(response.body.notes, spec.body.notes);
        assert.equal(response.body.feedback, spec.body.feedback);
      }
    }
    record.outcome = 'passed';
    await receipt.finish(record);
    return { step, status: response.status, outcome: 'passed', evidence: 'private receipt written' };
  } catch (error) {
    record.outcome = sent ? 'stopped-inspect-state-before-any-replay' : 'stopped-before-account-request';
    // Never put tokens, source claims, server bodies or exception strings in stdout.
    await receipt.finish(record);
    throw new Error('Acceptance stopped; inspect the private receipt and reconcile state before continuing.', { cause: error });
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    const [planFile, step, ...flags] = process.argv.slice(2);
    const plan = JSON.parse(await readFile(planFile, 'utf8'));
    const result = await runStep(plan, step, { execute: flags.includes('--execute'), allowWrites: flags.includes('--allow-writes') });
    console.log(JSON.stringify(result, null, 2));
  } catch {
    console.error('Stopped. Check the private plan/receipt; do not blindly repeat a request.');
    process.exitCode = 1;
  }
}

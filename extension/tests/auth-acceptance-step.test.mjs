import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { requestSpec, runStep } from '../../scripts/auth_acceptance_step.mjs';

const idA = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
const idB = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
const plan = () => ({
  run_id: '11111111-1111-4111-8111-111111111111',
  base_url: 'https://phishlens-staging.onrender.com', backend_sha: 'a'.repeat(40), model_sha: 'b'.repeat(64),
  authorization_reference: 'local fixture only', target_confirmation_reference: 'local fixture only',
  window_start: new Date(Date.now() - 60000).toISOString(), window_end: new Date(Date.now() + 60000).toISOString(),
  allow_mapping_creation: true, evidence_directory: '/private/tmp/unused-fixture',
  accounts: { a: { auth_subject: 'synthetic-a', token_file: 'a', report_id: null },
    b: { auth_subject: 'synthetic-b', token_file: 'b', report_id: null } }
});
const jwt = subject => 'header.' + Buffer.from(JSON.stringify({ sub: subject })).toString('base64url') + '.signature';

function fixture(p, { anonymous = 401, loseCreate = false } = {}) {
  const calls = [], records = [];
  const options = {
    execute: true, allowWrites: true,
    readToken: async alias => jwt('synthetic-' + alias),
    journal: async (_directory, _step, value) => {
      records.push(structuredClone(value));
      return { finish: async final => records.push(structuredClone(final)) };
    },
    fetchImpl: async (url, init) => {
      calls.push({ url, init });
      assert.equal(init.redirect, 'error');
      if (url.endsWith('/version')) return Response.json({ environment: 'staging', commit: p.backend_sha });
      if (url.endsWith('/ready')) return Response.json({ status: 'ready', database: 'connected' });
      if (url.endsWith('/model-info')) return Response.json({ provider_mode: 'tfidf', accepts_tfidf_reports: true, model_sha256: p.model_sha });
      if (!init.headers?.Authorization) return Response.json({ detail: 'Sign in' }, { status: anonymous });
      if (records.length) assert.equal(records[0].outcome, 'pending', 'journal before account request');
      if (loseCreate) throw new Error('private transport failure');
      const input = JSON.parse(init.body || '{}');
      return Response.json({ ...input, id: idA, analysis_mode: 'real',
        analysis_provenance: { provider_mode: 'tfidf', model_revision: p.model_sha } }, { status: 201 });
    }
  };
  return { calls, records, options };
}

test('planning makes no network calls or token reads', async () => {
  const result = await runStep(plan(), 'create-a', {
    fetchImpl: () => assert.fail('network'), readToken: () => assert.fail('token read')
  });
  assert.equal(result.mode, 'plan-only');
  assert.equal(result.expected_status, 201);
});

test('execution requires both explicit flags and authorization/target references', async () => {
  const p = plan(), f = fixture(p);
  await assert.rejects(runStep(p, 'create-a', { ...f.options, allowWrites: false }));
  p.authorization_reference = null;
  await assert.rejects(runStep(p, 'create-a', f.options));
  assert.equal(f.calls.length, 0);
});

test('production and other origins are refused before any request', async () => {
  const p = plan(), f = fixture(p); p.base_url = 'https://phishlens-api-ocvt.onrender.com';
  await assert.rejects(runStep(p, 'create-a', f.options));
  assert.equal(f.calls.length, 0);
});

test('expired authorization window stops before any request', async () => {
  const p = plan(), f = fixture(p);
  p.window_end = new Date(Date.now() - 1).toISOString();
  await assert.rejects(runStep(p, 'create-a', f.options));
  assert.equal(f.calls.length, 0);
});

test('demo mode stops before tokens or writes', async () => {
  const p = plan(), f = fixture(p, { anonymous: 200 });
  f.options.readToken = () => assert.fail('token read in demo mode');
  await assert.rejects(runStep(p, 'create-a', f.options));
  assert.equal(f.calls.filter(x => x.init.method === 'POST').length, 0);
  assert.equal(f.records.at(-1).outcome, 'stopped-before-account-request');
});

test('deployment drift stops at the version read', async () => {
  const p = plan(), f = fixture(p);
  const fetchImpl = async () => Response.json({ environment: 'staging', commit: 'c'.repeat(40) });
  await assert.rejects(runStep(p, 'create-a', { ...f.options, fetchImpl,
    readToken: () => assert.fail('token read after drift') }));
  assert.equal(f.records.at(-1).outcome, 'stopped-before-account-request');
});

test('a token for the other subject never reaches the account endpoint', async () => {
  const p = plan(), f = fixture(p);
  await assert.rejects(runStep(p, 'create-a', { ...f.options, readToken: async () => jwt('synthetic-b') }));
  assert.equal(f.calls.filter(x => x.init.method === 'POST').length, 0);
});

test('one create uses pinned model, private token, deterministic key and durable receipt', async () => {
  const p = plan(), f = fixture(p);
  const result = await runStep(p, 'create-a', f.options);
  assert.equal(result.outcome, 'passed');
  const post = f.calls.at(-1);
  assert.equal(post.init.headers.Authorization, 'Bearer ' + jwt('synthetic-a'));
  assert.equal(post.init.headers['X-PhishLens-Model'], p.model_sha);
  assert.equal(post.init.headers['Idempotency-Key'], requestSpec(p, 'replay-a').idempotency_key);
  assert.equal(JSON.stringify(f.records).includes(jwt('synthetic-a')), false);
  assert.equal(JSON.stringify(result).includes('synthetic-a'), false);
});

test('ambiguous create is never automatically retried and retains reconciliation data', async () => {
  const p = plan(), f = fixture(p, { loseCreate: true });
  await assert.rejects(runStep(p, 'create-a', f.options));
  assert.equal(f.calls.filter(x => x.init.method === 'POST').length, 1);
  assert.equal(f.records.at(-1).outcome, 'stopped-inspect-state-before-any-replay');
  assert.ok(f.records.at(-1).idempotency_key);
  assert.ok(f.records.at(-1).body);
});

test('A replay and conflict and B create share a key; only conflict changes payload', () => {
  const p = plan(); p.accounts.a.report_id = idA;
  const first = requestSpec(p, 'create-a'), replay = requestSpec(p, 'replay-a');
  const conflict = requestSpec(p, 'conflict-a'), second = requestSpec(p, 'create-b');
  assert.deepEqual(first.body, replay.body);
  assert.notDeepEqual(conflict.body, first.body);
  assert.equal(first.idempotency_key, second.idempotency_key);
  assert.equal(conflict.expected_status, 409);
  assert.throws(() => requestSpec(p, 'patch-a'), /approved scope/);
  p.accounts.b.report_id = idB;
  assert.equal(requestSpec(p, 'cross-read').account, 'b');
  assert.equal(requestSpec(p, 'cross-read').route, '/api/analyses/' + idA);
  p.include_updates = true;
  for (const [step, owner, method] of [
    ['cross-patch-a', 'a', 'PATCH'], ['cross-delete-a', 'a', 'DELETE'],
    ['cross-patch-b', 'b', 'PATCH'], ['cross-delete-b', 'b', 'DELETE']
  ]) {
    const spec = requestSpec(p, step);
    assert.equal(spec.account, owner === 'a' ? 'b' : 'a');
    assert.equal(spec.route, '/api/analyses/' + (owner === 'a' ? idA : idB));
    assert.equal(spec.method, method);
    assert.equal(spec.expected_status, 404);
  }
});

test('an existing receipt blocks duplicate execution, with no second network call', async () => {
  const p = plan(), f = fixture(p);
  p.evidence_directory = await mkdtemp(path.join(os.tmpdir(), 'auth-receipt-'));
  const options = { ...f.options };
  delete options.journal;
  try {
    await runStep(p, 'create-a', options);
    const count = f.calls.length;
    await assert.rejects(runStep(p, 'create-a', options));
    assert.equal(f.calls.length, count);
    const receipt = JSON.parse(await readFile(path.join(p.evidence_directory, 'create-a.json'), 'utf8'));
    assert.equal(receipt.response.body.id, idA);
    assert.equal(receipt.outcome, 'passed');
  } finally { await rm(p.evidence_directory, { recursive: true, force: true }); }
});

test('the complete simulated two-account sequence makes only two distinct reports and cleans them', async () => {
  const p = plan(); p.include_updates = true;
  const reports = new Map(), receipts = new Map();
  let initialCreates = 0;
  const options = {
    execute: true, allowWrites: true,
    readToken: async alias => jwt('synthetic-' + alias),
    journal: async (_directory, step, initial) => {
      assert.equal(receipts.has(step), false);
      receipts.set(step, initial);
      return { finish: async final => receipts.set(step, structuredClone(final)) };
    },
    fetchImpl: async (url, init) => {
      const route = new URL(url).pathname;
      if (route === '/version') return Response.json({ environment: 'staging', commit: p.backend_sha });
      if (route === '/ready') return Response.json({ status: 'ready', database: 'connected' });
      if (route === '/model-info') return Response.json({ provider_mode: 'tfidf', accepts_tfidf_reports: true, model_sha256: p.model_sha });
      if (!init.headers?.Authorization) return Response.json({}, { status: 401 });
      const owner = init.headers.Authorization === 'Bearer ' + jwt('synthetic-a') ? 'a' : 'b';
      const id = owner === 'a' ? idA : idB;
      const input = JSON.parse(init.body || '{}');
      if (init.method === 'POST') {
        const existing = reports.get(id);
        if (existing && existing.body !== input.body) return Response.json({ code: 'idempotency_conflict' }, { status: 409 });
        if (!existing) {
          reports.set(id, { ...input, id, owner, analysis_mode: 'real',
            analysis_provenance: { provider_mode: 'tfidf', model_revision: p.model_sha } });
          initialCreates++;
        }
        return Response.json(reports.get(id), { status: 201 });
      }
      if (route === '/api/analyses') return Response.json({ items: [...reports.values()].filter(x => x.owner === owner) });
      const report = reports.get(route.split('/').at(-1));
      if (!report || report.owner !== owner) return Response.json({}, { status: 404 });
      if (init.method === 'PATCH') Object.assign(report, input);
      if (init.method === 'DELETE') { reports.delete(report.id); return new Response(null, { status: 204 }); }
      return Response.json(report);
    }
  };
  const ordered = ['list-a-before', 'list-b-before', 'create-a', 'read-a', 'list-a',
    'replay-a', 'list-a-replay', 'conflict-a', 'list-a-conflict', 'create-b', 'read-b',
    'list-b', 'cross-read', 'cross-patch-a', 'cross-delete-a', 'cross-patch-b',
    'cross-delete-b', 'read-a-after-cross', 'patch-a', 'patch-b',
    'read-a-after-patch', 'read-b-after-patch', 'delete-a', 'delete-b',
    'missing-a', 'missing-b', 'list-a-after', 'list-b-after'];
  for (const step of ordered) {
    assert.equal((await runStep(p, step, options)).outcome, 'passed');
    if (step === 'create-a') p.accounts.a.report_id = receipts.get(step).response.body.id;
    if (step === 'create-b') p.accounts.b.report_id = receipts.get(step).response.body.id;
  }
  assert.equal(initialCreates, 2);
  assert.equal(reports.size, 0);
  assert.equal(receipts.size, ordered.length);
});

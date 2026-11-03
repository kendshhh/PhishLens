// These are software control-flow fixtures, not fabricated benchmark results.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createLocalAnalyzer } from '../ai/local-analyzer.mjs';
import { createWorkflow } from '../ai/live-workflow.mjs';
import { validateJudge, quoteOptions, releaseWorkflow } from '../ai/judge-contract.mjs';
import { createReevaluator } from '../ai/reevaluators.mjs';

const files = async url => new Response(await readFile(new URL(url)));
const analyze = createLocalAnalyzer({ fetchImpl: files });
const primary = await analyze('Team meeting tomorrow at ten. Thank you.');
function response(audit = 'supported', extra = {}) {
  return { ok: true, raw: JSON.stringify({ audit, evidence_id: quoteOptions(primary)[0].id,
    reason_code: audit === 'supported' ? 'protective_or_routine_context' : 'evidence_too_weak',
    missing_context: false, ...extra }), inputTokens: 200, generatedTokens: 40, seedPassed: true };
}
const agreed = () => ['tfidf', 'krr', 'lightgbm'].map(kind => ({ kind, valid: true, alert: primary.alert }));
test('every scan calls the judge and all reevaluators in the required order', async () => {
  const order = [];
  const scan = createWorkflow({ analyze: async () => { order.push('tfidf'); return primary; },
    judge: async () => { order.push('judge'); return response(); },
    evaluateAgain: async () => { order.push('reevaluate'); return agreed(); } });
  for (let i = 0; i < 2; i++) assert.equal((await scan('software fixture')).workflow.released, true);
  assert.deepEqual(order, ['tfidf', 'judge', 'reevaluate', 'tfidf', 'judge', 'reevaluate']);
});
test('a malformed judge still runs reevaluation and releases no reviewed verdict', async () => {
  let reevaluated = false;
  const scan = createWorkflow({ analyze: async () => primary, judge: async () => ({ ok: true, raw: 'bad JSON' }),
    evaluateAgain: async () => { reevaluated = true; return agreed(); } });
  const r = await scan('software fixture'); assert.equal(reevaluated, true);
  assert.equal(r.workflow.status, 'uncertain'); assert.equal(r.alert, null); assert.equal(r.verdict, 'uncertain');
});
test('one dissenting classifier prevents release without changing primary score', async () => {
  const checks = agreed(); checks[1].alert = !primary.alert;
  const judge = validateJudge(response().raw, primary);
  const r = releaseWorkflow(primary, judge, checks);
  assert.equal(r.workflow.released, false); assert.equal(r.score, primary.score);
});
test('quoted evidence, enum rubric and strict schema cannot be forged', () => {
  for (const extra of [{ evidence_id: 'fake' }, { extra: true }, { missing_context: true }, { reason_code: 'request_needs_verification' }]) {
    assert.throws(() => validateJudge(response('supported', extra).raw, primary));
  }
});
test('compact judge output expands to complete English without changing its audit', () => {
  const r = validateJudge(JSON.stringify({ q: quoteOptions(primary)[0].id, r: 'R' }), primary);
  assert.equal(r.audit, 'supported'); assert.match(r.reason, /routine or protective/);
  assert.throws(() => validateJudge(JSON.stringify({ q: 'q0', r: 'P' }), primary));
  const uncertain = validateJudge(JSON.stringify({ q: 'q0', r: 'M' }), primary);
  assert.equal(uncertain.audit, 'uncertain'); assert.equal(uncertain.missing_context, true);
  const unsupported = validateJudge(JSON.stringify({ q: 'q0', r: 'W' }), primary);
  assert.equal(unsupported.audit, 'unsupported');
  assert.throws(() => validateJudge(JSON.stringify({ a: 's', q: 'q0', r: 'W' }), primary));
});
test('cancellation before judge start performs no further model calls', async () => {
  let called = false;
  const scan = createWorkflow({ analyze: async () => primary, judge: async () => { called = true; }, evaluateAgain: async () => [] });
  await assert.rejects(scan('software fixture', { isCurrent: () => false }), /cancelled/);
  assert.equal(called, false);
});
test('real auxiliary artifacts return three finite locally computed outputs', async () => {
  const reevaluate = createReevaluator({ fetchImpl: files, getBasis: () => analyze.getAssets() });
  const rows = await reevaluate(primary);
  assert.deepEqual(rows.map(r => r.kind), ['tfidf', 'krr', 'lightgbm']);
  for (const r of rows) { assert.equal(r.valid, true); assert.ok(Number.isFinite(r.raw_margin)); assert.ok(r.score >= 0 && r.score <= 1); }
});

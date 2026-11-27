import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { retrieveGuidance, RETRIEVAL_CORPUS_VERSION } from '../ai/retrieval.mjs';
import { buildJudgePayload } from '../ai/judge-contract.mjs';
import { createWorkflow } from '../ai/live-workflow.mjs';
import { createLocalAnalyzer } from '../ai/local-analyzer.mjs';
import { quoteOptions } from '../ai/judge-contract.mjs';

const fetchLocal = async url => new Response(await readFile(new URL(url)));

test('local BM25 retrieves relevant guidance deterministically and returns source ids', () => {
  const query = 'Your account will close. Confirm your password at this link to keep access.';
  const first = retrieveGuidance(query);
  const second = retrieveGuidance(query);
  assert.deepEqual(first, second);
  assert.equal(first.version, RETRIEVAL_CORPUS_VERSION);
  assert.ok(first.documents.length > 0);
  assert.ok(first.documents.some(item => item.id === 'credentials-and-codes' || item.id === 'links-and-attachments'));
  assert.ok(first.documents.every(item => item.score > 0 && item.text.length < 500));
});

test('empty or unrelated text produces no fabricated retrieval citations', () => {
  assert.deepEqual(retrieveGuidance(''), { version: RETRIEVAL_CORPUS_VERSION, query_terms: 0, documents: [] });
  assert.deepEqual(retrieveGuidance('zqxv blorf quux'), { version: RETRIEVAL_CORPUS_VERSION, query_terms: 3, documents: [] });
  assert.throws(() => retrieveGuidance('payment', { limit: 0 }), /limits/);
});

test('judge payload contains bounded local passages while email quotes remain email-only', () => {
  const primary = { alert: true, analysis_text: 'Confirm your password at this link.',
    evidence: [{ quote: 'Confirm your password', type: 'sensitive' }],
    local_guidance: retrieveGuidance('Confirm your password at this link.') };
  const payload = buildJudgePayload(primary);
  assert.equal(payload.text, primary.analysis_text);
  assert.equal(payload.local_guidance.length, primary.local_guidance.documents.length);
  assert.ok(payload.local_guidance.every(({ id, title, text }) => id && title && text));
  assert.ok(payload.quotes.every(quote => primary.analysis_text.includes(quote.quote)));
});

test('workflow gives retrieved context to the local judge and records its provenance without changing TF-IDF score', async () => {
  const analyze = createLocalAnalyzer({ fetchImpl: fetchLocal });
  const primary = await analyze('Your account will close today. Confirm your password at https://account-check.example/verify to keep access.');
  let judgeInput;
  const judge = async input => {
    judgeInput = input;
    const evidence = quoteOptions(primary)[0];
    return { ok: true, raw: JSON.stringify({ r: 'P', q: evidence.id }), seedPassed: true };
  };
  const reevaluate = async p => ['tfidf', 'krr', 'lightgbm'].map(kind => ({ kind, valid: true, alert: p.alert }));
  const result = await createWorkflow({ analyze: async () => primary, judge, evaluateAgain: reevaluate })('fixture');
  assert.equal(judgeInput.local_guidance.version, RETRIEVAL_CORPUS_VERSION);
  assert.ok(judgeInput.local_guidance.documents.length > 0);
  assert.equal(result.score, primary.score);
  assert.equal(result.workflow.judge.retrieval.status, 'retrieved');
  assert.deepEqual(result.workflow.judge.retrieval.sources.map(s => s.id), judgeInput.local_guidance.documents.map(d => d.id));
  assert.equal(result.workflow.released, true);
});

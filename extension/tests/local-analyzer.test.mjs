import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createLocalAnalyzer, MODEL_SHA256 } from '../ai/local-analyzer.mjs';
import { mapScore } from '../ai/core.mjs';

const base = new URL('../ai/', import.meta.url);
const files = async url => new Response(await readFile(new URL(url)));
test('real artifact, protected wording, exact quotes and frozen threshold', async () => {
  const analyze = createLocalAnalyzer({ fetchImpl: files });
  const result = await analyze('Your verification code is 123456. Do not share your password or code.');
  assert.equal(result.model_sha256, MODEL_SHA256);
  assert.equal(result.alert, result.raw_margin >= 0);
  assert.ok(Math.abs(result.alert_threshold_score - .887126047083381) < 1e-14);
  assert.ok(Math.abs(result.attribution_sum - result.raw_margin) < 1e-12);
  for (const e of [...result.evidence, ...result.model_drivers]) {
    assert.equal(result.analysis_text.slice(e.start, e.end), e.quote);
  }
  assert.doesNotMatch(JSON.stringify(result.evidence), /123456/);
  assert.ok(result.evidence.some(e => e.type === 'protective'));
});
test('scores between 50% and 88.71% remain below frozen cutoff', () => {
  const mapping = { kind: 'margin_sigmoid', slope: 1.6158795082744162, intercept: 2.0617153419475205 };
  const p = mapScore(-.5, mapping);
  assert.ok(p > .5 && p < mapScore(0, mapping));
});
test('only packaged asset URLs are read and concurrent calls share one load', async () => {
  const requests = [];
  const analyze = createLocalAnalyzer({ fetchImpl: async url => { requests.push(url); return files(url); } });
  await Promise.all([analyze('Meeting agenda for the team.'), analyze('Please review the account notice.')]);
  assert.deepEqual(requests.sort(), [new URL('contract.json', base).href, new URL('tfidf_v12a.json', base).href].sort());
});
test('corruption never yields a verdict; failed model load can retry', async () => {
  let corrupt = true;
  const analyze = createLocalAnalyzer({ fetchImpl: url => corrupt && url.endsWith('tfidf_v12a.json') ?
    Promise.resolve(new Response('{}')) : files(url) });
  await assert.rejects(analyze('Meeting agenda'), /integrity/);
  corrupt = false; assert.equal((await analyze('Meeting agenda')).valid, true);
});
test('changed display mapping is rejected even with original weights', async () => {
  const analyze = createLocalAnalyzer({ fetchImpl: async url => {
    if (!url.endsWith('contract.json')) return files(url);
    const c = JSON.parse(await readFile(new URL(url))); c.mapping.slope = 1;
    return Response.json(c);
  } });
  await assert.rejects(analyze('Meeting agenda'), /integrity/);
});
test('empty, raw HTML, oversize and out-of-vocabulary inputs fail explicitly', async () => {
  const analyze = createLocalAnalyzer({ fetchImpl: files });
  for (const input of ['', '  ', '<html><body>account</body></html>', 'x'.repeat(30001), '🔒⚠️']) {
    await assert.rejects(analyze(input));
  }
});
test('shared first 2000 plus last 300 truncation survives integration', async () => {
  const analyze = createLocalAnalyzer({ fetchImpl: files });
  const r = await analyze('Meeting agenda ' + 'a'.repeat(2500) + ' end of meeting');
  assert.equal(r.input_truncated, true); assert.equal(Array.from(r.analysis_text).length, 2300);
  assert.ok(r.analysis_text.endsWith(' end of meeting'));
});
test('Unicode case expansion never presents a mismatched word-feature quote', async () => {
  const analyze = createLocalAnalyzer({ fetchImpl: files });
  const r = await analyze('İSTANBUL meeting tomorrow with team. Please check your account.');
  for (const d of r.model_drivers) {
    assert.equal((d.quote.toLowerCase().match(/[\p{L}\p{N}_]{2,}/gu) || []).join(' '), d.feature);
  }
});

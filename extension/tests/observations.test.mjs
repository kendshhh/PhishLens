// Software regression fixtures; these are not an accuracy dataset.
import test from 'node:test';
import assert from 'node:assert/strict';
import { observations } from '../ai/observations.mjs';
import { createLocalAnalyzer } from '../ai/local-analyzer.mjs';
import { readFile } from 'node:fs/promises';

test('pressure cannot borrow an action cue from another sentence or clause', () => {
  for (const boundary of ['. ', '! ', '? ', '; ', '\n']) {
    for (const text of [
      'Your account is locked' + boundary + 'Please confirm the meeting agenda.',
      'Please confirm the meeting agenda' + boundary + 'Your account is locked.'
    ]) {
      assert.equal(observations(text).some(e => e.type === 'pressure'), false, text);
    }
  }
});

test('pressure evidence quotes the connected action and consequence in the same clause', () => {
  const text = 'Your account will be locked unless you verify your details.';
  const evidence = observations(text).find(e => e.type === 'pressure');
  assert.ok(evidence);
  assert.match(evidence.quote, /account.*locked.*verify/i);
  assert.equal(text.slice(evidence.start, evidence.end), evidence.quote);
});

test('negated account consequences and reported phishing examples are not pressure evidence', () => {
  for (const text of [
    'Your account will not be locked unless you confirm an unexpected request.',
    'Phishing training: your account will be locked unless you verify it.'
  ]) assert.equal(observations(text).some(e => e.type === 'pressure'), false);
});

test('the actual scan adapter does not join unrelated sentence evidence', async () => {
  const analyze = createLocalAnalyzer({ fetchImpl: async url => new Response(await readFile(new URL(url))) });
  const result = await analyze('Your account is locked. Please confirm the meeting agenda.');
  assert.equal(result.valid, true);
  assert.equal(result.evidence.some(e => e.type === 'pressure'), false);
});

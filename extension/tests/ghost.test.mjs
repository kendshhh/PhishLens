import test from 'node:test';
import assert from 'node:assert/strict';
import { inspectText, moodFor } from '../js/ghost.js';

test('the ghost stays calm for ordinary text', () => {
  assert.equal(moodFor(inspectText('Hi team, the meeting moved to 3pm tomorrow.')), 'calm');
  assert.equal(moodFor(inspectText('')), 'calm');
  assert.equal(moodFor(inspectText(undefined)), 'calm');
});

test('a single phishing cue makes the ghost curious', () => {
  const found = inspectText('Kindly see the notes below.');
  assert.deepEqual(found.cues, ['kindly']);
  assert.equal(moodFor(found), 'curious');
});

test('several cues or a red-flag request make the ghost shocked', () => {
  const phishy = inspectText('Dear customer, your account will be suspended unless you verify your account immediately.');
  assert.ok(phishy.cues.length >= 2);
  assert.equal(moodFor(phishy), 'shocked');
  const secret = inspectText('Please send me your password.');
  assert.deepEqual(secret.flags, ['sensitive']);
  assert.equal(moodFor(secret), 'shocked');
});

test('an alerting result shocks the ghost even without cues', () => {
  assert.equal(moodFor({ cues: [], flags: [] }, { alert: true }), 'shocked');
});

test('cues match whole words only', () => {
  assert.deepEqual(inspectText('The unblocked lockedin prizes').cues, []);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import { classify, linkedNumbers } from '../auto_labels.mjs';

test('issue title assigns type, scope and explicit sprint', () => {
  assert.deepEqual(classify({ title: 'feat (s2-t1): implement backend endpoints' }),
    ['area: api', 'area: backend', 'enhancement', 'sprint-2']);
});
test('template checklist does not label every component', () => {
  assert.deepEqual(classify({ title: 'docs: update guide', body: 'Backend, extension, staging integration checks pass.' }),
    ['documentation']);
});
test('PR paths and linked issues supply areas and sprint without copying status or priority', () => {
  const labels = classify({ title: 'fix: handle failures' },
    ['backend/app/ai/provider.py', 'backend/tests/test_provider.py'],
    [{ labels: [{ name: 'sprint-2' }, { name: 'area: api' }, { name: 'priority:P0' }, { name: 'carryover' }] }]);
  assert.deepEqual(labels, ['area: ai', 'area: api', 'area: backend', 'area: testing', 'bug', 'sprint-2']);
});
test('arbitrary titles get a type but no guessed sprint or priority', () => {
  assert.deepEqual(classify({ title: 'Improve things' }), ['enhancement']);
});
test('priority requires an explicit declaration', () => {
  assert.ok(classify({ title: 'fix: priority:P1 timeout' }).includes('priority:P1'));
  assert.ok(!classify({ title: 'fix: P0 timeout' }).includes('priority:P0'));
});
test('only explicit local issue relationships are inherited', () => {
  assert.deepEqual(linkedNumbers('Related to #42 and #43.\nCloses https://github.com/kendshhh/PhishLens/issues/44\nSee #9\nFixes https://github.com/other/repo/issues/77', 'kendshhh/PhishLens'), [42, 43, 44]);
});

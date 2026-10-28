import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { classify, linkedNumbers, runLabeler } from '../auto_labels.mjs';

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

test('GitHub 403 skips optional labeling without failing CI', async () => {
  const directory = mkdtempSync(join(tmpdir(), 'phishlens-label-test-'));
  const eventPath = join(directory, 'event.json');
  const summaryPath = join(directory, 'summary.md');
  try {
    writeFileSync(eventPath, JSON.stringify({ issue: { number: 42 } }));
    const result = await runLabeler({
      env: {
        GITHUB_REPOSITORY: 'kendshhh/PhishLens',
        GITHUB_TOKEN: 'test-token',
        GITHUB_EVENT_PATH: eventPath,
        GITHUB_STEP_SUMMARY: summaryPath
      },
      fetchImpl: async () => ({ ok: false, status: 403 })
    });

    assert.deepEqual(result, { skipped: true, reason: 'github-api-forbidden' });
    assert.match(readFileSync(summaryPath, 'utf8'), /no labels were changed/);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test('issue webhook data avoids a redundant issue API read', async () => {
  const directory = mkdtempSync(join(tmpdir(), 'phishlens-label-test-'));
  const eventPath = join(directory, 'event.json');
  const calls = [];
  try {
    writeFileSync(eventPath, JSON.stringify({ issue: { number: 42, title: 'fix: a defect', body: '', labels: [] } }));
    const result = await runLabeler({
      env: {
        GITHUB_REPOSITORY: 'kendshhh/PhishLens',
        GITHUB_TOKEN: 'test-token',
        GITHUB_EVENT_PATH: eventPath
      },
      fetchImpl: async (url, init) => {
        calls.push({ url, init });
        return { ok: true, json: async () => init.method === 'POST' ? [] : [{ name: 'bug' }] };
      }
    });

    assert.deepEqual(result, { skipped: false, additions: ['bug'] });
    assert.equal(calls.length, 2);
    assert.match(calls[0].url, /\/labels\?/);
    assert.match(calls[1].url, /\/issues\/42\/labels$/);
    assert.equal(calls[1].init.method, 'POST');
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test('403 on a read retries anonymously while label writes keep the token', async () => {
  const directory = mkdtempSync(join(tmpdir(), 'phishlens-label-test-'));
  const eventPath = join(directory, 'event.json');
  const calls = [];
  try {
    writeFileSync(eventPath, JSON.stringify({ issue: { number: 42, title: 'fix: a defect', body: '', labels: [] } }));
    const result = await runLabeler({
      env: {
        GITHUB_REPOSITORY: 'kendshhh/PhishLens',
        GITHUB_TOKEN: 'test-token',
        GITHUB_EVENT_PATH: eventPath
      },
      fetchImpl: async (url, init) => {
        calls.push({ url, init });
        if (calls.length === 1) return { ok: false, status: 403 };
        return { ok: true, json: async () => init.method === 'POST' ? [] : [{ name: 'bug' }] };
      }
    });

    assert.deepEqual(result, { skipped: false, additions: ['bug'] });
    assert.equal(calls.length, 3);
    assert.equal(calls[1].init.headers.Authorization, undefined);
    assert.equal(calls[2].init.headers.Authorization, 'Bearer test-token');
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

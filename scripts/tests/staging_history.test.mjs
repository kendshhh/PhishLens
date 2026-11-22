import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { waitForHistoryEndpoint } from '../staging_history.mjs';

const record = {
  id: '29d80c39-ec0d-4db8-a6e5-87444ba2600c',
  subject: 'Staging history integration check',
  prediction: 'phishing',
  confidence: 0.93,
  risk_level: 'high',
  threat_indicators: [],
  explanation: 'Synthetic test record',
  created_at: '2026-10-14T04:00:00Z',
};

async function serve(t, handler) {
  const server = createServer(handler);
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise(resolve => {
    server.closeAllConnections();
    server.close(resolve);
  }));
  return `http://127.0.0.1:${server.address().port}`;
}

test('staging history check waits through a transient outage after readiness', async t => {
  let calls = 0;
  const baseUrl = await serve(t, (request, response) => {
    assert.equal(request.url, '/api/analyses');
    calls++;
    if (calls === 1) {
      response.writeHead(503, { 'Content-Type': 'application/json' });
      response.end(JSON.stringify({ detail: 'database is starting' }));
      return;
    }
    response.writeHead(200, { 'Content-Type': 'application/json' });
    response.end(JSON.stringify({ items: [record] }));
  });

  const result = await waitForHistoryEndpoint(baseUrl, {
    attempts: 3,
    delayMs: 5,
    timeoutMs: 1000,
  });

  assert.equal(result.status, 200);
  assert.equal(result.attempt, 2);
  assert.deepEqual(result.items, [record]);
  assert.equal(calls, 2);
});

test('staging history check returns a 401 for the Bearer challenge assertion', async t => {
  const baseUrl = await serve(t, (_request, response) => {
    response.writeHead(401, {
      'Content-Type': 'application/json',
      'WWW-Authenticate': 'Bearer',
    });
    response.end(JSON.stringify({ detail: 'Sign in required' }));
  });

  const result = await waitForHistoryEndpoint(baseUrl, {
    attempts: 2,
    delayMs: 5,
    timeoutMs: 1000,
  });

  assert.equal(result.status, 401);
  assert.equal(result.error.wwwAuthenticate, 'Bearer');
  assert.equal(result.error.category, 'authentication_authorization');
});

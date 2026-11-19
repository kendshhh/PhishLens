import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { once } from 'node:events';
import { webBuildConfig, deploymentConfig } from '../../scripts/web_build_config.mjs';
import { createPreviewServer } from '../../scripts/serve_web.mjs';

const sha = 'a'.repeat(40);
test('web release rejects cross-environment, arbitrary, credentialed and unpinned account targets', () => {
  for (const env of [
    { PHISHLENS_WEB_ENV: 'unknown' },
    { PHISHLENS_WEB_API_ORIGIN: 'https://other.test' },
    { PHISHLENS_WEB_ENV: 'staging', PHISHLENS_WEB_API_ORIGIN: 'https://phishlens-api-ocvt.onrender.com' },
    { PHISHLENS_WEB_API_ORIGIN: 'https://secret@phishlens-api-ocvt.onrender.com' },
    { PHISHLENS_WEB_API_ORIGIN: 'https://phishlens-api-ocvt.onrender.com/path' },
    { PHISHLENS_WEB_AUTH_URL: 'https://ep-test.neonauth.c-4.ap-southeast-1.aws.neon.tech/neondb/auth' },
    { PHISHLENS_WEB_AUTH_URL: 'https://attacker.test/neondb/auth', PHISHLENS_WEB_BACKEND_SHA: sha },
    { PHISHLENS_WEB_BACKEND_SHA: 'short' },
    { PHISHLENS_WEB_ENV: 'development', PHISHLENS_WEB_API_ORIGIN: 'http://192.0.2.1' },
    { PHISHLENS_WEB_ENV: 'development', PHISHLENS_WEB_API_ORIGIN: 'http://127.0.0.1', VERCEL: '1' }
  ]) assert.throws(() => webBuildConfig(env));
});

test('account-enabled release names only one verified public Auth origin and a fixed API destination', () => {
  const config = webBuildConfig({ PHISHLENS_WEB_ENV: 'staging', PHISHLENS_WEB_BACKEND_SHA: sha,
    PHISHLENS_WEB_AUTH_URL: 'https://ep-test.neonauth.c-4.ap-southeast-1.aws.neon.tech/neondb/auth' });
  const routes = deploymentConfig(config).routes;
  assert.equal(config.requiredReportAuthMode, 'neon');
  assert.equal(config.expectedBackendSha, sha);
  assert.equal(config.database, 'neondb');
  const csp = routes[0].headers['Content-Security-Policy'];
  assert.match(csp, /connect-src 'self' https:\/\/ep-test\.neonauth/);
  assert.ok(!csp.includes('unsafe-inline') && !csp.includes('*'));
  assert.equal(routes[1].dest, 'https://phishlens-staging.onrender.com$1');
  assert.equal(routes[1].headers['Cache-Control'], 'no-store');
  assert.deepEqual(routes[1].transforms.map(t => [t.type, t.target.key]),
    [['request.headers', 'cookie'], ['response.headers', 'set-cookie']]);
  for (const url of ['/api/admin', '/api/analyses/../../admin', '/api/analyses//evil.test', '/backend/secrets']) {
    assert.ok(!routes.some(r => r.dest && new RegExp(r.src).test(url)));
  }
  assert.equal(webBuildConfig({}).authUrl, null);
});

test('preview proxies real loopback HTTP with bearer and body, strips cookies and prevents open routes', async t => {
  const seen = [];
  const api = createServer(async (req, res) => {
    let body = ''; for await (const chunk of req) body += chunk;
    seen.push({ url: req.url, headers: req.headers, body });
    res.writeHead(201, { 'Content-Type': 'application/json', 'Set-Cookie': 'internal=secret' });
    res.end('{"ok":true}');
  }).listen(0, '127.0.0.1');
  await once(api, 'listening');
  const config = deploymentConfig(webBuildConfig({ PHISHLENS_WEB_ENV: 'development',
    PHISHLENS_WEB_API_ORIGIN: `http://127.0.0.1:${api.address().port}` }));
  const preview = createPreviewServer(config).listen(0, '127.0.0.1');
  await once(preview, 'listening');
  t.after(() => { preview.closeAllConnections(); preview.close(); api.closeAllConnections(); api.close(); });
  const base = `http://127.0.0.1:${preview.address().port}`;
  const response = await fetch(base + '/api/analyses?limit=1', { method: 'POST',
    headers: { Authorization: 'Bearer synthetic-token', Cookie: 'browser=private',
      'Content-Type': 'application/json', 'X-Require-Auth-Mode': 'neon' }, body: '{"body":"Synthetic"}' });
  assert.equal(response.status, 201);
  assert.equal(response.headers.get('set-cookie'), null);
  assert.equal(response.headers.get('cache-control'), 'no-store');
  assert.equal(seen[0].headers.authorization, 'Bearer synthetic-token');
  assert.equal(seen[0].headers.cookie, undefined);
  assert.equal(seen[0].headers['x-require-auth-mode'], 'neon');
  assert.equal(seen[0].body, '{"body":"Synthetic"}');
  assert.equal(seen[0].url, '/api/analyses?limit=1');
  assert.equal((await fetch(base + '/backend/secrets')).status, 404);
  assert.equal((await fetch(base + '/backend/health', { method: 'POST' })).status, 405);
  assert.equal(seen.length, 1);
});

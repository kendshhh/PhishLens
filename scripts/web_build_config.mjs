// Public build settings only. No token, key, database URL or password is read.
const API_ORIGINS = Object.freeze({ production: 'https://phishlens-api-ocvt.onrender.com',
  staging: 'https://phishlens-staging.onrender.com' });
const COMMIT = /^[a-f0-9]{40}$/;

export function webBuildConfig(env = process.env) {
  const environment = env.PHISHLENS_WEB_ENV || 'production';
  if (!['production', 'staging', 'development'].includes(environment)) throw new Error('Invalid web environment');
  if (environment === 'development' && env.VERCEL) throw new Error('A localhost development build cannot be deployed');
  const apiOrigin = env.PHISHLENS_WEB_API_ORIGIN || API_ORIGINS[environment];
  let api;
  try { api = new URL(apiOrigin); } catch { throw new Error('A valid web API origin is required'); }
  if (api.username || api.password || api.search || api.hash || api.pathname !== '/') throw new Error('API configuration must be an origin');
  if (environment === 'development') {
    if (api.protocol !== 'http:' || !['localhost', '127.0.0.1', '[::1]'].includes(api.hostname)) {
      throw new Error('Development API must be loopback HTTP');
    }
  } else if (api.origin !== API_ORIGINS[environment]) throw new Error('API does not match the selected environment');
  let authUrl = null, database = null;
  if (env.PHISHLENS_WEB_BACKEND_SHA && !COMMIT.test(env.PHISHLENS_WEB_BACKEND_SHA)) {
    throw new Error('Backend SHA must contain 40 lowercase hexadecimal characters');
  }
  if (env.PHISHLENS_WEB_AUTH_URL) {
    let auth;
    try { auth = new URL(env.PHISHLENS_WEB_AUTH_URL); } catch { throw new Error('Invalid public Auth URL'); }
    const hostAllowed = /^[a-z0-9-]+\.neonauth\.c-\d+\.[a-z0-9-]+\.aws\.neon\.tech$/.test(auth.hostname)
      || (environment === 'development' && auth.hostname.endsWith('.test'));
    const match = /^\/([a-zA-Z0-9_-]{1,63})\/auth$/.exec(auth.pathname);
    if (auth.protocol !== 'https:' || auth.username || auth.password || auth.search || auth.hash || !hostAllowed || !match) {
      throw new Error('Auth must be an HTTPS Neon database Auth URL');
    }
    if (!COMMIT.test(env.PHISHLENS_WEB_BACKEND_SHA || '')) throw new Error('Auth build requires the approved full backend SHA');
    authUrl = auth.href; database = match[1];
  }
  return { environment, apiOrigin: api.origin, authUrl, database,
    expectedBackendSha: env.PHISHLENS_WEB_BACKEND_SHA || null,
    requiredReportAuthMode: authUrl ? 'neon' : null };
}

export function deploymentConfig(config) {
  const authOrigin = config.authUrl ? ' ' + new URL(config.authUrl).origin : '';
  const headers = {
    'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'" +
      authOrigin + "; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'",
    'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer',
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=()', 'Cache-Control': 'no-cache'
  };
  const noCookies = [
    { type: 'request.headers', op: 'delete', target: { key: 'cookie' } },
    { type: 'response.headers', op: 'delete', target: { key: 'set-cookie' } }
  ];
  return { version: 3, routes: [
    { src: '/.*', headers, continue: true },
    { src: '^(/api/analyses(?:/[a-fA-F0-9-]{36})?)$', dest: config.apiOrigin + '$1',
      methods: ['GET', 'POST', 'PATCH', 'DELETE', 'OPTIONS'],
      headers: { 'Cache-Control': 'no-store' }, transforms: noCookies },
    { src: '^/backend/(health|ready|version|model-info)$', dest: config.apiOrigin + '/$1',
      methods: ['GET'], headers: { 'Cache-Control': 'no-store' }, transforms: noCookies },
    { handle: 'filesystem' }
  ] };
}

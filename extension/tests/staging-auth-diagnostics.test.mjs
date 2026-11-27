import assert from 'node:assert/strict';
import test from 'node:test';
import { authEndpointName, authResponseEvidence, extractProviderErrorCode } from '../../scripts/staging_auth_diagnostics.mjs';

test('labels only known Auth endpoints and never returns an arbitrary path', () => {
  assert.equal(authEndpointName('/api/auth/sign-in/email'), 'sign_in');
  assert.equal(authEndpointName('/api/auth/get-session'), 'get_session');
  assert.equal(authEndpointName('/api/auth/sign-out'), 'sign_out');
  assert.equal(authEndpointName('/api/auth/custom/path/with-user-data'), 'other');
  assert.equal(authEndpointName('/api/analyses'), 'other');
});

test('keeps only allowlisted provider codes in acceptance evidence', () => {
  assert.equal(extractProviderErrorCode({ code: 'INVALID_EMAIL_OR_PASSWORD' }), 'INVALID_EMAIL_OR_PASSWORD');
  assert.equal(extractProviderErrorCode({ error_code: 'email_not_verified' }), 'EMAIL_NOT_VERIFIED');
  assert.equal(extractProviderErrorCode({ errorCode: 'SESSION_NOT_FOUND' }), 'SESSION_NOT_FOUND');
  assert.equal(extractProviderErrorCode({ code: 'user@example.test' }), null);
  assert.equal(extractProviderErrorCode({ message: 'INVALID_EMAIL_OR_PASSWORD' }), null);
  assert.equal(extractProviderErrorCode({ code: 'raw provider response with credentials' }), null);
  assert.equal(extractProviderErrorCode('INVALID_EMAIL_OR_PASSWORD'), null);
});

test('acceptance evidence includes only an allowlisted provider error code', () => {
  const evidence = authResponseEvidence({
    service: 'neon-auth',
    route: '/sign-in/email',
    status: 401,
    payload: {
      code: 'invalid_credentials',
      message: 'account-a@example.test raw provider detail',
    },
  });
  assert.deepEqual(evidence, {
    service: 'neon-auth',
    route: '/sign-in/email',
    status: 401,
    provider_error_code: 'INVALID_CREDENTIALS',
  });
  assert.equal(JSON.stringify(evidence).includes('account-a@example.test'), false);

  const unknown = authResponseEvidence({
    service: 'neon-auth',
    route: '/sign-in/email',
    status: 401,
    payload: { code: 'account-a@example.test', message: 'raw provider detail' },
  });
  assert.equal(unknown.provider_error_code, null);
  assert.equal(JSON.stringify(unknown).includes('raw provider detail'), false);
});

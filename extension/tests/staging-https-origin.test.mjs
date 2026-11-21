import test from 'node:test';
import assert from 'node:assert/strict';
import { requireHttpsOrigin } from '../../scripts/https_origin.mjs';

test('accepts HTTPS Auth URLs and returns the exact parsed origin', () => {
  assert.equal(
    requireHttpsOrigin('https://auth.example.net/v1/auth?tenant=staging', 'Auth URL'),
    'https://auth.example.net',
  );
});

test('rejects an HTTP URL', () => {
  assert.throws(
    () => requireHttpsOrigin('http://auth.example.net', 'Auth URL'),
    /absolute HTTPS URL/,
  );
});

test('rejects malformed URLs and URLs containing credentials', () => {
  assert.throws(() => requireHttpsOrigin('/relative/auth', 'Auth URL'), /absolute HTTPS URL/);
  assert.throws(
    () => requireHttpsOrigin('https://user:password@auth.example.net', 'Auth URL'),
    /without credentials/,
  );
});

test('keeps a hostname suffix as a distinct origin instead of accepting a string prefix', () => {
  assert.equal(
    requireHttpsOrigin('https://auth.example.net.attacker.invalid', 'Auth URL'),
    'https://auth.example.net.attacker.invalid',
  );
});

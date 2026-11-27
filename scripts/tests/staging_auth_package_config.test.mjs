import assert from 'node:assert/strict';
import test from 'node:test';

import { readStagingAuthConfig } from '../staging_auth_package_config.mjs';

test('reads the generated JavaScript Auth configuration object literal', () => {
  const config = {
    enabled: true,
    authUrl: 'https://auth.example.test/neondb/auth',
    database: 'neondb',
    apiOrigin: 'https://api.example.test',
    transport: 'https-bridge',
    bridgeUrl: 'https://api.example.test/auth/bridge'
  };
  const source = 'export const AUTH_CONFIGS = Object.freeze({production:null,staging:' +
    JSON.stringify(config) +
    '});\nexport const AUTH_CONFIG = AUTH_CONFIGS.staging;\n';

  const actual = readStagingAuthConfig(source);

  assert.equal(actual.enabled, true);
  assert.equal(actual.authUrl, config.authUrl);
  assert.equal(actual.database, 'neondb');
  assert.equal(actual.transport, 'https-bridge');
  assert.equal(actual.bridgeUrl, config.bridgeUrl);
});

test('accepts the generated Auth-disabled staging map', () => {
  const source = 'export const AUTH_CONFIGS = Object.freeze({production:null,staging:null});\n' +
    'export const AUTH_CONFIG = AUTH_CONFIGS.staging;\n';
  assert.equal(readStagingAuthConfig(source), null);
});

test('rejects exports that do not select staging by default', () => {
  const source = 'export const AUTH_CONFIGS = Object.freeze({production:null,staging:null});\n' +
    'export const AUTH_CONFIG = AUTH_CONFIGS.production;\n';
  assert.throws(readStagingAuthConfig.bind(null, source), /default to its staging Auth config/);
});

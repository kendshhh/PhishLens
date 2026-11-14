import { createAuthClient, BetterAuthVanillaAdapter } from '../vendor/neon/sdk.mjs';
import { createNeonAccounts } from './neon-accounts.js';
import { createAnalysisClient } from './api.js';
import { MODEL_SHA256 } from '../ai/local-analyzer.mjs';

export function createNeonIntegration({ config, apiOrigin, fetchImpl = globalThis.fetch,
  sdkFactory = createAuthClient, adapterFactory = BetterAuthVanillaAdapter,
  hostPermissions = globalThis.chrome?.runtime?.getManifest()?.host_permissions || [] } = {}) {
  if (!config?.enabled) return {};
  const url = new URL(config.authUrl);
  if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash ||
      !config.database || url.pathname !== `/${encodeURIComponent(config.database)}/auth` ||
      config.apiOrigin !== apiOrigin || !hostPermissions.includes(url.origin + '/*')) {
    throw new Error('The account environment configuration or host permission does not match this build.');
  }
  const sdk = sdkFactory(url.href, { adapter: adapterFactory({ fetchOptions: {
    credentials: 'include', redirect: 'error', timeout: 10000, retry: 0
  } }) });
  const adapter = createNeonAccounts(sdk);
  return { adapter, createClient: session => createAnalysisClient(apiOrigin, fetchImpl, {
    requiredModel: MODEL_SHA256, getAccessToken: () => adapter.getAccessToken(session.user.id)
  }) };
}

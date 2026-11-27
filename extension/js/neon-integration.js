import { createAuthClient, BetterAuthVanillaAdapter } from '../vendor/neon/sdk.mjs';
import { createNeonAccounts } from './neon-accounts.js';
import { AUTH_BRIDGE_REQUEST_MS, AUTH_BRIDGE_STARTUP_MS, createNeonBridgeClient } from './neon-bridge-client.js';
import { createAnalysisClient } from './api.js';
import { MODEL_SHA256 } from '../ai/local-analyzer.mjs';

export function createNeonIntegration({ config, apiOrigin, fetchImpl = globalThis.fetch,
  sdkFactory = createAuthClient, adapterFactory = BetterAuthVanillaAdapter,
  bridgeFactory = createNeonBridgeClient,
  storage = globalThis.chrome?.storage?.local,
  hostPermissions = globalThis.chrome?.runtime?.getManifest()?.host_permissions || [] } = {}) {
  if (!config?.enabled) return {};
  const url = new URL(config.authUrl);
  if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash ||
      !config.database || url.pathname !== `/${encodeURIComponent(config.database)}/auth` ||
      config.apiOrigin !== apiOrigin || !hostPermissions.includes(apiOrigin + '/*')) {
    throw new Error('The account environment configuration or host permission does not match this build.');
  }

  let sdk;
  if (config.transport === 'https-bridge') {
    const bridge = new URL(config.bridgeUrl);
    if (bridge.origin !== apiOrigin || bridge.protocol !== 'https:' || bridge.username || bridge.password ||
        bridge.search || bridge.hash || bridge.pathname !== '/auth/bridge' ||
        !hostPermissions.includes(bridge.origin + '/*')) {
      throw new Error('The account bridge configuration or host permission does not match this build.');
    }
    sdk = bridgeFactory({ bridgeUrl: bridge.href, authUrl: url.href });
  } else if (config.transport === 'direct') {
    if (!hostPermissions.includes(url.origin + '/*')) {
      throw new Error("The direct Auth origin is not listed in this build's host permissions.");
    }
    sdk = sdkFactory(url.href, { adapter: adapterFactory({ fetchOptions: {
      credentials: 'include', redirect: 'error', timeout: 10000, retry: 0,
    } }) });
  } else {
    if (config.transport && config.transport !== 'https-proxy') {
      throw new Error('Unsupported account transport.');
    }
    // The release build proxies Auth through the configured HTTPS API origin.
    const authProxyUrl = new URL('/api/auth', apiOrigin).href;
    sdk = sdkFactory(authProxyUrl, { adapter: adapterFactory({ fetchOptions: {
      credentials: 'include', redirect: 'error', timeout: 10000, retry: 0,
    } }) });
  }

  const key = 'phishlensSignedOut:' + url.href;
  const signOutStorage = storage && {
    async isBlocked() { return (await storage.get(key))[key] === true; },
    async setBlocked(blocked) {
      if (blocked) await storage.set({ [key]: true });
      else await storage.remove(key);
    }
  };
  const accountOptions = { signOutStorage };
  if (config.transport === 'https-bridge') {
    // The bridge owns the startup and dispatch timeouts.
    accountOptions.timeoutMs = AUTH_BRIDGE_STARTUP_MS + AUTH_BRIDGE_REQUEST_MS + 1000;
  }
  const adapter = createNeonAccounts(sdk, accountOptions);
  return { adapter, createClient: session => createAnalysisClient(apiOrigin, fetchImpl, {
    requiredModel: MODEL_SHA256, getAccessToken: () => adapter.getAccessToken(session.user.id)
  }) };
}

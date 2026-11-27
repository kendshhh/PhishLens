import { createAuthClient, BetterAuthVanillaAdapter } from '../vendor/neon/sdk.mjs';
import { createNeonAccounts } from './neon-accounts.js';
import { createNeonBridgeClient } from './neon-bridge-client.js';
import { createAnalysisClient } from './api.js';
import { MODEL_SHA256 } from '../ai/local-analyzer.mjs';

export function createNeonIntegration({ config, apiOrigin, fetchImpl = globalThis.fetch,
  sdkFactory = createAuthClient, adapterFactory = BetterAuthVanillaAdapter,
  bridgeFactory = createNeonBridgeClient,
  storage = globalThis.chrome?.storage?.local,
  browserSessionStorage = globalThis.chrome?.storage?.session,
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
  const isUnconfirmed = async () => (await browserSessionStorage?.get(key))?.[key] === true;
  const signOutStorage = (storage || browserSessionStorage) && {
    isUnconfirmed,
    async isBlocked() { return (await storage?.get(key))?.[key] === true; },
    async setBlocked(blocked) {
      if (!blocked) {
        await storage?.remove(key);
        return;
      }
      if (storage) {
        try {
          await storage.set({ [key]: true });
          return !(await isUnconfirmed());
        } catch (error) {
          if (!browserSessionStorage) throw error;
        }
      }
      // A retry marker survives popup closure even when local storage cannot be written.
      await browserSessionStorage.set({ [key]: true });
      return false;
    },
    async clearUnconfirmed() {
      if (await isUnconfirmed()) await browserSessionStorage.remove(key);
    }
  };
  const adapter = createNeonAccounts(sdk, { signOutStorage });
  return { adapter, createClient: session => createAnalysisClient(apiOrigin, fetchImpl, {
    requiredModel: MODEL_SHA256, getAccessToken: () => adapter.getAccessToken(session.user.id)
  }) };
}

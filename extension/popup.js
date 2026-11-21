import { initializeAccountPopup } from './js/account-popup.js';
import { createNeonIntegration } from './js/neon-integration.js';
import { AUTH_CONFIG } from './js/auth-config.js';
import { API_BASE_URL } from './js/config.js';
// TEMPORARY TEST ACCESS (imports): remove these two lines with the block below.
import { createAnalysisClient } from './js/api.js';
import { MODEL_SHA256 } from './ai/local-analyzer.mjs';

// ===== TEMPORARY TEST ACCESS: START =====
// Lets teammates test checking and saving emails before Neon sign-in is live.
// To remove: delete everything between START and END, the two imports above, the
// `withTestAccess(...)`/`mountTestAccess(...)` wrapping at the bottom, and the
// `#test-access` button line in popup.html. Nothing else depends on it.
//
// Safety limits:
// - Only active while real sign-in is NOT configured (AUTH_CONFIG is null).
// - Sends report requests without a token, so only a backend running
//   REPORT_AUTH_MODE=demo accepts them. Those reports are shared by all testers:
//   use synthetic emails only.
const TEST_ACCESS_KEY = 'phishlensTestAccess';
const TEST_ACCESS_HOURS = 8;
const TEST_USER = Object.freeze({ id: 'temporary-test-access', email: 'test-access@phishlens.invalid',
  name: 'Temporary test access', emailVerified: true });
const NOT_CONNECTED = 'Account sign-in is not connected yet. Local scanning is still available.';

function withTestAccess(integration, { chromeImpl = globalThis.chrome, apiOrigin, now = Date.now } = {}) {
  if (integration.adapter) return integration; // Real sign-in is configured: never offer a bypass.
  const storage = chromeImpl.storage.session;
  const unavailable = async () => { throw new Error(NOT_CONNECTED); };
  const adapter = {
    async restore() {
      const expiresAt = (await storage.get(TEST_ACCESS_KEY))[TEST_ACCESS_KEY];
      return Number.isFinite(expiresAt) && expiresAt > now() ? { user: TEST_USER, expiresAt } : null;
    },
    async signIn(input) {
      if (input?.testAccess !== true) return unavailable(); // Email/password sign-in is still not connected.
      const expiresAt = now() + TEST_ACCESS_HOURS * 3600000;
      await storage.set({ [TEST_ACCESS_KEY]: expiresAt });
      return { user: TEST_USER, expiresAt };
    },
    async signOut() { await storage.remove(TEST_ACCESS_KEY); },
    signUp: unavailable, verifyEmail: unavailable, resend: unavailable, recover: unavailable, resetPassword: unavailable
  };
  function createClient() {
    const client = createAnalysisClient(apiOrigin, globalThis.fetch, { requiredModel: MODEL_SHA256 });
    // A backend that requires real sign-in answers 401; say so instead of "session expired".
    return Object.fromEntries(Object.entries(client).map(([name, method]) => [name, async (...args) => {
      try { return await method(...args); }
      catch (error) {
        if (error?.status !== 401) throw error;
        throw Object.assign(new Error('The server requires real sign-in, so temporary test access cannot use saved reports there.'), { status: 403 });
      }
    }]));
  }
  return { adapter, createClient, testAccess: true };
}

function mountTestAccess(app, integration, doc = document) {
  const button = doc.getElementById('test-access');
  if (!button || !integration.testAccess) return;
  app.accounts.subscribe(state => button.classList.toggle('hidden', state.status === 'signed-in'));
  button.addEventListener('click', async () => {
    button.disabled = true;
    const status = doc.getElementById('account-status');
    try {
      if (await app.accounts.signIn({ testAccess: true })) {
        status.textContent = 'Signed in with temporary test access. Saved reports are shared by all testers, so use synthetic emails only.';
      }
    } catch (error) {
      status.textContent = error.message || 'Temporary test access could not start.';
    } finally { button.disabled = false; }
  });
}
// ===== TEMPORARY TEST ACCESS: END =====

const integration = withTestAccess(createNeonIntegration({ config: AUTH_CONFIG, apiOrigin: API_BASE_URL }), { apiOrigin: API_BASE_URL });
mountTestAccess(initializeAccountPopup(integration), integration);
// After removing test access, restore the original line:
// initializeAccountPopup(createNeonIntegration({ config: AUTH_CONFIG, apiOrigin: API_BASE_URL }));

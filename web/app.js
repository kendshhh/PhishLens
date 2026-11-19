// PhishLens web app entry. It reuses the extension's UI controller and local
// analysis workflow; only the browser runtime differs (see runtime.js).
import { initializeAccountPopup } from './js/account-popup.js';
import { createNeonIntegration } from './js/neon-integration.js';
import { AUTH_CONFIG } from './js/auth-config.js';
import { API_BASE_URL } from './js/config.js';
import { createWorkflow } from './ai/live-workflow.mjs';
import { createWebRuntime, unavailableJudge } from './runtime.js';

// A web page has no extension host permissions. When accounts are enabled, the
// Auth origin must instead be allowed by the deployment's Content-Security-Policy.
const hostPermissions = AUTH_CONFIG?.enabled ? [new URL(AUTH_CONFIG.authUrl).origin + '/*'] : [];

initializeAccountPopup({
  chromeImpl: createWebRuntime({ workflow: createWorkflow({ judge: unavailableJudge }) }),
  ...createNeonIntegration({ config: AUTH_CONFIG, apiOrigin: API_BASE_URL, hostPermissions })
});

import { initializeAccountPopup } from './js/account-popup.js';
import { createNeonIntegration } from './js/neon-integration.js';
import * as authConfigModule from './js/auth-config.js';
import * as apiConfig from './js/config.js';
import { initializeGhost } from './js/ghost.js';

const requestedEnvironment = new globalThis.URLSearchParams(globalThis.location?.search || '').get('environment');
const releaseEnvironment = requestedEnvironment === 'staging' ? 'staging' : 'production';
// Staging-only packages export a single API origin and Auth configuration.
const { API_BASE_URL, API_BASE_URLS } = apiConfig;
const apiOrigin = (API_BASE_URLS && API_BASE_URLS[releaseEnvironment]) || API_BASE_URL;
const authConfig = authConfigModule.AUTH_CONFIGS
  ? authConfigModule.AUTH_CONFIGS[releaseEnvironment] : authConfigModule.AUTH_CONFIG;
initializeAccountPopup({
  ...createNeonIntegration({ config: authConfig, apiOrigin }),
  apiOrigin,
});
initializeGhost();

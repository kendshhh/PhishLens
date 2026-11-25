import { initializeAccountPopup } from './js/account-popup.js';
import { createNeonIntegration } from './js/neon-integration.js';
import { AUTH_CONFIGS, AUTH_CONFIG } from './js/auth-config.js';
import { API_BASE_URL, API_BASE_URLS } from './js/config.js';

const requestedEnvironment = new globalThis.URLSearchParams(globalThis.location?.search || '').get('environment');
const releaseEnvironment = requestedEnvironment === 'staging' ? 'staging' : 'production';
const apiOrigin = API_BASE_URLS[releaseEnvironment] || API_BASE_URL;
const authConfig = AUTH_CONFIGS ? AUTH_CONFIGS[releaseEnvironment] : AUTH_CONFIG;
initializeAccountPopup({
  ...createNeonIntegration({ config: authConfig, apiOrigin }),
  apiOrigin,
});

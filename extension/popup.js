import { initializeAccountPopup } from './js/account-popup.js';
import { createNeonIntegration } from './js/neon-integration.js';
import { AUTH_CONFIG } from './js/auth-config.js';
import { API_BASE_URL } from './js/config.js';

let integration;
try {
  integration = createNeonIntegration({ config: AUTH_CONFIG, apiOrigin: API_BASE_URL });
} catch {
  integration = { unavailableMessage: 'Accounts are unavailable in this build. Local scanning is still available.' };
}
initializeAccountPopup(integration);

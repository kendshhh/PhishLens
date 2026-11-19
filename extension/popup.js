import { initializeAccountPopup } from './js/account-popup.js';
import { createNeonIntegration } from './js/neon-integration.js';
import { AUTH_CONFIG } from './js/auth-config.js';
import { API_BASE_URL } from './js/config.js';
import { initializeGhost } from './js/ghost.js';

initializeAccountPopup(createNeonIntegration({ config: AUTH_CONFIG, apiOrigin: API_BASE_URL }));
initializeGhost();

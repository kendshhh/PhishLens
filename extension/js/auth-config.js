// Release packaging fills these public, branch-specific endpoints. Auth
// credentials are never stored in this file or in the extension package.
export const AUTH_CONFIGS = Object.freeze({ production: null, staging: null });
export const AUTH_CONFIG = AUTH_CONFIGS.production;

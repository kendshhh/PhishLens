// Release packaging fills public, branch-specific endpoints. Auth
// credentials are never stored in this file or in the extension package.
// The HTTPS bridge build may use a single paired configuration.
export const AUTH_CONFIGS = Object.freeze({ production: null, staging: null });
export const AUTH_CONFIG = AUTH_CONFIGS.production;

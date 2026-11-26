const PROVIDER_ERROR_CODES = new Set([
  'EMAIL_NOT_VERIFIED',
  'FORBIDDEN',
  'INTERNAL_SERVER_ERROR',
  'INVALID_CREDENTIALS',
  'INVALID_EMAIL',
  'INVALID_EMAIL_OR_PASSWORD',
  'INVALID_PASSWORD',
  'INVALID_SESSION',
  'RATE_LIMITED',
  'SESSION_EXPIRED',
  'SESSION_NOT_FOUND',
  'TOO_MANY_REQUESTS',
  'UNAUTHORIZED',
  'USER_NOT_FOUND',
]);

const ENDPOINTS = new Map([
  ['sign-in/email', 'sign_in'],
  ['get-session', 'get_session'],
  ['sign-out', 'sign_out'],
  ['sign-up/email', 'sign_up'],
  ['email-otp/verify-email', 'verify_email'],
]);

export function authEndpointName(pathname) {
  const prefix = '/api/auth/';
  if (typeof pathname !== 'string' || !pathname.startsWith(prefix)) return 'other';
  return ENDPOINTS.get(pathname.slice(prefix.length)) || 'other';
}

export function extractProviderErrorCode(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) return null;
  for (const value of [payload.code, payload.error_code, payload.errorCode]) {
    if (typeof value !== 'string') continue;
    const code = value.toUpperCase();
    if (PROVIDER_ERROR_CODES.has(code)) return code;
  }
  return null;
}

/** Return the exact origin of a credential-free HTTPS URL. */
export function requireHttpsOrigin(value, label = 'URL') {
  let parsed;
  try {
    parsed = new URL(value);
  } catch {
    throw new TypeError(`${label} must be an absolute HTTPS URL`);
  }

  if (parsed.protocol !== 'https:' || !parsed.hostname || parsed.username || parsed.password) {
    throw new TypeError(`${label} must be an absolute HTTPS URL without credentials`);
  }

  return parsed.origin;
}

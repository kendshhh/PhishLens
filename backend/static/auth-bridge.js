import { createAuthClient, BetterAuthVanillaAdapter } from './sdk.mjs';

const { authUrl, extensionOrigin } = document.body.dataset;
const sdk = createAuthClient(authUrl, { adapter: BetterAuthVanillaAdapter({ fetchOptions: {
  credentials: 'include', redirect: 'error', timeout: 10000, retry: 0
} }) });

// Keep the RPC surface limited to signup, sign-in, password recovery and sessions.
const actions = {
  getSession: () => sdk.getSession({ fetchOptions: { headers: { 'X-Force-Fetch': 'true' } } }),
  signIn: input => sdk.signIn.email(input),
  signUp: input => sdk.signUp.email(input),
  recover: input => sdk.forgetPassword.emailOtp(input),
  resetPassword: input => sdk.emailOtp.resetPassword(input),
  signOut: () => sdk.signOut()
};
const fields = {
  getSession: [], signOut: [], signIn: ['email', 'password'], signUp: ['name', 'email', 'password'],
  recover: ['email'],
  resetPassword: ['email', 'otp', 'password']
};
let channel;
function safeError(error) {
  const details = error?.error && typeof error.error === 'object' ? error.error : error;
  const code = ['OTP_EXPIRED', 'USER_ALREADY_EXISTS_USE_ANOTHER_EMAIL'].includes(details?.code)
    ? details.code : undefined;
  return { error: { status: Number(details?.status) || Number(error?.status) || 503, code } };
}
globalThis.addEventListener('message', async event => {
  const value = event.data;
  if (event.source !== globalThis.parent || event.source === globalThis || event.origin !== extensionOrigin ||
      value?.type !== 'phishlens-auth-request' || value.authUrl !== authUrl ||
      typeof value.channel !== 'string' || !/^[0-9a-f-]{36}$/.test(value.channel) ||
      !Number.isSafeInteger(value.id) || value.id < 1) return;
  if (channel && value.channel !== channel) return;
  channel = value.channel;
  const method = value.method;
  let result = { error: { status: 400 } };
  if (Object.hasOwn(actions, method)) {
    const input = value.input ?? {};
    const expected = fields[method];
    if (input && typeof input === 'object' && !Array.isArray(input) &&
        Object.keys(input).length === expected.length &&
        expected.every(key => typeof input[key] === 'string' && input[key].length <= 320)) {
      try {
        const response = await actions[method](input);
        // Provider error messages and an opaque session-cookie token must never
        // cross the frame boundary. getSession uses the SDK's JWT substitution.
        if (response?.error) result = safeError(response.error);
        else if (method === 'getSession') {
          const data = response?.data;
          if (data?.session && !/^[\w-]+\.[\w-]+\.[\w-]+$/.test(data.session.token || '')) {
            result = { error: { status: 503 } };
          } else result = { data: data?.session && data?.user ? {
            user: { id: data.user.id, email: data.user.email, name: data.user.name,
              emailVerified: data.user.emailVerified },
            session: { expiresAt: data.session.expiresAt, token: data.session.token }
          } : null };
        } else result = { data: { success: true } };
      } catch (error) { result = safeError(error); }
    }
  }
  event.source.postMessage({ type: 'phishlens-auth-result', channel, id: value.id, result }, extensionOrigin);
});

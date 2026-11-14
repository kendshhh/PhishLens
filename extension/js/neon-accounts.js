// SDK-independent boundary: credentials go only to the injected Neon client.
function failure(status) {
  const messages = { 400: 'The details or code were not accepted. Check them and try again.',
    401: 'Email or password was not accepted. Sign in again.',
    409: 'The account could not be created. Try signing in or verifying your email.',
    403: 'Verify your email before accessing saved reports.', 429: 'Too many attempts. Please wait before trying again.' };
  return Object.assign(new Error(messages[status] || 'The account service is temporarily unavailable. Please try again.'), { status });
}

export function createNeonAccounts(sdk, { now = Date.now, timeoutMs = 12000 } = {}) {
  let epoch = 0, signedOut = false;
  async function call(action) {
    let timer;
    try {
      const result = await Promise.race([action(), new Promise((_, reject) => {
        timer = setTimeout(() => reject(failure(503)), timeoutMs);
      })]);
      if (result?.error) throw failure(Number(result.error.status) || 503);
      return result?.data;
    } catch (error) {
      throw failure([400, 401, 403, 409, 429].includes(error?.status) ? error.status : 503);
    } finally { clearTimeout(timer); }
  }
  async function read() {
    const version = epoch;
    if (signedOut) return null;
    // SDK cache bypass ensures logout/account changes and renewed JWTs are seen.
    const data = await call(() => sdk.getSession({ fetchOptions: { headers: { 'X-Force-Fetch': 'true' } } }));
    if (signedOut || version !== epoch || !data?.session || !data?.user) return null;
    const { user, session } = data;
    if (!user.id || !user.email || user.emailVerified !== true) throw failure(403);
    const expiresAt = new Date(session.expiresAt).getTime();
    if (!Number.isFinite(expiresAt) || expiresAt <= now()) return null;
    return { user: { id: user.id, email: user.email, name: user.name || '', emailVerified: true }, expiresAt,
      token: session.token };
  }
  const publicSession = value => value && ({ user: value.user, expiresAt: value.expiresAt });
  async function establish(action, email, allowNoSession = false) {
    const version = ++epoch;
    signedOut = true;
    await call(action);
    if (version !== epoch) return null;
    signedOut = false;
    const current = await read();
    if (!current && !allowNoSession) {
      throw new Error('Sign-in could not be confirmed. Check browser cookie permissions and try again.');
    }
    if (current && current.user.email.toLowerCase() !== email.trim().toLowerCase()) throw failure(401);
    return publicSession(current);
  }
  return {
    async restore() { return publicSession(await read()); },
    async signUp({ name, email, password }) {
      await call(() => sdk.signUp.email({ name, email, password }));
      // Signup verification must be configured at the provider; no second OTP is
      // sent automatically here, to avoid invalidating the first delivered code.
    },
    signIn: ({ email, password }) => establish(() => sdk.signIn.email({ email, password }), email),
    verifyEmail: ({ email, code }) => establish(() => sdk.emailOtp.verifyEmail({ email, otp: code }), email, true),
    async resend({ email }) { await call(() => sdk.emailOtp.sendVerificationOtp({ email, type: 'email-verification' })); },
    async signOut() { ++epoch; signedOut = true; await call(() => sdk.signOut()); },
    async getAccessToken(expectedUserId) {
      const current = await read();
      if (!current || current.user.id !== expectedUserId) return null;
      const token = current.token;
      // This check prevents opaque session tokens being sent as JWTs. It is not
      // signature verification: the API remains the authorization authority.
      if (typeof token !== 'string' || !/^[\w-]+\.[\w-]+\.[\w-]+$/.test(token)) throw failure(503);
      let payload;
      try { payload = JSON.parse(globalThis.atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/'))); }
      catch { throw failure(503); }
      if (payload.sub !== expectedUserId || !Number.isFinite(payload.exp) || payload.exp * 1000 <= now()) return null;
      return token;
    },
    async recover({ email }) { await call(() => sdk.forgetPassword.emailOtp({ email })); },
    async resetPassword({ email, code, password }) {
      await call(() => sdk.emailOtp.resetPassword({ email, otp: code, password }));
      ++epoch; signedOut = true;
    }
  };
}

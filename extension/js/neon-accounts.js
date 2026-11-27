// SDK-independent boundary: credentials go only to the injected Neon client.
function failure(status, code) {
  const messages = { 400: 'The details or code were not accepted. Check them and try again.',
    401: 'Email or password was not accepted. Sign in again.',
    409: 'The account could not be created. Try signing in instead.',
    403: code === 'EMAIL_NOT_VERIFIED' ? 'Verify your email before signing in.' : 'This account is not allowed to sign in.',
    429: 'Too many attempts. Please wait before trying again.' };
  const message = status === 400 && code === 'OTP_EXPIRED'
    ? 'This code expired. Request a new code and try again.'
    : messages[status] || 'The account service is temporarily unavailable. Please try again.';
  return Object.assign(new Error(message), { status, ...(code ? { code } : {}) });
}

function providerFailure(error) {
  // The pinned SDK can throw a normalized AuthError with the raw HTTP details
  // under .error, as well as return a Better Auth error result.
  const details = error?.error && typeof error.error === 'object' ? error.error : error;
  const status = Number(details?.status) || Number(error?.status) || 503;
  const code = ['OTP_EXPIRED', 'USER_ALREADY_EXISTS_USE_ANOTHER_EMAIL', 'EMAIL_NOT_VERIFIED'].includes(details?.code)
    ? details.code : undefined;
  const duplicate = status === 422 && code === 'USER_ALREADY_EXISTS_USE_ANOTHER_EMAIL';
  return failure(duplicate ? 409 : status === 422 ? 400 : status, code);
}

export function createNeonAccounts(sdk, { now = Date.now, timeoutMs = 12000, signOutStorage } = {}) {
  let epoch = 0, signedOut = false;
  async function call(action) {
    let timer, result;
    try {
      result = await Promise.race([action(), new Promise((_, reject) => {
        timer = setTimeout(() => reject(failure(503)), timeoutMs);
      })]);
    } catch (error) {
      throw providerFailure(error);
    } finally { clearTimeout(timer); }
    if (result?.error) {
      throw providerFailure(result.error);
    }
    return result?.data;
  }
  async function readProviderSession() {
    // SDK cache bypass ensures logout/account changes and renewed JWTs are seen.
    const data = await call(() => sdk.getSession({ fetchOptions: { headers: { 'X-Force-Fetch': 'true' } } }));
    if (!data?.session || !data?.user) return null;
    const { user, session } = data;
    if (!user.id || !user.email || user.banned === true) throw failure(403);
    const expiresAt = new Date(session.expiresAt).getTime();
    if (!Number.isFinite(expiresAt) || expiresAt <= now()) return null;
    return { user: { id: user.id, email: user.email, name: user.name || '', emailVerified: user.emailVerified === true }, expiresAt,
      token: session.token };
  }
  async function read() {
    const version = epoch;
    if (signedOut || (signOutStorage && await signOutStorage.isBlocked()) || version !== epoch) return null;
    const current = await readProviderSession();
    if ((signOutStorage && await signOutStorage.isBlocked()) || signedOut || version !== epoch) return null;
    return current;
  }
  const publicSession = value => value && ({ user: value.user, expiresAt: value.expiresAt });
  async function rejectProviderSession(version) {
    // A provider may create a cookie session before email ownership is confirmed.
    // Keep local restoration blocked even if the remote sign-out endpoint is down.
    await signOutStorage?.setBlocked(true);
    signedOut = true;
    if (version !== epoch) return;
    await call(() => sdk.signOut());
  }
  async function establish(action, email, allowNoSession = false) {
    const version = ++epoch;
    signedOut = true;
    await call(action);
    if (version !== epoch) return null;
    const current = await readProviderSession();
    if (version !== epoch) return null;
    if (!current && !allowNoSession) {
      throw new Error('Sign-in could not be confirmed. Check browser cookie permissions and try again.');
    }
    if (current && current.user.email.toLowerCase() !== email.trim().toLowerCase()) throw failure(401);
    if (current) {
      await signOutStorage?.setBlocked(false);
      if (version !== epoch) return null;
      signedOut = false;
    }
    return publicSession(current);
  }
  function normalizeEmail(email) {
    if (typeof email !== 'string' || email.trim().length > 254 || !/^[^\s@]+@[^\s@]+$/.test(email.trim())) {
      throw failure(400);
    }
    return email.trim();
  }
  async function sendVerification(email) {
    await call(() => sdk.emailOtp.sendVerificationOtp({ email, type: 'email-verification' }));
  }
  return {
    async restore() { return publicSession(await read()); },
    async signUp({ name, email, password }) {
      if (typeof name !== 'string' || typeof password !== 'string') throw failure(400);
      name = name.trim();
      email = normalizeEmail(email);
      if (!name || name.length > 100 || email.length > 254 || !/^[^\s@]+@[^\s@]+$/.test(email) ||
          password.length < 8 || password.length > 128) throw failure(400);
      const result = await establish(() => sdk.signUp.email({ name, email, password }), email, true);
      // Sign-up is never an authenticated product session. Some provider settings
      // create a session before email verification, so explicitly revoke that cookie.
      if (result) {
        const version = epoch;
        await rejectProviderSession(version);
      }
      // The email-OTP plugin does not send a verification code by default for
      // sign-up; request the email-verification purpose explicitly.
      await sendVerification(email);
      return null;
    },
    async signIn({ email, password }) {
      email = normalizeEmail(email);
      let result;
      try { result = await establish(() => sdk.signIn.email({ email, password }), email); }
      catch (error) {
        if (error?.code !== 'EMAIL_NOT_VERIFIED') throw error;
        const version = epoch;
        try { await rejectProviderSession(version); }
        catch { throw failure(503); }
        throw error;
      }
      if (result?.user.emailVerified !== true) {
        const version = epoch;
        try { await rejectProviderSession(version); }
        catch { throw failure(503); }
        throw failure(403, 'EMAIL_NOT_VERIFIED');
      }
      return result;
    },
    async verifyEmail({ email, code }) {
      email = normalizeEmail(email);
      if (typeof code !== 'string' || !/^\d{6}$/.test(code)) throw failure(400);
      const version = ++epoch;
      signedOut = true;
      await signOutStorage?.setBlocked(true);
      await call(() => sdk.emailOtp.verifyEmail({ email, otp: code }));
      if (version !== epoch) return false;
      // Verification endpoints can also establish a provider session. Keep local
      // restoration blocked; the UI explicitly signs it out before returning to sign-in.
      const current = await readProviderSession();
      if (version !== epoch) return false;
      return Boolean(current);
    },
    async resend({ email }) {
      email = normalizeEmail(email);
      await sendVerification(email);
    },
    async signOut() {
      ++epoch;
      signedOut = true;
      // Keep restoration blocked across popup and browser restarts if the
      // provider is unreachable and its session cookie survives.
      try { await signOutStorage?.setBlocked(true); }
      finally { await call(() => sdk.signOut()); }
    },
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
      if (payload?.sub !== expectedUserId || !Number.isFinite(payload.exp) || payload.exp * 1000 <= now()) return null;
      return token;
    },
    async recover({ email }) { await call(() => sdk.forgetPassword.emailOtp({ email })); },
    async resetPassword({ email, code, password }) {
      await call(() => sdk.emailOtp.resetPassword({ email, otp: code, password }));
      ++epoch; signedOut = true;
      await signOutStorage?.setBlocked(true);
    }
  };
}

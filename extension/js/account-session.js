export function sessionError(message = 'Sign in to view your saved reports.') {
  return Object.assign(new Error(message), { code: 'session_required', status: 401 });
}

// The adapter owns credentials and refresh. This boundary only holds a verified session in memory.
export function createAccountSession({ adapter, createClient, onChange = () => {}, now = Date.now,
  schedule = setTimeout, cancel = clearTimeout }) {
  let session = null, client = null, revision = 0, timer, disposed = false;
  const listeners = new Set();
  let current = { status: 'restoring', user: null, message: 'Restoring your session…' };
  function publish(status, message = '') {
    current = { status, user: session?.user || null, message };
    for (const listener of listeners) listener(current);
  }
  async function clear(status = 'signed-out', message = '') {
    const version = ++revision;
    cancel(timer);
    session = null; client = null;
    publish(status, message);
    await onChange(null);
    return version;
  }
  async function accept(next, version) {
    if (disposed || version !== revision) return false;
    if (!next) { publish('signed-out'); return false; }
    if (!next.user?.id || !next.user.email || next.user.emailVerified !== true ||
        !Number.isFinite(next.expiresAt) || next.expiresAt <= now()) {
      publish('expired', 'Your session expired. Sign in again.');
      return false;
    }
    // Clear old account state before allowing a request for the next account.
    await onChange(next.user.id);
    if (disposed || version !== revision) return false;
    const nextClient = createClient(next);
    session = next;
    client = nextClient;
    publish('signed-in');
    timer = schedule(() => { void clear('expired', 'Your session expired. Sign in again.').catch(() => {}); },
      Math.min(next.expiresAt - now(), 2147483647));
    return true;
  }
  async function authenticate(method, input) {
    const version = await clear('restoring', 'Checking your account…');
    if (disposed || version !== revision) return false;
    try { return await accept(await adapter[method](input), version); }
    catch (error) { if (version === revision) publish('signed-out'); throw error; }
  }
  async function refresh() {
    const version = revision;
    if (!session) return;
    try {
      const next = await adapter.restore();
      if (disposed || version !== revision) return;
      if (!next || next.user?.id !== session.user.id) {
        await clear('expired', 'Your account changed or signed out. Sign in again.');
        return;
      }
      if (next.user.emailVerified !== true || !Number.isFinite(next.expiresAt) || next.expiresAt <= now()) {
        await clear('expired', 'Your session expired. Sign in again.'); return;
      }
      session = next;
      cancel(timer);
      timer = schedule(() => { void clear('expired', 'Your session expired. Sign in again.').catch(() => {}); },
        Math.min(next.expiresAt - now(), 2147483647));
    } catch {
      if (version === revision) await clear('expired', 'Your session could not be checked. Sign in again.');
    }
  }
  const ready = (async () => {
    const version = revision;
    try { await accept(await adapter.restore(), version); }
    catch { if (version === revision) publish('signed-out', 'Your session could not be restored. Sign in again.'); }
  })();
  const guarded = {};
  for (const method of ['listAnalyses', 'getAnalysis', 'createAnalysis', 'updateAnalysis', 'deleteAnalysis']) {
    guarded[method] = async (...args) => {
      if (!session || session.expiresAt <= now()) {
        if (session) await clear('expired', 'Your session expired. Sign in again.');
        throw sessionError(current.message || undefined);
      }
      const version = revision;
      try {
        const result = await client[method](...args);
        if (version !== revision) throw sessionError('The account changed. Open your reports again.');
        return result;
      } catch (error) {
        if (version === revision && error.status === 401) {
          await clear('expired', 'Your session expired. Sign in again.');
        }
        throw error;
      }
    };
  }
  return {
    ready, refresh, client: guarded, get state() { return current; },
    subscribe(listener) { listeners.add(listener); listener(current); return () => listeners.delete(listener); },
    signIn: input => authenticate('signIn', input),
    verifyEmail: input => authenticate('verifyEmail', input),
    signUp: input => adapter.signUp(input),
    resend: input => adapter.resend(input),
    recover: input => adapter.recover(input),
    resetPassword: input => adapter.resetPassword(input),
    async signOut() {
      await clear();
      try { await adapter.signOut(); }
      catch { publish('signed-out', 'Signed out on this device. The account service could not confirm sign-out.'); }
    },
    dispose() { disposed = true; ++revision; cancel(timer); listeners.clear(); session = null; client = null; }
  };
}

export const unavailableAccounts = {
  async restore() { return null; },
  async signOut() {},
  ...Object.fromEntries(['signIn', 'signUp', 'verifyEmail', 'resend', 'recover', 'resetPassword'].map(name =>
    [name, async () => { throw new Error('Account sign-in is not connected yet. Local scanning is still available.'); }]))
};

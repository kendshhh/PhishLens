// Run the Neon SDK in the API's HTTPS frame. Credentials stay with the
// pinned bridge and are submitted only once.
export const AUTH_BRIDGE_STARTUP_MS = 75000;
export const AUTH_BRIDGE_REQUEST_MS = 11000;
const BRIDGE_MODULE = '<script type="module" src="/auth/bridge/client.js">';
const RETRYABLE_STARTUP_STATUSES = new Set([200, 202, 502, 503, 504]);

export function createNeonBridgeClient({ bridgeUrl, authUrl, documentImpl = globalThis.document,
  windowImpl = documentImpl?.defaultView, fetchImpl = globalThis.fetch,
  startupMs = AUTH_BRIDGE_STARTUP_MS, timeoutMs = AUTH_BRIDGE_REQUEST_MS, retryDelayMs = 2500 } = {}) {
  const target = new URL(bridgeUrl);
  let connection;
  let sequence = 0;
  let disposed = false;

  function unavailable() { return { error: { status: 503 } }; }

  function close(active) {
    if (connection === active) connection = undefined;
    clearTimeout(active.startupTimer);
    active.controller.abort();
    active.resolveReady(false);
    for (const { resolve, timer } of active.pending.values()) {
      clearTimeout(timer);
      resolve(unavailable());
    }
    active.pending.clear();
    active.frame.remove();
  }

  function receive(event) {
    const active = connection;
    const value = event.data;
    if (!active || event.source !== active.frame.contentWindow || event.origin !== target.origin ||
        value?.type !== 'phishlens-auth-result' || value.channel !== active.channel) return;
    const request = active.pending.get(value.id);
    if (!request) return;
    active.pending.delete(value.id);
    clearTimeout(request.timer);
    request.resolve(value.result);
  }

  function waitForRetry(signal) {
    return new Promise(resolve => {
      function finish() {
        clearTimeout(timer);
        signal.removeEventListener('abort', finish);
        resolve();
      }
      const timer = setTimeout(finish, retryDelayMs);
      if (signal.aborted) finish();
      else signal.addEventListener('abort', finish, { once: true });
    });
  }

  async function checkBridge(signal) {
    // Render can serve a loading document before the application wakes.
    // Check the real bridge document without cookies or a credential payload.
    while (!signal.aborted) {
      try {
        const response = await fetchImpl(target.href, {
          cache: 'no-store', credentials: 'omit', redirect: 'error', signal,
        });
        const contentType = response.headers.get('content-type') ?? '';
        if (response.status === 200 && contentType.includes('text/html') &&
            (await response.text()).includes(BRIDGE_MODULE)) return true;
        await response.body?.cancel().catch(() => {});
        // An application-level configuration error needs a fresh explicit action.
        if (!RETRYABLE_STARTUP_STATUSES.has(response.status) || contentType.includes('application/json')) return false;
      } catch {
        if (signal.aborted) return false;
      }
      await waitForRetry(signal);
    }
    return false;
  }

  function open() {
    const frame = documentImpl.createElement('iframe');
    frame.hidden = true;
    frame.title = 'PhishLens account connection';
    frame.referrerPolicy = 'no-referrer';
    frame.setAttribute('sandbox', 'allow-scripts allow-same-origin');
    const controller = new globalThis.AbortController();
    let resolveReady;
    const ready = new Promise(resolve => { resolveReady = resolve; });
    const active = { frame, controller, ready, resolveReady, pending: new Map(), channel: globalThis.crypto.randomUUID() };
    connection = active;
    active.startupTimer = setTimeout(() => close(active), startupMs);
    void checkBridge(controller.signal).then(available => {
      if (connection !== active) return;
      if (!available) { close(active); return; }
      frame.addEventListener('load', () => {
        clearTimeout(active.startupTimer);
        resolveReady(true);
      }, { once: true });
      frame.src = target.href;
      documentImpl.body.append(frame);
    }, () => { if (connection === active) close(active); });
    return active;
  }

  async function request(method, input) {
    if (disposed) return unavailable();
    const active = connection ?? open();
    if (!(await active.ready) || connection !== active) return unavailable();
    const id = ++sequence;
    return new Promise(resolve => {
      const timer = setTimeout(() => {
        active.pending.delete(id);
        resolve(unavailable());
        // A stalled or interrupted frame is replaced on the next explicit request.
        // No action that may have reached the provider is replayed.
        if (active.pending.size === 0) close(active);
      }, timeoutMs);
      active.pending.set(id, { resolve, timer });
      try {
        active.frame.contentWindow.postMessage({
          type: 'phishlens-auth-request', channel: active.channel, id, method, input, authUrl
        }, target.origin);
      } catch {
        close(active);
      }
    });
  }

  function dispose() {
    disposed = true;
    windowImpl.removeEventListener('message', receive);
    windowImpl.removeEventListener('pagehide', dispose);
    if (connection) close(connection);
  }
  windowImpl.addEventListener('message', receive);
  windowImpl.addEventListener('pagehide', dispose, { once: true });
  return {
    getSession: () => request('getSession'),
    signIn: { email: input => request('signIn', input) },
    signUp: { email: input => request('signUp', input) },
    emailOtp: { resetPassword: input => request('resetPassword', input) },
    forgetPassword: { emailOtp: input => request('recover', input) },
    signOut: () => request('signOut'),
    dispose
  };
}

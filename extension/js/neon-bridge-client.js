// Run the existing Neon SDK in the API's HTTPS frame. The browser supplies its
// real HTTPS Origin; credentials and tokens never enter a content script.
export function createNeonBridgeClient({ bridgeUrl, authUrl, documentImpl = globalThis.document,
  windowImpl = documentImpl?.defaultView, timeoutMs = 11000 } = {}) {
  const target = new URL(bridgeUrl);
  const channel = globalThis.crypto.randomUUID();
  const frame = documentImpl.createElement('iframe');
  frame.hidden = true;
  frame.title = 'PhishLens account connection';
  frame.referrerPolicy = 'no-referrer';
  frame.setAttribute('sandbox', 'allow-scripts allow-same-origin');
  const pending = new Map();
  let sequence = 0, disposed = false;
  function unavailable() { return { error: { status: 503 } }; }
  function receive(event) {
    const value = event.data;
    if (event.source !== frame.contentWindow || event.origin !== target.origin ||
        value?.type !== 'phishlens-auth-result' || value.channel !== channel) return;
    const request = pending.get(value.id);
    if (!request) return;
    pending.delete(value.id);
    clearTimeout(request.timer);
    request.resolve(value.result);
  }
  windowImpl.addEventListener('message', receive);
  let loaded;
  const ready = new Promise(resolve => { loaded = resolve; });
  frame.addEventListener('load', () => loaded());
  frame.src = target.href;
  documentImpl.body.append(frame);
  async function request(method, input) {
    if (disposed) return unavailable();
    const id = ++sequence;
    return new Promise(resolve => {
      const timer = setTimeout(() => {
        pending.delete(id);
        resolve(unavailable());
      }, timeoutMs);
      pending.set(id, { resolve, timer });
      void ready.then(() => {
        // A timed-out credential request must never be submitted by a late frame.
        if (pending.has(id) && !disposed) frame.contentWindow.postMessage({
          type: 'phishlens-auth-request', channel, id, method, input, authUrl
        }, target.origin);
      });
    });
  }
  function dispose() {
    disposed = true;
    windowImpl.removeEventListener('message', receive);
    windowImpl.removeEventListener('pagehide', dispose);
    for (const { resolve, timer } of pending.values()) { clearTimeout(timer); resolve(unavailable()); }
    pending.clear();
    frame.remove();
  }
  windowImpl.addEventListener('pagehide', dispose, { once: true });
  return {
    getSession: () => request('getSession'),
    signIn: { email: input => request('signIn', input) },
    signUp: { email: input => request('signUp', input) },
    emailOtp: {
      verifyEmail: input => request('verifyEmail', input),
      sendVerificationOtp: input => request('resend', input),
      resetPassword: input => request('resetPassword', input)
    },
    forgetPassword: { emailOtp: input => request('recover', input) },
    signOut: () => request('signOut'),
    dispose
  };
}

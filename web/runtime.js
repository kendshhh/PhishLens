// Browser replacement for the extension-only APIs used by the shared PhishLens UI.
// The extension runs scans in a background service worker and keeps state in
// chrome.storage.session. The web app runs the same local workflow in the page
// and keeps the same state in this tab's sessionStorage, so js/popup.js works
// unchanged. Email text never leaves the browser unless the user saves a report.
// app.js supplies the workflow, so this module has no build-time dependencies.

const ANALYSIS_KEY = 'veriqoAnalysis';
const STORAGE_PREFIX = 'phishlens:';

// The local LLM review needs about 1 GB of separately provisioned weights and
// WebGPU, which a hosted static site does not ship. Report that the reviewer is
// unavailable so the workflow returns its documented Uncertain outcome.
export async function unavailableJudge() {
  return { ok: false, code: 'model_assets_missing' };
}

// sessionStorage is per tab and cleared when the tab closes, like the extension's
// session storage. Private modes or blocked site data can make it throw, so fall
// back to memory for this page load instead of failing the scan.
export function createSessionArea(storage) {
  const memory = new Map();
  // If persistence fails, memory becomes authoritative for that key so an older
  // value left in sessionStorage cannot replace the newest in-page state.
  const memoryOverrides = new Set();
  const getStorage = () => {
    try {
      return storage === undefined ? globalThis.sessionStorage : storage;
    } catch {
      // Accessing the sessionStorage property itself can be blocked.
      return undefined;
    }
  };
  const read = key => {
    if (memoryOverrides.has(key)) {
      return memory.has(key) ? structuredClone(memory.get(key)) : undefined;
    }
    try {
      const raw = getStorage()?.getItem(STORAGE_PREFIX + key);
      if (raw != null) return JSON.parse(raw);
    } catch {
      // Unreadable or unavailable storage falls back to memory.
    }
    return memory.has(key) ? structuredClone(memory.get(key)) : undefined;
  };
  const write = (key, value) => {
    memory.set(key, structuredClone(value));
    const target = getStorage();
    if (!target) {
      memoryOverrides.add(key);
      return;
    }
    try {
      target.setItem(STORAGE_PREFIX + key, JSON.stringify(value));
      memoryOverrides.delete(key);
    } catch {
      memoryOverrides.add(key);
      // Memory still holds the newest value for this page load.
    }
  };
  const remove = key => {
    memory.delete(key);
    const target = getStorage();
    if (!target) {
      memoryOverrides.add(key);
      return;
    }
    try {
      target.removeItem(STORAGE_PREFIX + key);
      memoryOverrides.delete(key);
    } catch {
      memoryOverrides.add(key);
      // Keep the removal authoritative for this page load.
    }
  };
  return { read, write, remove };
}

export function createWebRuntime({ workflow, area = createSessionArea(),
  randomUUID = () => globalThis.crypto.randomUUID(), now = () => new Date() } = {}) {
  const listeners = new Set();
  let generation = 0;
  let activeJob;

  function notify(changes) {
    if (!Object.keys(changes).length) return;
    // Chrome delivers storage events asynchronously; keep the same ordering.
    queueMicrotask(() => { for (const listener of listeners) listener(changes, 'session'); });
  }
  const keysOf = keys => keys == null ? null : Array.isArray(keys) ? keys
    : typeof keys === 'string' ? [keys] : Object.keys(keys);

  const session = {
    async get(keys) {
      const result = {};
      for (const key of keysOf(keys) ?? [ANALYSIS_KEY]) {
        const value = area.read(key);
        if (value !== undefined) result[key] = value;
        else if (keys && typeof keys === 'object' && !Array.isArray(keys) && keys[key] !== undefined) result[key] = keys[key];
      }
      return result;
    },
    async set(items) {
      const changes = {};
      for (const [key, newValue] of Object.entries(items)) {
        const oldValue = area.read(key);
        area.write(key, newValue);
        changes[key] = { oldValue, newValue: structuredClone(newValue) };
      }
      notify(changes);
    },
    async remove(keys) {
      const changes = {};
      for (const key of keysOf(keys)) {
        const oldValue = area.read(key);
        if (oldValue === undefined) continue;
        area.remove(key);
        changes[key] = { oldValue };
      }
      notify(changes);
    }
  };

  const setAnalysis = (request, state) => {
    if (request !== generation) return Promise.resolve();
    return state === null ? session.remove(ANALYSIS_KEY) : session.set({ [ANALYSIS_KEY]: state });
  };

  async function analyze(text) {
    const request = ++generation;
    const jobId = randomUUID();
    activeJob = { request, text };
    await setAnalysis(request, { status: 'loading', selectedText: text, stage: 'TF-IDF v12a', result: null, error: null });
    try {
      // The same one-shot flag the extension uses to demonstrate a controlled failure.
      if (area.read('phishlensDebugFailNext')) {
        await session.remove('phishlensDebugFailNext');
        throw Error('Simulated local-model failure. Check again to retry.');
      }
      const result = await workflow(text, { jobId,
        isCurrent: () => request === generation,
        onProgress: stage => setAnalysis(request, { status: 'loading', selectedText: text, stage, result: null, error: null })
      });
      await setAnalysis(request, { status: 'success', selectedText: text, result, error: null,
        scanId: randomUUID(), recordedAt: now().toISOString() });
    } catch (error) {
      await setAnalysis(request, { status: 'error', selectedText: text, result: null,
        error: error instanceof Error ? error.message : 'Unable to assess. Reload the page and try again.' });
    } finally {
      if (activeJob?.request === request) activeJob = undefined;
    }
  }

  async function sendMessage(message) {
    if (message?.type === 'phishlens-analyze-text' && typeof message.text === 'string') {
      await analyze(message.text);
      return { ok: true };
    }
    if (message?.type === 'phishlens-cancel-analysis') {
      const job = activeJob;
      if (!job) return { ok: true };
      activeJob = undefined;
      const request = ++generation;
      await setAnalysis(request, { status: 'cancelled', selectedText: job.text, result: null, error: null });
      return { ok: true };
    }
    if (message?.type === 'phishlens-clear-analysis') {
      activeJob = undefined;
      await setAnalysis(++generation, null);
      return { ok: true };
    }
    return undefined;
  }

  // A reload during a scan cannot resume it; show the retained text with an error.
  const stored = area.read(ANALYSIS_KEY);
  if (stored?.status === 'loading') {
    area.write(ANALYSIS_KEY, { status: 'error', selectedText: stored.selectedText, result: null,
      error: 'The previous check was interrupted when the page reloaded. Check again to retry.' });
  }

  return {
    storage: { session, onChanged: {
      addListener: listener => listeners.add(listener),
      removeListener: listener => listeners.delete(listener)
    } },
    runtime: { sendMessage }
  };
}

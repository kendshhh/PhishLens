// Run the real side panel (extension/popup.html) in an ordinary browser tab, without
// loading the extension. A small stand-in for the extension APIs runs the same local
// TF-IDF + reevaluator workflow in the page, and keeps state in this tab's
// sessionStorage. The ~1 GB local LLM review is not available here, so results read
// "Uncertain — check before acting", as in an extension without model weights.
// Accounts stay disabled, as in the extension. Nothing is sent over the network.
import { initializeAccountPopup } from '../extension/js/account-popup.js';
import { initializeGhost } from '../extension/js/ghost.js';
import { createWorkflow } from '../extension/ai/live-workflow.mjs';

const ANALYSIS = 'veriqoAnalysis';
const PREFIX = 'phishlens-preview:';
const listeners = new Set();
const workflow = createWorkflow({ judge: async () => ({ ok: false, code: 'model_assets_missing' }) });

function read(key) {
  try { const raw = sessionStorage.getItem(PREFIX + key); return raw == null ? undefined : JSON.parse(raw); }
  catch { return undefined; }
}
function write(key, value) {
  try { if (value === undefined) sessionStorage.removeItem(PREFIX + key); else sessionStorage.setItem(PREFIX + key, JSON.stringify(value)); }
  catch { /* the preview keeps working without persistence */ }
}
function notify(changes) {
  if (Object.keys(changes).length) queueMicrotask(() => { for (const fn of listeners) fn(changes, 'session'); });
}
const keysOf = keys => keys == null ? [] : Array.isArray(keys) ? keys : typeof keys === 'string' ? [keys] : Object.keys(keys);
const session = {
  async get(keys) {
    const result = {};
    for (const key of keysOf(keys)) { const value = read(key); if (value !== undefined) result[key] = value; }
    return result;
  },
  async set(items) {
    const changes = {};
    for (const [key, newValue] of Object.entries(items)) { changes[key] = { oldValue: read(key), newValue }; write(key, newValue); }
    notify(changes);
  },
  async remove(keys) {
    const changes = {};
    for (const key of keysOf(keys)) { const oldValue = read(key); if (oldValue === undefined) continue; write(key, undefined); changes[key] = { oldValue }; }
    notify(changes);
  }
};

let generation = 0;
let active;
const setAnalysis = (request, state) => request !== generation ? Promise.resolve()
  : state === null ? session.remove(ANALYSIS) : session.set({ [ANALYSIS]: state });

async function analyze(text) {
  const request = ++generation;
  active = { request, text };
  await setAnalysis(request, { status: 'loading', selectedText: text, stage: 'TF-IDF v12a', result: null, error: null });
  try {
    const result = await workflow(text, { jobId: crypto.randomUUID(), isCurrent: () => request === generation,
      onProgress: stage => setAnalysis(request, { status: 'loading', selectedText: text, stage, result: null, error: null }) });
    await setAnalysis(request, { status: 'success', selectedText: text, result, error: null,
      scanId: crypto.randomUUID(), recordedAt: new Date().toISOString() });
  } catch (error) {
    await setAnalysis(request, { status: 'error', selectedText: text, result: null,
      error: error instanceof Error ? error.message : 'Unable to assess. Reload the page and try again.' });
  } finally { if (active?.request === request) active = undefined; }
}

const chromeImpl = {
  storage: { session, onChanged: { addListener: fn => listeners.add(fn), removeListener: fn => listeners.delete(fn) } },
  runtime: {
    async sendMessage(message) {
      if (message?.type === 'phishlens-analyze-text' && typeof message.text === 'string') { await analyze(message.text); return { ok: true }; }
      if (message?.type === 'phishlens-cancel-analysis') {
        const job = active; active = undefined;
        if (job) await setAnalysis(++generation, { status: 'cancelled', selectedText: job.text, result: null, error: null });
        return { ok: true };
      }
      if (message?.type === 'phishlens-clear-analysis') { active = undefined; await setAnalysis(++generation, null); return { ok: true }; }
      return undefined;
    }
  }
};

// A reload during a check cannot resume it.
if (read(ANALYSIS)?.status === 'loading') {
  write(ANALYSIS, { status: 'error', selectedText: read(ANALYSIS).selectedText, result: null,
    error: 'The previous check was interrupted when the page reloaded. Check again to retry.' });
}

initializeAccountPopup({ chromeImpl, fetchImpl: async () => { throw new Error('Network is disabled in the sidebar preview.'); } });
initializeGhost({ chromeImpl });

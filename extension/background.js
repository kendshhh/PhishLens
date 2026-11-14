import { analyzeWithReview } from './ai/live-workflow.mjs';
import { cancelJudge } from './ai/judge-client.mjs';

const MENU_ID = 'phishlens-analyze-selection';
let analysisGeneration = 0;
let stateUpdates = Promise.resolve();
let activeJob;

// Serialize writes so Clear and the newest scan win, including slow model loads.
function updateAnalysis(generation, state, badge) {
  const update = stateUpdates.catch(() => {}).then(async () => {
    if (generation !== analysisGeneration) return;
    if (state === null) await chrome.storage.session.remove('veriqoAnalysis');
    else await chrome.storage.session.set({ veriqoAnalysis: state });
    if (generation === analysisGeneration) await chrome.action.setBadgeText({ text: badge });
  });
  stateUpdates = update;
  return update;
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.removeAll(() => chrome.contextMenus.create({
    id: MENU_ID, title: 'Analyze selection with PhishLens', contexts: ['selection']
  }));
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (sender.id !== chrome.runtime.id) return;
  if (message?.type === 'phishlens-cancel-analysis') {
    const job = activeJob;
    if (!job) { sendResponse({ ok: true }); return; }
    activeJob = undefined;
    cancelJudge();
    updateAnalysis(++analysisGeneration, { status: 'cancelled', selectedText: job.selectedText,
      result: null, error: null }, '').then(
      () => sendResponse({ ok: true }), () => sendResponse({ ok: false })
    );
    return true;
  }
  if (message?.type === 'phishlens-clear-analysis') {
    activeJob = undefined;
    cancelJudge();
    updateAnalysis(++analysisGeneration, null, '').then(
      () => sendResponse({ ok: true }), () => sendResponse({ ok: false })
    );
    return true;
  }
  if (message?.type === 'phishlens-judge-heartbeat') { sendResponse({ ok: true }); return; }
  if (message?.type === 'phishlens-judge-progress') {
    if (activeJob?.jobId === message.jobId) {
      updateAnalysis(activeJob.generation, { status: 'loading', selectedText: activeJob.selectedText,
        stage: message.stage, progress: Number.isFinite(message.value) ? message.value : null,
        result: null, error: null }, '...').catch(() => {});
    }
    sendResponse({ ok: true }); return;
  }
  if (message?.type === 'phishlens-analyze-text' && typeof message.text === 'string') {
    analyzeSelectedText(message.text).then(
      () => sendResponse({ ok: true }), () => sendResponse({ ok: false })
    );
    return true;
  }
});

// Read the visible selection before the popup takes focus. Context-menu text
// can flatten paragraph breaks; accept the page value only for the same words.
async function readSelectedText(info, tab) {
  if (!Number.isInteger(tab?.id)) return info.selectionText;
  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id, frameIds: [Number.isInteger(info.frameId) ? info.frameId : 0] },
      injectImmediately: true,
      func: () => {
        const field = document.activeElement;
        if ((field?.tagName === 'TEXTAREA' || (field?.tagName === 'INPUT' &&
            ['text', 'search', 'email', 'url', 'tel'].includes(field.type))) &&
            Number.isInteger(field.selectionStart) && field.selectionEnd > field.selectionStart) {
          return field.value.slice(field.selectionStart, field.selectionEnd);
        }
        return globalThis.getSelection()?.toString() || '';
      }
    });
    const selected = results[0]?.result;
    const words = value => value.replace(/\s+/g, ' ').trim();
    if (typeof selected === 'string' && selected.trim() && words(selected) === words(info.selectionText)) return selected;
  } catch {
    // Restricted pages/frames can deny access; their menu selection still works.
  }
  return info.selectionText;
}

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === MENU_ID && typeof info.selectionText === 'string') {
    const request = ++analysisGeneration;
    const selectedText = await readSelectedText(info, tab);
    if (request !== analysisGeneration) return;
    return analyzeSelectedText(selectedText, { onStarted: async () => {
      try {
        await chrome.action.openPopup(Number.isInteger(tab?.windowId) ? { windowId: tab.windowId } : {});
      } catch {
        console.warn('PhishLens could not open the popup. Open it from the toolbar to view this scan.');
      }
    } }).catch(() => {
      console.error('PhishLens could not save the local scan state.');
    });
  }
});

async function analyzeSelectedText(selectedText, { onStarted } = {}) {
  const generation = ++analysisGeneration;
  cancelJudge();
  const jobId = crypto.randomUUID(); activeJob = { generation, jobId, selectedText };
  await updateAnalysis(generation, { status: 'loading', selectedText, stage: 'TF-IDF v12a', result: null, error: null }, '...');
  if (generation !== analysisGeneration) return;
  if (onStarted) await onStarted();
  if (generation !== analysisGeneration) return;
  try {
    const debug = await chrome.storage.session.get('phishlensDebugFailNext');
    if (debug.phishlensDebugFailNext) {
      await chrome.storage.session.remove('phishlensDebugFailNext');
      throw Error('Simulated local-model failure. Scan again to retry.');
    }
    const result = await analyzeWithReview(selectedText, { jobId,
      isCurrent: () => generation === analysisGeneration,
      onProgress: stage => updateAnalysis(generation, { status: 'loading', selectedText, stage, result: null, error: null }, '...')
    });
    await updateAnalysis(generation, {
      status: 'success', selectedText, result, error: null,
      scanId: crypto.randomUUID(), recordedAt: new Date().toISOString()
    }, result.workflow?.released ? (result.alert ? '!' : '·') : '?');
  } catch (error) {
    await updateAnalysis(generation, {
      status: 'error', selectedText, result: null,
      error: error instanceof Error ? error.message : 'Unable to assess. Reload the extension and retry.'
    }, '?');
  } finally {
    if (activeJob?.generation === generation) activeJob = undefined;
  }
}

// A restarted worker must not leave a previous interrupted scan loading forever.
chrome.storage.session.get('veriqoAnalysis').then(data => {
  if (analysisGeneration === 0 && data.veriqoAnalysis?.status === 'loading') {
    cancelJudge();
    return updateAnalysis(++analysisGeneration, { status: 'error', result: null,
      selectedText: data.veriqoAnalysis.selectedText,
      error: 'The previous local review was interrupted. Scan again to retry.' }, '?');
  }
}).catch(() => {});

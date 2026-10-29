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

chrome.contextMenus.onClicked.addListener(info => {
  if (info.menuItemId === MENU_ID && typeof info.selectionText === 'string') {
    analyzeSelectedText(info.selectionText).catch(() => {
      console.error('PhishLens could not save the local scan state.');
    });
  }
});

async function analyzeSelectedText(selectedText) {
  const generation = ++analysisGeneration;
  cancelJudge();
  const jobId = crypto.randomUUID(); activeJob = { generation, jobId, selectedText };
  await updateAnalysis(generation, { status: 'loading', selectedText, stage: 'TF-IDF v12a', result: null, error: null }, '...');
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

let creating;
async function ensureOffscreen() {
  const url = chrome.runtime.getURL('offscreen.html');
  if ((await chrome.runtime.getContexts({ contextTypes: ['OFFSCREEN_DOCUMENT'], documentUrls: [url] })).length) return;
  if (!creating) creating = chrome.offscreen.createDocument({ url: 'offscreen.html', reasons: ['WORKERS'],
    justification: 'Run the local LLM judge in a cancellable worker independently of popup lifetime.' }).finally(() => { creating = undefined; });
  await creating;
}

export async function requestJudge(primary, jobId) {
  try {
    await ensureOffscreen();
    const response = await chrome.runtime.sendMessage({ type: 'phishlens-run-judge', jobId, primary });
    const debug = await chrome.storage.session.get('phishlensDebug');
    if (debug.phishlensDebug && response?.diagnostic) {
      await chrome.storage.session.set({ phishlensLastJudgeDiagnostic: response.diagnostic });
    }
    if (debug.phishlensDebug && response?.ok) {
      await chrome.storage.session.set({ phishlensLastJudgeDiagnostic: {
        phase: 'judge_output', raw: response.raw, generated_tokens: response.generatedTokens,
        input_tokens: response.inputTokens, seed_passed: response.seedPassed
      } });
    }
    return response;
  } catch { return { ok: false, code: 'judge_service_unavailable' }; }
}

export function cancelJudge() {
  return chrome.runtime.sendMessage({ type: 'phishlens-cancel-judge' }).catch(() => {});
}

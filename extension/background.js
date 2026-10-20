import { API_BASE_URL } from "./js/config.js";

const MENU_ID = "phishlens-analyze-selection";
// Leave time to save an error before Chrome's 30-second fetch deadline.
const ANALYSIS_TIMEOUT_MS = 25_000;

let analysisGeneration = 0;
let stateUpdates = Promise.resolve();

// Serialize storage and badge writes so Clear and newer requests always win.
function updateAnalysis(generation, state, badge) {
  const update = stateUpdates.catch(() => {}).then(async () => {
    if (generation !== analysisGeneration) {
      return;
    }
    if (state === null) {
      await chrome.storage.session.remove("veriqoAnalysis");
    } else {
      await chrome.storage.session.set({ veriqoAnalysis: state });
    }
    if (generation === analysisGeneration) {
      await chrome.action.setBadgeText({ text: badge });
    }
  });
  stateUpdates = update;
  return update;
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "phishlens-clear-analysis") {
    return;
  }
  const generation = ++analysisGeneration;
  updateAnalysis(generation, null, "").then(
    () => sendResponse({ ok: true }),
    () => sendResponse({ ok: false })
  );
  return true;
});


// ---------------------------------------------------------
// Create the context-menu item when extension is installed
// ---------------------------------------------------------

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: MENU_ID,
      title: "Analyze selection with VeriQo",
      contexts: ["selection"]
    });
  });
});


// ---------------------------------------------------------
// Handle right-click context-menu action
// ---------------------------------------------------------

chrome.contextMenus.onClicked.addListener((info) => {
  if (info.menuItemId !== MENU_ID) {
    return;
  }

  const selectedText = info.selectionText?.trim();

  if (!selectedText) {
    return;
  }

  analyzeSelectedText(selectedText);
});


// ---------------------------------------------------------
// Send selected text to FastAPI
// ---------------------------------------------------------

async function analyzeSelectedText(selectedText) {
  const generation = ++analysisGeneration;
  // Save loading state for popup
  await updateAnalysis(generation, {
    status: "loading",
    selectedText,
    result: null,
    error: null
  }, "...");
  if (generation !== analysisGeneration) {
    return;
  }

  const controller = new AbortController();
  let timeout;
  try {
    const result = await Promise.race([
      requestAnalysis(selectedText, controller.signal),
      new Promise((_, reject) => {
        timeout = setTimeout(() => {
          reject(new Error("Analysis timed out. Please try again; the backend may still be starting."));
          controller.abort();
        }, ANALYSIS_TIMEOUT_MS);
      })
    ]);

    await updateAnalysis(generation, {
      status: "success",
      selectedText,
      result,
      error: null
    }, "✓");
  } catch (error) {
    if (generation !== analysisGeneration) {
      return;
    }
    console.error("PhishLens analysis failed:", error);
    await updateAnalysis(generation, {
      status: "error",
      selectedText,
      result: null,
      error: error instanceof Error ? error.message : "Unknown error"
    }, "!");
  } finally {
    clearTimeout(timeout);
  }
}

async function requestAnalysis(selectedText, signal) {
  const response = await fetch(
    `${API_BASE_URL}/analyses`,
    {
      method: "POST",
      signal,

      headers: {
        "Content-Type": "application/json"
      },

      body: JSON.stringify({
        text: selectedText
      })
    }
  );

  if (!response.ok) {
    let errorBody;
    try {
      errorBody = await response.json();
    } catch {
      throw new Error(
        `Backend returned HTTP ${response.status} with an invalid error response.`
      );
    }

    const message = errorBody?.error?.message;
    const legacyMessage = errorBody?.detail;

    throw new Error(
      typeof message === "string" && message.trim()
        ? message
        : typeof legacyMessage === "string" && legacyMessage.trim()
          ? legacyMessage
          : `Backend returned HTTP ${response.status}`
    );
  }

  return response.json();
}

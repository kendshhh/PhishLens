const API_URL = "http://127.0.0.1:8000";

const MENU_ID = "phishlens-analyze-selection";


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
  // Save loading state for popup
  await chrome.storage.session.set({
    veriqoAnalysis: {
      status: "loading",
      selectedText,
      result: null,
      error: null
    }
  });

  // Visual indicator
  await chrome.action.setBadgeText({
    text: "..."
  });

  try {
    const response = await fetch(
      `${API_URL}/analyses`,
      {
        method: "POST",

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

      throw new Error(
        typeof errorBody.detail === "string"
          ? errorBody.detail
          : `Backend returned HTTP ${response.status}`
      );
    }

    const result = await response.json();

    // Save successful result
    await chrome.storage.session.set({
      veriqoAnalysis: {
        status: "success",
        selectedText,
        result,
        error: null
      }
    });

    await chrome.action.setBadgeText({
      text: "✓"
    });
  } catch (error) {
    console.error(
      "PhishLens analysis failed:",
      error
    );

    await chrome.storage.session.set({
      veriqoAnalysis: {
        status: "error",
        selectedText,
        result: null,
        error:
          error instanceof Error
            ? error.message
            : "Unknown error"
      }
    });

    await chrome.action.setBadgeText({
      text: "!"
    });
  }
}
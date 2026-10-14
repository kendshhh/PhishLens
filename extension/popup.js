const emptyState =
  document.getElementById("empty-state");

const loadingState =
  document.getElementById("loading-state");

const errorState =
  document.getElementById("error-state");

const resultState =
  document.getElementById("result-state");

const errorMessage =
  document.getElementById("error-message");

const classification =
  document.getElementById("classification");

const riskLevel =
  document.getElementById("risk-level");

const analysisMode =
  document.getElementById("analysis-mode");

const tactics =
  document.getElementById("tactics");

const recommendations =
  document.getElementById("recommendations");

const selectedText =
  document.getElementById("selected-text");

const clearButton =
  document.getElementById("clear-button");


// ---------------------------------------------------------
// Load state from extension session storage
// ---------------------------------------------------------

async function loadState() {
  const data =
    await chrome.storage.session.get(
      "veriqoAnalysis"
    );

  render(data.veriqoAnalysis);
}


// ---------------------------------------------------------
// Render popup state
// ---------------------------------------------------------

function render(state) {
  hideAllStates();

  if (!state) {
    emptyState.classList.remove("hidden");
    return;
  }

  if (state.status === "loading") {
    loadingState.classList.remove("hidden");
    return;
  }

  if (state.status === "error") {
    errorState.classList.remove("hidden");

    errorMessage.textContent =
      state.error ?? "Unknown error";

    return;
  }

  if (
    state.status === "success" &&
    state.result
  ) {
    renderResult(
      state.result,
      state.selectedText
    );

    resultState.classList.remove("hidden");
    return;
  }

  emptyState.classList.remove("hidden");
}


// ---------------------------------------------------------
// Render successful result
// ---------------------------------------------------------

function renderResult(result, text) {
  classification.textContent =
    result.classification ?? "Unknown";

  riskLevel.textContent =
    result.risk_level ?? "Unknown";

  analysisMode.textContent =
    "Mock response - configure Gemini for AI analysis.";
  analysisMode.classList.toggle(
    "hidden",
    result.mode !== "mock"
  );

  selectedText.textContent =
    text ?? "";

  renderList(
    tactics,
    result.tactics
  );

  renderList(
    recommendations,
    result.recommendations
  );
}


// ---------------------------------------------------------
// Render arrays safely
// ---------------------------------------------------------

function renderList(element, items = []) {
  element.replaceChildren();

  if (!items || items.length === 0) {
    const item =
      document.createElement("li");

    item.textContent = "None";

    element.appendChild(item);

    return;
  }

  for (const value of items) {
    const item =
      document.createElement("li");

    item.textContent = value;

    element.appendChild(item);
  }
}


// ---------------------------------------------------------
// Hide all states
// ---------------------------------------------------------

function hideAllStates() {
  emptyState.classList.add("hidden");
  loadingState.classList.add("hidden");
  errorState.classList.add("hidden");
  resultState.classList.add("hidden");
}


// ---------------------------------------------------------
// Automatically update popup if result changes
// ---------------------------------------------------------

chrome.storage.onChanged.addListener(
  (changes, areaName) => {
    if (
      areaName === "session" &&
      changes.veriqoAnalysis
    ) {
      render(
        changes.veriqoAnalysis.newValue
      );
    }
  }
);


// ---------------------------------------------------------
// Clear button
// ---------------------------------------------------------

clearButton.addEventListener(
  "click",
  async () => {
    await chrome.storage.session.remove(
      "veriqoAnalysis"
    );

    await chrome.action.setBadgeText({
      text: ""
    });

    render(null);
  }
);


// ---------------------------------------------------------
// Startup
// ---------------------------------------------------------

loadState();
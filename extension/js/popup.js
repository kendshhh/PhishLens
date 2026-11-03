import { API_BASE_URL } from "./config.js";
import { createAnalysisClient } from "./api.js";
import { saveAnalysisAndRefresh } from "./report-client.js";

const feedbackLabels = new Map([
  [null, "Unspecified"], ["none", "No feedback"], ["false_positive", "False positive"],
  ["false_negative", "False negative"]
]);
const provenanceLabels = new Map([
  ["mock", "Mock analysis (development/test output)"], ["real", "Provider-backed AI analysis"],
  ["unknown", "AI provenance unknown"]
]);
const classificationLabels = new Map([
  ["phishing", "Phishing"], ["legitimate", "Legitimate"], ["spam", "Spam"]
]);
const providerLabels = new Map([
  ["mock", "Mock provider"], ["gemini", "Gemini"], ["local", "Local model"]
]);

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function errorMessage(error, operation = "analysis") {
  if (error?.name === "TimeoutError" || [408, 504].includes(error?.status)) {
    return `The ${operation} request timed out. Your email is still here. Check your connection and try again.`;
  }
  if (error instanceof SyntaxError || /^Invalid\b|malformed/i.test(error?.message || "")) {
    return `The service returned a malformed ${operation} response. Your email is still here. Try again.`;
  }
  if (error?.status === 422) {
    return `The service could not validate this email: ${error.message}. Your email is still here. Check it and try again.`;
  }
  if (error?.status >= 500 || error?.name === "TypeError") {
    return `The ${operation} service is unavailable. Your email is still here. Check your connection and try again.`;
  }
  return `The ${operation} could not be completed: ${error?.message || "Unknown error"}. Your email is still here. Try again.`;
}

function historyErrorMessage(error) {
  if (error?.name === "TimeoutError" || [408, 504].includes(error?.status)) {
    return "Saved analyses took too long to load. Existing history is preserved; retry loading history.";
  }
  if (error instanceof SyntaxError || /^Invalid\b|malformed/i.test(error?.message || "")) {
    return "The saved analyses response was malformed. Existing history is preserved; retry loading history.";
  }
  return "Saved analyses are unavailable. Existing history is preserved; retry loading history.";
}

function detailErrorMessage(error) {
  if (error?.name === "TimeoutError" || [408, 504].includes(error?.status)) {
    return "Analysis details timed out. The saved report remains in history; reopen it to try again.";
  }
  if (error instanceof SyntaxError || /^Invalid\b|malformed/i.test(error?.message || "")) {
    return "The saved report details were malformed. No new result was displayed; reopen the report to try again.";
  }
  return "Analysis details are unavailable. The saved report remains in history; reopen it to try again.";
}

function node(doc, tag, className, text) {
  const element = doc.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function show(element, visible) {
  element.classList.toggle("hidden", !visible);
}

export function createPopupController(client, doc = document) {
  const $ = id => doc.getElementById(id);
  const ui = {
    status: $("crud-status"), list: $("history-list"), empty: $("empty"),
    loading: $("loading"), retryHistory: $("retry-history"), createForm: $("create-form"), subject: $("create-subject"),
    body: $("create-body"), detail: $("detail-panel"), detailContent: $("detail-content"),
    editForm: $("edit-form"), notes: $("edit-notes"), feedback: $("edit-feedback"),
    deleteConfirm: $("delete-confirm"), deleteSubject: $("delete-subject"),
    deleteButton: $("confirm-delete"), cancelDelete: $("cancel-delete"),
    cancelEdit: $("cancel-edit"), saveEdit: $("save-edit"), createButton: $("create-button")
  };
  let records = [];
  let selected = null;
  let busy = false;
  let detailRequest = 0;
  let listRequest = 0;

  function setStatus(message, kind = "info") {
    ui.status.textContent = message;
    ui.status.className = `status ${kind}`;
    show(ui.status, Boolean(message));
  }

  function setBusy(value) {
    busy = value;
    ui.subject.disabled = value;
    ui.body.disabled = value;
    ui.notes.disabled = value;
    ui.feedback.disabled = value;
    for (const button of [ui.createButton, ui.saveEdit, ui.cancelEdit, ui.deleteButton, ui.cancelDelete]) {
      button.disabled = value;
    }
    ui.createButton.textContent = value ? "Analyzing…" : "Analyze and save";
    ui.saveEdit.textContent = value ? "Saving…" : "Save changes";
    ui.deleteButton.textContent = value ? "Deleting…" : "Delete analysis";
  }

  function renderDetail(record) {
    ui.detailContent.replaceChildren();
    const analyzed = classificationLabels.has(record.prediction);
    const provenance = isRecord(record.analysis_provenance) ? record.analysis_provenance : {};
    const provenanceLines = [provenanceLabels.get(record.analysis_mode) || "AI provenance unknown"];
    if (typeof provenance.provider_mode === "string" && provenance.provider_mode.trim()) {
      provenanceLines.push(`Provider: ${providerLabels.get(provenance.provider_mode) || `Unrecognized (${provenance.provider_mode})`}`);
    }
    if (typeof provenance.model === "string" && provenance.model.trim()) provenanceLines.push(`Model: ${provenance.model}`);
    if (typeof provenance.model_revision === "string" && provenance.model_revision.trim()) provenanceLines.push(`Model revision: ${provenance.model_revision}`);
    if (typeof provenance.prompt_version === "string" && provenance.prompt_version.trim()) provenanceLines.push(`Prompt version: ${provenance.prompt_version}`);
    if (typeof provenance.explanation_source === "string" && provenance.explanation_source.trim()) provenanceLines.push(`Explanation source: ${provenance.explanation_source}`);
    if (provenanceLines.length === 1 && record.analysis_mode === "real") provenanceLines.push("Provider and model were not reported.");
    const values = [
      ["Subject", record.subject || "Untitled analysis"], ["Email body", record.body],
      ["Explanation", record.explanation || (analyzed
        ? "No explanation was returned. Review the available indicators and verify independently."
        : "Unavailable because this report has not been analyzed.")],
      ["Classification", classificationLabels.get(record.prediction) || (record.prediction == null ? "Not analyzed yet" : "Classification unavailable")],
      ["Risk", record.risk_level || (analyzed ? "Not provided" : "Not assessed (analysis not completed)")],
      ["Confidence", record.confidence == null
        ? "Not provided; no confidence estimate is available."
        : `${Math.round(record.confidence * 100)}% (model-reported score, not a guarantee)`],
      ["Threat indicators", !analyzed
        ? "Unavailable because this report has not been analyzed."
        : record.threat_indicators.length
        ? record.threat_indicators.map(indicator => `${indicator.type}: ${indicator.detail}${indicator.quote ? ` (“${indicator.quote}”)` : ""}`).join("\n")
        : "No validated indicators were returned."],
      ["Notes", record.notes || "No notes"], ["Feedback", feedbackLabels.get(record.feedback) || "Feedback unavailable"],
      ["AI provenance", provenanceLines.join("\n")]
    ];
    for (const [label, value] of values) {
      const section = node(doc, "div", "detail-field");
      section.append(node(doc, "h4", "", label), node(doc, "p", "", value));
      ui.detailContent.append(section);
    }
    const edit = node(doc, "button", "secondary", "Edit notes and feedback");
    edit.type = "button";
    edit.addEventListener("click", openEdit);
    const remove = node(doc, "button", "danger", "Delete analysis");
    remove.type = "button";
    remove.addEventListener("click", openDelete);
    ui.detailContent.append(edit, remove);
    ui.notes.value = record.notes || "";
    ui.feedback.value = record.feedback || "none";
    show(ui.detail, true);
  }

  function renderList() {
    ui.list.replaceChildren();
    show(ui.empty, records.length === 0);
    for (const record of records) {
      const item = node(doc, "li", "history-item");
      const title = node(doc, "strong", "", record.subject || "Untitled analysis");
      const summary = classificationLabels.get(record.prediction) || (record.prediction == null ? "Not analyzed yet" : "Classification unavailable");
      const meta = node(doc, "p", "muted", `${summary} · ${record.risk_level || (classificationLabels.has(record.prediction) ? "Risk not provided" : "Risk not assessed")}`);
      const open = node(doc, "button", "link-button", "View details");
      open.type = "button";
      open.setAttribute("aria-label", `View ${record.subject || "untitled analysis"}`);
      open.addEventListener("click", () => loadDetail(record.id));
      item.append(title, meta, open);
      ui.list.append(item);
    }
  }

  function invalidatePendingDetail() {
    detailRequest++;
    selected = null;
    ui.detailContent.replaceChildren();
    show(ui.detail, false);
    show(ui.editForm, false);
    show(ui.deleteConfirm, false);
  }

  async function refresh() {
    const request = ++listRequest;
    show(ui.loading, true);
    show(ui.empty, false);
    show(ui.retryHistory, false);
    try {
      const latestRecords = await client.listAnalyses();
      if (request !== listRequest) return false;
      records = latestRecords;
      renderList();
      show(ui.loading, false);
      show(ui.retryHistory, false);
      setStatus(records.length ? "Saved analyses loaded." : "No saved analyses yet.", records.length ? "success" : "info");
      return true;
    } catch (error) {
      if (request !== listRequest) return false;
      show(ui.loading, false);
      show(ui.retryHistory, true);
      if (records.length) renderList();
      else show(ui.empty, false);
      setStatus(historyErrorMessage(error), "error");
      return false;
    }
  }

  ui.retryHistory.addEventListener("click", () => refresh());

  async function loadDetail(id, { announce = true } = {}) {
    if (busy) return;
    const request = ++detailRequest;
    selected = null;
    ui.detailContent.replaceChildren();
    show(ui.detail, false);
    show(ui.editForm, false);
    show(ui.deleteConfirm, false);
    if (announce) setStatus("Loading analysis details…", "info");
    try {
      const result = await client.getAnalysis(id);
      if (request !== detailRequest) return;
      selected = result;
      renderDetail(selected);
      show(ui.editForm, false);
      show(ui.deleteConfirm, false);
      if (announce) setStatus("Analysis details loaded.", "success");
    } catch (error) {
      if (request !== detailRequest) return;
      setStatus(detailErrorMessage(error), "error");
    }
  }

  function openEdit() {
    ui.notes.value = selected.notes || "";
    ui.feedback.value = selected.feedback === null ? "null" : selected.feedback;
    show(ui.editForm, true);
    ui.notes.focus();
  }
  function openDelete() {
    ui.deleteSubject.textContent = selected.subject || "Untitled analysis";
    show(ui.deleteConfirm, true);
    ui.cancelDelete.focus();
  }

  ui.createForm.addEventListener("submit", async event => {
    event.preventDefault();
    if (busy) return;
    const input = { subject: ui.subject.value.trim(), body: ui.body.value.trim() };
    if (!input.body) {
      setStatus("Enter the email body before saving.", "error");
      ui.body.focus();
      return;
    }
    invalidatePendingDetail();
    setBusy(true);
    const createGeneration = ++listRequest;
    setStatus("Analyzing and saving your report…", "info");
    let result;
    try {
      result = await saveAnalysisAndRefresh(client, input);
    } catch (error) {
      setStatus(errorMessage(error), "error");
    } finally { setBusy(false); }
    if (!result) {
      if (createGeneration === listRequest) {
        show(ui.loading, false);
        show(ui.retryHistory, true);
      }
      return;
    }

    const { saved, detail, history, refreshErrors } = result;
    if (createGeneration === listRequest) show(ui.loading, false);
    const usableHistory = createGeneration === listRequest ? history : null;
    records = usableHistory === null
      ? [saved, ...records.filter(record => record.id !== saved.id)]
      : usableHistory;
    if (usableHistory !== null && !records.some(record => record.id === saved.id)) {
      records = [saved, ...records];
    }
    renderList();
    ui.subject.value = "";
    ui.body.value = "";
    selected = detail || saved;
    renderDetail(selected);
    show(ui.editForm, false);
    show(ui.deleteConfirm, false);

    const detailError = refreshErrors.find(item => item.operation === "detail")?.error;
    const historyError = refreshErrors.find(item => item.operation === "history")?.error;
    if (detailError || historyError) {
      const messages = [];
      if (detailError) messages.push("The full report could not be loaded; the save response is shown. Use View details to retry.");
      if (historyError) messages.push(historyErrorMessage(historyError));
      show(ui.retryHistory, Boolean(historyError && createGeneration === listRequest));
      setStatus(`Report saved. ${messages.join(" ")}`, "error");
    } else if (!classificationLabels.has(selected.prediction)) {
      show(ui.retryHistory, false);
      setStatus("Report saved, but the service did not return an analyzed result. No classification was inferred.", "info");
    } else {
      show(ui.retryHistory, false);
      setStatus("Analysis completed and report saved.", "success");
    }
  });

  ui.editForm.addEventListener("submit", async event => {
    event.preventDefault();
    if (busy || !selected) return;
    setBusy(true);
    try {
      selected = await client.updateAnalysis(selected.id, {
        notes: ui.notes.value.trim() || null,
        feedback: ui.feedback.value === "null" ? null : ui.feedback.value
      });
      show(ui.editForm, false);
      records = records.map(record => record.id === selected.id ? selected : record);
      renderList();
      renderDetail(selected);
      const refreshed = await refresh();
      if (refreshed) setStatus("Changes saved successfully.", "success");
    } catch (error) {
      setStatus(error instanceof SyntaxError || /Invalid/.test(error.message)
        ? "The server returned a malformed result. Your edits are still here."
        : `Could not save changes: ${error.message}. Your edits are still here.`, "error");
    } finally { setBusy(false); }
  });
  ui.cancelEdit.addEventListener("click", () => { show(ui.editForm, false); if (selected) renderDetail(selected); });
  ui.cancelDelete.addEventListener("click", () => show(ui.deleteConfirm, false));
  ui.deleteConfirm.addEventListener("submit", async event => {
    event.preventDefault();
    if (busy || !selected) return;
    setBusy(true);
    try {
      const deletedId = selected.id;
      await client.deleteAnalysis(deletedId);
      records = records.filter(record => record.id !== deletedId);
      renderList();
      selected = null;
      show(ui.detail, false);
      show(ui.deleteConfirm, false);
      show(ui.editForm, false);
      const refreshed = await refresh();
      if (refreshed) setStatus("Analysis deleted successfully.", "success");
    } catch (error) {
      setStatus(`Could not delete analysis: ${error.message}`, "error");
    } finally { setBusy(false); }
  });

  return { refresh, loadDetail, get records() { return records; } };
}

const contextStateIds = ["empty-state", "loading-state", "error-state", "result-state"];

export function renderContextAnalysis(state, doc = document) {
  const get = id => doc.getElementById(id);
  for (const id of contextStateIds) show(get(id), false);
  if (!state) {
    get("empty-state").textContent = "Select text on a page, then choose Analyze selection with VeriQo.";
    show(get("empty-state"), true);
    return;
  }
  if (state.status === "loading") {
    show(get("loading-state"), true);
    return;
  }
  if (state.status === "error") {
    const reason = state.error || "Unknown error";
    get("error-message").textContent = /timeout|timed out/i.test(reason)
      ? "Analysis timed out. Select the text and try again."
      : /malformed|invalid json|invalid response/i.test(reason)
        ? "The analysis service returned a malformed response. Select the text and try again."
        : /unavailable|network|fetch/i.test(reason)
          ? "The analysis service is unavailable. Check your connection and try again."
          : reason;
    show(get("error-state"), true);
    return;
  }
  if (state.status === "not_analyzed" || (state.status === "success" && !state.result)) {
    get("empty-state").textContent = "No analysis result is available yet. Select text and run an analysis to create a report.";
    show(get("empty-state"), true);
    return;
  }
  if (state.status !== "success") {
    get("error-message").textContent = "The saved analysis state was malformed. Select the text and try again.";
    show(get("error-state"), true);
    return;
  }
  const result = state.result;
  const classifications = new Set(["phishing", "legitimate", "spam"]);
  const risks = new Set(["low", "medium", "high"]);
  const isStringList = value => Array.isArray(value) && value.every(item => typeof item === "string");
  const validEvidence = Array.isArray(result.evidence) && result.evidence.every(item =>
    isRecord(item) && typeof item.text === "string" && typeof item.reason === "string");
  if (!classifications.has(result.classification) || !risks.has(result.risk_level) ||
      !(result.confidence == null || (typeof result.confidence === "number" && Number.isFinite(result.confidence) && result.confidence >= 0 && result.confidence <= 1)) ||
      !isStringList(result.tactics) || !isStringList(result.recommendations) || !validEvidence) {
    get("error-message").textContent = "The analysis service returned a malformed or incomplete report. Select the text and try again.";
    show(get("error-state"), true);
    return;
  }
  const classificationNames = { phishing: "Phishing", legitimate: "Legitimate", spam: "Spam" };
  const confidence = result.confidence;
  get("classification").textContent = classificationNames[result.classification];
  get("risk-level").textContent = result.risk_level;
  get("analysis-confidence").textContent = confidence == null
    ? "Not provided; no confidence estimate is available."
    : `${Math.round(confidence * 100)}% (model-reported score)`;
  get("confidence-note").textContent = "A confidence score is not a guarantee of correctness.";
  const contextProvenance = { mock: "Mock analysis (development/test output)", gemini: "Gemini provider", local: "Local model" };
  get("analysis-mode").textContent = contextProvenance[result.mode] || "AI provenance unknown";
  const modelDetails = [];
  if (typeof result.model === "string" && result.model.trim()) modelDetails.push(`Model: ${result.model}`);
  if (typeof result.model_revision === "string" && result.model_revision.trim()) modelDetails.push(`Revision: ${result.model_revision}`);
  if (typeof result.prompt_version === "string" && result.prompt_version.trim()) modelDetails.push(`Prompt version: ${result.prompt_version}`);
  get("analysis-model").textContent = modelDetails.join(" · ") || "Provider/model details were not reported.";
  get("selected-text").textContent = state.selectedText ?? "";
  const evidence = get("evidence");
  evidence.replaceChildren();
  if (result.evidence.length === 0) {
    evidence.append(node(doc, "li", "", "No supporting indicators were returned."));
  }
  for (const indicator of result.evidence) {
    evidence.append(node(doc, "li", "", `${indicator.text}: ${indicator.reason}`));
  }
  for (const [id, values] of [["tactics", result.tactics], ["recommendations", result.recommendations]]) {
    const list = get(id);
    list.replaceChildren();
    const items = values.length ? values : ["None returned"];
    for (const value of items) list.append(node(doc, "li", "", value));
  }
  show(get("result-state"), true);
}

export function connectContextAnalysis(chromeApi, doc = document) {
  const clearButton = doc.getElementById("clear-button");
  const onChanged = (changes, areaName) => {
    if (areaName === "session" && changes.veriqoAnalysis) {
      renderContextAnalysis(changes.veriqoAnalysis.newValue, doc);
    }
  };
  chromeApi.storage.session.get("veriqoAnalysis").then(data => renderContextAnalysis(data.veriqoAnalysis, doc));
  chromeApi.storage.onChanged.addListener(onChanged);
  clearButton.addEventListener("click", async () => {
    const response = await chromeApi.runtime.sendMessage({ type: "phishlens-clear-analysis" });
    if (!response?.ok) {
      doc.getElementById("error-message").textContent = "Could not clear the analysis. Please try again.";
      for (const id of contextStateIds) show(doc.getElementById(id), false);
      show(doc.getElementById("error-state"), true);
    }
  });
}

if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", () => {
    if (globalThis.chrome?.storage?.session && globalThis.chrome?.runtime) {
      connectContextAnalysis(globalThis.chrome, document);
    }
    const controller = createPopupController(createAnalysisClient(API_BASE_URL));
    controller.refresh();
  });
}

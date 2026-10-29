import { API_BASE_URL } from "./config.js";
import { createAnalysisClient } from "./api.js";

const feedbackLabels = new Map([
  [null, "Unspecified"], ["none", "No feedback"], ["false_positive", "False positive"],
  ["false_negative", "False negative"]
]);
const provenanceLabels = new Map([
  ["mock", "Mock AI analysis"], ["real", "Real AI analysis"],
  ["unknown", "AI provenance unknown"]
]);

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
    loading: $("loading"), createForm: $("create-form"), subject: $("create-subject"),
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
    for (const button of [ui.createButton, ui.saveEdit, ui.cancelEdit, ui.deleteButton, ui.cancelDelete]) {
      button.disabled = value;
    }
    ui.createButton.textContent = value ? "Saving…" : "Save analysis";
    ui.saveEdit.textContent = value ? "Saving…" : "Save changes";
    ui.deleteButton.textContent = value ? "Deleting…" : "Delete analysis";
  }

  function renderDetail(record) {
    ui.detailContent.replaceChildren();
    const values = [
      ["Subject", record.subject || "Untitled analysis"], ["Email body", record.body],
      ["Explanation", record.explanation || "No explanation available."],
      ["Prediction", record.prediction || "Pending"], ["Risk", record.risk_level || "Unknown"],
      ["Confidence", record.confidence == null ? "Not provided" : `${Math.round(record.confidence * 100)}%`],
      ["Threat indicators", record.threat_indicators.length
        ? record.threat_indicators.map(indicator => `${indicator.type}: ${indicator.detail}${indicator.quote ? ` (“${indicator.quote}”)` : ""}`).join("\n")
        : "None reported"],
      ["Notes", record.notes || "No notes"], ["Feedback", feedbackLabels.get(record.feedback) || "Feedback unavailable"],
      ["AI provenance", provenanceLabels.get(record.analysis_mode) || "AI provenance unknown"]
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
      const meta = node(doc, "p", "muted", `${record.prediction || "Pending"} · ${record.risk_level || "Risk unknown"}`);
      const open = node(doc, "button", "link-button", "View details");
      open.type = "button";
      open.setAttribute("aria-label", `View ${record.subject || "untitled analysis"}`);
      open.addEventListener("click", () => loadDetail(record.id));
      item.append(title, meta, open);
      ui.list.append(item);
    }
  }

  async function refresh() {
    const request = ++listRequest;
    show(ui.loading, true);
    show(ui.empty, false);
    try {
      const latestRecords = await client.listAnalyses();
      if (request !== listRequest) return false;
      records = latestRecords;
      renderList();
      show(ui.loading, false);
      setStatus(records.length ? "Saved analyses loaded." : "No saved analyses yet.", records.length ? "success" : "info");
      return true;
    } catch (error) {
      if (request !== listRequest) return false;
      show(ui.loading, false);
      if (records.length) renderList();
      else show(ui.empty, false);
      setStatus(error instanceof SyntaxError || /Invalid/.test(error.message)
        ? "The server returned malformed analysis data. Try again later."
        : `Saved analyses are unavailable: ${error.message}`, "error");
      return false;
    }
  }

  async function loadDetail(id, { announce = true } = {}) {
    if (busy) return;
    const request = ++detailRequest;
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
      setStatus(error instanceof SyntaxError || /Invalid/.test(error.message)
        ? "The server returned malformed analysis details."
        : `Unable to load details: ${error.message}`, "error");
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
    setBusy(true);
    let created;
    try {
      created = await client.createAnalysis(input);
      records = [created, ...records.filter(record => record.id !== created.id)];
      renderList();
      ui.subject.value = "";
      ui.body.value = "";
      const refreshed = await refresh();
      if (refreshed) setStatus("Analysis saved successfully.", "success");
    } catch (error) {
      setStatus(error instanceof SyntaxError || /Invalid/.test(error.message)
        ? "The server returned a malformed result. Your input is still here."
        : `Could not save analysis: ${error.message}. Your input is still here.`, "error");
    } finally { setBusy(false); }
    if (created) await loadDetail(created.id, { announce: false });
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
    show(get("empty-state"), true);
    return;
  }
  if (state.status === "loading") {
    show(get("loading-state"), true);
    return;
  }
  if (state.status === "error") {
    get("error-message").textContent = state.error || "Unknown error";
    show(get("error-state"), true);
    return;
  }
  if (state.status !== "success" || !state.result) {
    show(get("empty-state"), true);
    return;
  }
  const result = state.result;
  get("classification").textContent = result.classification ?? "Unknown";
  get("risk-level").textContent = result.risk_level ?? "Unknown";
  get("selected-text").textContent = state.selectedText ?? "";
  show(get("analysis-mode"), result.mode === "mock");
  for (const [id, values] of [["tactics", result.tactics], ["recommendations", result.recommendations]]) {
    const list = get(id);
    list.replaceChildren();
    const items = Array.isArray(values) && values.length ? values : ["None"];
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

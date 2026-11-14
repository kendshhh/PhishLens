import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createPopupController } from "../js/popup.js";
import { createInMemoryAnalysisClient } from "./in-memory-analysis-client.mjs";

class Element {
  constructor(id = "", classes = "") {
    this.id = id; this.children = []; this.listeners = new Map(); this.attributes = {};
    this.value = ""; this.disabled = false; this.textContent = ""; this.className = "";
    const names = new Set(classes.split(/\s+/).filter(Boolean));
    this.classList = {
      add: name => names.add(name), remove: name => names.delete(name),
      contains: name => names.has(name), toggle: (name, force) => {
        const add = force === undefined ? !names.has(name) : force;
        if (add) names.add(name); else names.delete(name);
        return add;
      }
    };
  }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = [...nodes]; }
  addEventListener(name, fn) { this.listeners.set(name, fn); }
  setAttribute(name, value) { this.attributes[name] = value; }
  focus() { this.focused = true; }
  async fire(name, extra = {}) {
    const handler = this.listeners.get(name);
    if (handler) await handler({ preventDefault() {}, target: this, ...extra });
  }
}

const ids = ["clear-report-search", "reset-report-search", "edit-correction", "reports-list-view", "report-search", "report-count", "no-report-matches", "back-to-reports", "history-heading", "report-mode-warning", "crud-status", "history-list", "empty", "loading", "create-form", "create-subject", "create-body", "detail-panel", "detail-heading", "detail-content", "edit-form", "edit-notes", "edit-feedback", "delete-confirm", "delete-heading", "delete-subject", "confirm-delete", "cancel-delete", "cancel-edit", "save-edit", "create-button", "empty-state", "loading-state", "error-state", "result-state", "error-message", "classification", "risk-level", "analysis-mode", "selected-text", "tactics", "recommendations", "clear-button"];
function setup(client) {
  const elements = new Map(ids.map(id => [id, new Element(id, ["empty", "detail-panel", "edit-form", "delete-confirm", "crud-status"].includes(id) ? "hidden" : "")]));
  const doc = { getElementById: id => elements.get(id), createElement: tag => Object.assign(new Element(), { tagName: tag }) };
  return { ui: elements, controller: createPopupController(client, doc) };
}
function record(id, subject = "Example") {
  return { id, subject, body: "Safe body <img src=x>", prediction: "phishing", confidence: 0.9,
    risk_level: "high", threat_indicators: [], explanation: "Safe explanation <script>",
    created_at: "2026-10-20T10:00:00Z", notes: null, feedback: "none", analysis_mode: "mock" };
}
const id = "29d80c39-ec0d-4db8-a6e5-87444ba2600c";

test('account reset removes report details, notes and confirmation text', async () => {
  const { ui, controller } = setup(createInMemoryAnalysisClient([record(id, 'Private demo report')]));
  await controller.refresh(); await controller.loadDetail(id);
  ui.get('edit-notes').value = 'Previous account note';
  ui.get('delete-subject').textContent = 'Private demo report';
  controller.reset();
  assert.deepEqual(controller.records, []);
  assert.equal(ui.get('history-list').children.length, 0);
  assert.equal(ui.get('detail-content').children.length, 0);
  assert.equal(ui.get('edit-notes').value, '');
  assert.equal(ui.get('delete-subject').textContent, '');
});

test('account reset rejects a late create completion without repopulating the library', async () => {
  let resolve;
  const { ui, controller } = setup({ ...createInMemoryAnalysisClient(),
    createAnalysis: () => new Promise(done => { resolve = done; }) });
  ui.get('create-body').value = 'Synthetic previous account draft';
  const pending = ui.get('create-form').fire('submit');
  controller.reset(); resolve(record(id, 'Previous account result')); await pending;
  assert.deepEqual(controller.records, []);
  assert.equal(ui.get('history-list').children.length, 0);
  assert.equal(ui.get('detail-panel').classList.contains('hidden'), true);
});

test("a local save completed over an open detail restores the report library", async () => {
  const previous = record(id, "Previous report");
  const saved = record("50d073a2-e810-401c-a848-a1d501843bc7", "New local report");
  const { ui, controller } = setup(createInMemoryAnalysisClient([previous]));
  await controller.loadDetail(previous.id);
  assert.equal(ui.get("reports-list-view").classList.contains("hidden"), true);
  assert.equal(controller.beginSave(), true);
  assert.equal(controller.showLibrary({ focus: false }), false);

  controller.acceptSavedReport({ saved, detail: saved, history: [saved, previous] }, { reveal: false });
  controller.endSave();

  assert.equal(ui.get("reports-list-view").classList.contains("hidden"), false);
  assert.equal(ui.get("detail-panel").classList.contains("hidden"), true);
  assert.equal(ui.get("history-list").children.length, 2);
  assert.equal(ui.get("history-list").children[0].children[0].textContent, "New local report");
  await controller.openSavedReport(saved.id);
  assert.equal(ui.get("detail-panel").classList.contains("hidden"), false);
  assert.equal(ui.get("detail-heading").textContent, "New local report");
});

test("HTML provides associated labels, focusable CRUD controls, a bounded popup and a responsive side panel", async () => {
  const html = await readFile(new URL("../popup.html", import.meta.url), "utf8");
  const css = await readFile(new URL("../css/popup.css", import.meta.url), "utf8");
  const popup = await readFile(new URL("../js/popup.js", import.meta.url), "utf8");
  const manifest = JSON.parse(await readFile(new URL("../manifest.json", import.meta.url), "utf8"));
  for (const [label, control] of [["create-subject", "create-subject"], ["create-body", "create-body"], ["edit-notes", "edit-notes"], ["edit-feedback", "edit-feedback"]]) {
    assert.match(html, new RegExp(`<label for="${label}">`));
    assert.match(html, new RegExp(`id="${control}"`));
  }
  assert.match(html, /role="status" aria-live="polite"/);
  assert.match(html, /id="edit-notes"[^>]*maxlength="2000"/);
  assert.match(html, /id="detail-heading" tabindex="-1"/);
  assert.match(html, /id="delete-heading" tabindex="-1"/);
  assert.match(html, /Analyze selection with PhishLens/);
  for (const id of ["empty-state", "loading-state", "error-state", "result-state", "clear-button"]) assert.match(html, new RegExp(`id="${id}"`));
  // Split flow: right-click opens a tab-scoped action popup (chrome.action.openPopup, Chrome 127+);
  // the toolbar opens the side panel, so the manifest must not define a default popup.
  assert.equal(manifest.minimum_chrome_version, "127");
  assert.equal(manifest.action.default_popup, undefined);
  assert.equal(manifest.side_panel.default_path, "popup.html");
  assert.ok(manifest.permissions.includes("sidePanel"));
  assert.match(css, /\.popup-surface body \{[^}]*width:\s*380px[^}]*max-height:\s*600px/);
  assert.match(css, /width:\s*min\(100vw,\s*460px\)/);
  assert.match(css, /min-width:\s*300px/);
  assert.match(css, /max-width:\s*520px/);
  assert.match(css, /overflow-y:\s*auto/);
  assert.match(popup, /createAnalysisClient\(API_BASE_URL, fetchImpl, \{ requiredModel: MODEL_SHA256 \}\)/);
  assert.doesNotMatch(popup, /in-memory-analysis-client/);
});

test("opening another analysis hides old actions during loading and after failure", async () => {
  let rejectB;
  const first = record(id, "A");
  const client = {
    ...createInMemoryAnalysisClient([first]),
    getAnalysis(recordId) {
      if (recordId === id) return Promise.resolve(first);
      return new Promise((_resolve, reject) => { rejectB = reject; });
    }
  };
  const { ui, controller } = setup(client);
  await controller.loadDetail(id);
  assert.equal(ui.get("detail-panel").classList.contains("hidden"), false);
  assert.equal(ui.get("detail-content").children.length, 12);

  const loadingB = controller.loadDetail("record-b");
  await Promise.resolve();
  assert.equal(ui.get("detail-panel").classList.contains("hidden"), true);
  assert.equal(ui.get("detail-content").children.length, 0);
  assert.equal(ui.get("edit-form").classList.contains("hidden"), true);
  assert.equal(ui.get("delete-confirm").classList.contains("hidden"), true);

  rejectB(new Error("Server unavailable"));
  await loadingB;
  assert.equal(ui.get("detail-panel").classList.contains("hidden"), true);
  assert.equal(ui.get("detail-content").children.length, 0);
  assert.match(ui.get("crud-status").textContent, /Unable to load details/);
});
test("late detail response cannot replace the most recently opened analysis", async () => {
  let resolveA;
  const first = record("first", "A");
  const second = record("second", "B");
  const client = { ...createInMemoryAnalysisClient(), getAnalysis(id) {
    if (id === "first") return new Promise(resolve => { resolveA = resolve; });
    return Promise.resolve(second);
  } };
  const { ui, controller } = setup(client);
  const doc = { getElementById: id => ui.get(id), createElement: tag => Object.assign(new Element(), { tagName: tag }) };
  const openA = controller.loadDetail("first");
  await controller.loadDetail("second");
  resolveA(first);
  await openA;
  assert.equal(ui.get("detail-content").children[0].children[1].textContent, "B");
});

test("starting Analyze and save invalidates an older pending detail response", async () => {
  let resolveOldDetail;
  const older = record("older", "Older report");
  const saved = record("created", "New analysis");
  const client = { ...createInMemoryAnalysisClient(), getAnalysis(recordId) {
    if (recordId === "older") return new Promise(resolve => { resolveOldDetail = resolve; });
    return Promise.resolve(saved);
  } };
  const { ui, controller } = setup(client);
  const openingOlder = controller.loadDetail("older");
  assert.equal(controller.beginSave(), true);
  resolveOldDetail(older);
  await openingOlder;
  assert.equal(ui.get("detail-panel").classList.contains("hidden"), true);
  assert.equal(ui.get("detail-content").children.length, 0);
  assert.equal(ui.get("edit-form").classList.contains("hidden"), true);
  assert.equal(ui.get("delete-confirm").classList.contains("hidden"), true);

  controller.acceptSavedReport({ saved, detail: saved, history: [saved] });
  controller.endSave();
  assert.equal(ui.get("detail-content").children[0].children[1].textContent, "New analysis");
  assert.equal(ui.get("detail-heading").focused, true);
});

test("older history response cannot erase a newly created analysis", async () => {
  let resolveOldList;
  let listCalls = 0;
  const saved = record("created", "New analysis");
  const client = {
    ...createInMemoryAnalysisClient(),
    listAnalyses() {
      listCalls++;
      if (listCalls === 1) return new Promise(resolve => { resolveOldList = resolve; });
      return Promise.resolve([saved]);
    },
    async createAnalysis() { return saved; },
    async getAnalysis() { return saved; }
  };
  const { ui, controller } = setup(client);
  const oldRefresh = controller.refresh();
  ui.get("create-body").value = "Synthetic email body";
  await ui.get("create-form").fire("submit");
  resolveOldList([]);
  await oldRefresh;
  assert.equal(ui.get("history-list").children.length, 1);
  assert.equal(ui.get("history-list").children[0].children[0].textContent, "New analysis");
});

test("loads, views safe text, labels mock provenance, and starts empty after last deletion", async () => {
  const memory = createInMemoryAnalysisClient([record(id, "<img src=x>")]);
  const { ui, controller } = setup(memory);
  await controller.refresh();
  assert.equal(ui.get("history-list").children.length, 1, ui.get("crud-status").textContent);
  await ui.get("history-list").children[0].children[2].fire("click");
  const detail = ui.get("detail-content");
  assert.equal(detail.children[0].children[1].textContent, "<img src=x>");
  assert.equal(detail.children[2].children[1].textContent, "Safe explanation <script>");
  assert.match(detail.children[9].children[1].textContent, /Mock/);
  const deleteButton = detail.children.at(-1);
  await deleteButton.fire("click");
  assert.equal(ui.get("delete-confirm").classList.contains("hidden"), false);
  await ui.get("delete-confirm").fire("submit");
  assert.equal(ui.get("history-list").children.length, 0);
  assert.equal(ui.get("empty").classList.contains("hidden"), false);
});

test("unknown AI provenance stays explicitly unknown", async () => {
  const data = record(id); data.analysis_mode = null;
  const { ui, controller } = setup(createInMemoryAnalysisClient([data]));
  await controller.refresh();
  await controller.loadDetail(id);
  assert.match(ui.get("detail-content").children[9].children[1].textContent, /unknown/i);
});

test('library search filters loaded reports and back navigation preserves the query', async () => {
  const first = record(id, 'Account notice');
  const second = record('00000000-0000-4000-8000-000000000002', 'Meeting agenda');
  const memory = createInMemoryAnalysisClient([first, second]);
  const { ui, controller } = setup(memory);
  await controller.refresh();
  ui.get('report-search').value = 'ACCOUNT';
  await ui.get('report-search').fire('input');
  assert.equal(ui.get('history-list').children.length, 1);
  assert.equal(ui.get('report-count').textContent, '1 of 2 reports');
  await controller.loadDetail(id);
  assert.equal(ui.get('reports-list-view').classList.contains('hidden'), true);
  await ui.get('back-to-reports').fire('click');
  assert.equal(ui.get('reports-list-view').classList.contains('hidden'), false);
  assert.equal(ui.get('detail-panel').classList.contains('hidden'), true);
  assert.equal(ui.get('report-search').value, 'ACCOUNT');
  ui.get('report-search').value = 'No matching title';
  await ui.get('report-search').fire('input');
  assert.equal(ui.get('history-list').children.length, 0);
  assert.equal(ui.get('no-report-matches').classList.contains('hidden'), false);
  assert.equal((await memory.listAnalyses()).length, 2);
});

test('returning to the library invalidates a pending detail response', async () => {
  let finish;
  const data = record(id);
  const { ui, controller } = setup({ ...createInMemoryAnalysisClient([data]),
    getAnalysis: () => new Promise(resolve => { finish = resolve; }) });
  const pending = controller.loadDetail(id);
  controller.showLibrary();
  finish(data); await pending;
  assert.equal(ui.get('detail-panel').classList.contains('hidden'), true);
  assert.equal(ui.get('reports-list-view').classList.contains('hidden'), false);
});

test('search tolerates extra spaces and clears from no results without losing loaded reports', async () => {
  const first = { ...record(id, 'Account notice'), explanation: 'Review the payment\n\nrequest.' };
  const second = record('00000000-0000-4000-8000-000000000002', 'Meeting agenda');
  const { ui, controller } = setup(createInMemoryAnalysisClient([first, second]));
  await controller.refresh();
  ui.get('report-search').value = '  PAYMENT   account  ';
  await ui.get('report-search').fire('input');
  assert.equal(ui.get('history-list').children.length, 1);
  assert.equal(ui.get('clear-report-search').classList.contains('hidden'), false);
  ui.get('report-search').value = 'No matching report';
  await ui.get('report-search').fire('input');
  assert.equal(ui.get('no-report-matches').classList.contains('hidden'), false);
  await ui.get('reset-report-search').fire('click');
  assert.equal(ui.get('history-list').children.length, 2);
  assert.equal(ui.get('report-search').focused, true);
  assert.equal(ui.get('clear-report-search').classList.contains('hidden'), true);
  ui.get('report-search').value = 'Meeting';
  await ui.get('report-search').fire('input');
  await ui.get('report-search').fire('keydown', { key: 'Escape' });
  assert.equal(ui.get('history-list').children.length, 2);
  assert.equal(ui.get('report-search').value, '');
});

test("saved report uncertainty and missing results are described without inventing a verdict", async () => {
  const data = record(id);
  data.prediction = null;
  data.confidence = null;
  data.risk_level = null;
  data.explanation = null;
  data.threat_indicators = [];
  data.analysis_mode = "unknown";
  data.analysis_provenance = { provider_mode: "unknown", model: "fixture-model" };
  const { ui, controller } = setup(createInMemoryAnalysisClient([data]));
  await controller.loadDetail(id);
  const detail = ui.get("detail-content");
  assert.equal(detail.children[3].children[1].textContent, "Not analyzed yet");
  assert.match(detail.children[2].children[1].textContent, /not been analyzed/i);
  assert.match(detail.children[4].children[1].textContent, /not assessed/i);
  assert.match(detail.children[5].children[1].textContent, /Not provided/);
  assert.match(detail.children[6].children[1].textContent, /not been analyzed/i);
  assert.match(detail.children[9].children[1].textContent, /source unknown/i);
  assert.doesNotMatch(detail.children[9].children[1].textContent, /fixture-model/);
});

test("provider provenance is labeled explicitly", async () => {
  const data = record(id);
  data.analysis_mode = "real";
  data.analysis_provenance = { provider_mode: "gemini", model: "fixture-gemini-model", model_revision: "fixture-revision" };
  const { ui, controller } = setup(createInMemoryAnalysisClient([data]));
  await controller.loadDetail(id);
  const text = ui.get("detail-content").children[9].children[1].textContent;
  assert.match(text, /Automated analysis/);
  assert.doesNotMatch(text, /fixture-gemini-model|fixture-revision/);
});

test("edit cancel and delete cancel preserve the saved record", async () => {
  const memory = createInMemoryAnalysisClient([record(id)]);
  const { ui, controller } = setup(memory);
  await controller.refresh(); await controller.loadDetail(id);
  assert.equal(ui.get("detail-heading").focused, true);
  const editButton = ui.get("detail-content").children.at(-2);
  await editButton.fire("click");
  assert.equal(ui.get("edit-notes").focused, true);
  ui.get("edit-notes").value = "unsaved";
  await ui.get("cancel-edit").fire("click");
  assert.equal(ui.get("detail-content").children.at(-2).focused, true);
  assert.equal((await memory.getAnalysis(id)).notes, null);
  const deleteButton = ui.get("detail-content").children.at(-1);
  await deleteButton.fire("click");
  assert.equal(ui.get("delete-heading").focused, true);
  await ui.get("cancel-delete").fire("click");
  assert.equal(ui.get("detail-content").children.at(-1).focused, true);
  assert.equal((await memory.listAnalyses()).length, 1);
});

test("editing notes alone preserves null feedback", async () => {
  const nullable = record(id);
  nullable.feedback = null;
  const memory = createInMemoryAnalysisClient([nullable]);
  const { ui, controller } = setup(memory);
  await controller.refresh();
  await controller.loadDetail(id);
  assert.equal(ui.get("detail-content").children[8].children[1].textContent, "No feedback provided");
  await ui.get("detail-content").children.at(-2).fire("click");
  assert.equal(ui.get("edit-feedback").value, "none");
  ui.get("edit-notes").value = "Notes only";
  await ui.get("edit-form").fire("submit");
  const updated = await memory.getAnalysis(id);
  assert.equal(updated.notes, "Notes only");
  assert.equal(updated.feedback, null);
});

test("unknown feedback is labeled unavailable", async () => {
  const invalid = record(id);
  invalid.feedback = "unrecognized";
  const { ui, controller } = setup(createInMemoryAnalysisClient([invalid]));
  await controller.loadDetail(id);
  assert.equal(ui.get("detail-content").children[8].children[1].textContent, "Feedback unavailable");
});

test('the single no-feedback choice clears a correction and remains unchanged for notes-only edits', async () => {
  const original = { ...record(id), feedback: 'false_positive' };
  const memory = createInMemoryAnalysisClient([original]);
  const { ui, controller } = setup(memory);
  await controller.loadDetail(id);
  await ui.get('detail-content').children.at(-2).fire('click');
  assert.equal(ui.get('edit-correction').open, true);
  ui.get('edit-feedback').value = 'none';
  await ui.get('edit-form').fire('submit');
  assert.equal((await memory.getAnalysis(id)).feedback, 'none');
  await ui.get('detail-content').children.at(-2).fire('click');
  assert.equal(ui.get('edit-correction').open, false);
  ui.get('edit-notes').value = 'Contacted the sender.';
  await ui.get('edit-form').fire('submit');
  const updated = await memory.getAnalysis(id);
  assert.equal(updated.feedback, 'none');
  assert.equal(updated.prediction, original.prediction);
});

test("notes and feedback stay disabled until edit save settles", async () => {
  let resolveUpdate;
  const original = record(id, "Pending edit");
  let submitted;
  const client = {
    ...createInMemoryAnalysisClient([original]),
    updateAnalysis(_id, patch) {
      submitted = patch;
      return new Promise(resolve => { resolveUpdate = () => resolve({ ...original, ...patch }); });
    }
  };
  const { ui, controller } = setup(client);
  await controller.loadDetail(id);
  await ui.get("detail-content").children.at(-2).fire("click");
  ui.get("edit-notes").value = "Draft saved";
  ui.get("edit-feedback").value = "false_positive";

  const saving = ui.get("edit-form").fire("submit");
  assert.equal(ui.get("edit-notes").disabled, true);
  assert.equal(ui.get("edit-feedback").disabled, true);
  assert.equal(ui.get("edit-notes").value, "Draft saved");
  assert.equal(ui.get("edit-feedback").value, "false_positive");
  assert.deepEqual(submitted, { notes: "Draft saved", feedback: "false_positive" });
  resolveUpdate();
  await saving;
  assert.equal(ui.get("edit-notes").disabled, false);
  assert.equal(ui.get("edit-feedback").disabled, false);
  assert.equal(ui.get("detail-content").children[7].children[1].textContent, "Draft saved");
  assert.equal(ui.get("detail-content").children[8].children[1].textContent,
    "Flagged, but I think it’s legitimate");
});

test("a delayed older detail response cannot replace an open editor draft", async () => {
  let resolveOlder;
  const selected = record(id, "Selected");
  const client = {
    ...createInMemoryAnalysisClient([selected]),
    getAnalysis(recordId) {
      if (recordId === "older") return new Promise(resolve => { resolveOlder = resolve; });
      return Promise.resolve(selected);
    }
  };
  const { ui, controller } = setup(client);
  const olderRead = controller.loadDetail("older");
  await Promise.resolve();
  await controller.loadDetail(id);
  await ui.get("detail-content").children.at(-2).fire("click");
  ui.get("edit-notes").value = "Unsaved editor draft";

  resolveOlder(record("older", "Older response"));
  await olderRead;

  assert.equal(ui.get("edit-form").classList.contains("hidden"), false);
  assert.equal(ui.get("edit-notes").value, "Unsaved editor draft");
  assert.equal(ui.get("detail-content").children[0].children[1].textContent, "Selected");
});
test("create subject and body stay disabled until save settles", async () => {
  let resolveCreate;
  const saved = record("created", "New draft");
  const client = {
    ...createInMemoryAnalysisClient(),
    createAnalysis() { return new Promise(resolve => { resolveCreate = resolve; }); },
    async listAnalyses() { return [saved]; },
    async getAnalysis() { return saved; }
  };
  const { ui } = setup(client);
  ui.get("create-subject").value = "New draft";
  ui.get("create-body").value = "Synthetic body";
  const saving = ui.get("create-form").fire("submit");
  assert.equal(ui.get("create-subject").disabled, true);
  assert.equal(ui.get("create-body").disabled, true);
  resolveCreate(saved);
  await saving;
  assert.equal(ui.get("create-subject").disabled, false);
  assert.equal(ui.get("create-body").disabled, false);
});

test("failed post-create history refresh warning is not replaced by detail success", async () => {
  const saved = record("created", "Saved but refresh unavailable");
  const client = {
    ...createInMemoryAnalysisClient(),
    async createAnalysis() { return saved; },
    async listAnalyses() { throw new Error("Server unavailable"); },
    async getAnalysis() { return saved; }
  };
  const { ui } = setup(client);
  ui.get("create-body").value = "Synthetic email body";
  await ui.get("create-form").fire("submit");
  assert.match(ui.get("crud-status").textContent, /Saved analyses are unavailable: Server unavailable/);
  assert.doesNotMatch(ui.get("crud-status").textContent, /details loaded|saved successfully/i);
});

test("create and edit submit through the injected five-method client", async () => {
  const client = createInMemoryAnalysisClient();
  const { ui, controller } = setup(client);
  await controller.refresh();
  ui.get("create-subject").value = "Test subject";
  ui.get("create-body").value = "Email body";
  await ui.get("create-form").fire("submit");
  const saved = (await client.listAnalyses())[0];
  assert.equal(saved.subject, "Test subject");
  assert.equal(saved.body, "Email body");
  assert.equal(ui.get("detail-heading").focused, true);
  await controller.loadDetail(saved.id);
  const editButton = ui.get("detail-content").children.at(-2);
  await editButton.fire("click");
  ui.get("edit-notes").value = "Reviewed";
  ui.get("edit-feedback").value = "false_positive";
  await ui.get("edit-form").fire("submit");
  assert.equal((await client.getAnalysis(saved.id)).notes, "Reviewed");
  assert.equal((await client.getAnalysis(saved.id)).feedback, "false_positive");
});

test("failed create preserves input and duplicate pending submit is ignored", async () => {
  let release;
  let creates = 0;
  const base = createInMemoryAnalysisClient();
  const client = { ...base, async createAnalysis(input) {
    creates++;
    if (creates === 1) throw new Error("unavailable");
    await new Promise(resolve => { release = resolve; });
    return base.createAnalysis(input);
  } };
  const { ui } = setup(client);
  ui.get("create-subject").value = "Keep me";
  ui.get("create-body").value = "Keep this body";
  await ui.get("create-form").fire("submit");
  assert.equal(ui.get("create-body").value, "Keep this body");
  assert.equal(ui.get("create-subject").disabled, false);
  assert.equal(ui.get("create-body").disabled, false);
  const first = ui.get("create-form").fire("submit");
  const second = ui.get("create-form").fire("submit");
  await Promise.resolve();
  assert.equal(creates, 2);
  assert.equal(ui.get("create-subject").disabled, true);
  assert.equal(ui.get("create-body").disabled, true);
  release(); await Promise.all([first, second]);
  assert.equal(ui.get("create-subject").disabled, false);
  assert.equal(ui.get("create-body").disabled, false);
});

test("empty body validation focuses the field and never calls create", async () => {
  let calls = 0;
  const client = { ...createInMemoryAnalysisClient(), async createAnalysis() { calls++; } };
  const { ui } = setup(client);
  await ui.get("create-form").fire("submit");
  assert.equal(calls, 0);
  assert.equal(ui.get("create-body").focused, true);
  assert.match(ui.get("crud-status").textContent, /required|Enter/i);
});

test("an unavailable refresh preserves the last loaded records", async () => {
  let requests = 0;
  const base = createInMemoryAnalysisClient([record(id)]);
  const client = { ...base, async listAnalyses() {
    requests++;
    if (requests > 1) throw new Error("Server unavailable");
    return base.listAnalyses();
  } };
  const { ui, controller } = setup(client);
  await controller.refresh();
  await controller.refresh();
  assert.equal(ui.get("history-list").children.length, 1);
  assert.match(ui.get("crud-status").textContent, /unavailable/i);
});

test("loading remains visible while listing is pending, then shows empty state", async () => {
  let resolveList;
  const client = { ...createInMemoryAnalysisClient(), listAnalyses: () => new Promise(resolve => { resolveList = resolve; }) };
  const { ui, controller } = setup(client);
  const pending = controller.refresh();
  assert.equal(ui.get("loading").classList.contains("hidden"), false);
  resolveList([]);
  await pending;
  assert.equal(ui.get("loading").classList.contains("hidden"), true);
  assert.equal(ui.get("empty").classList.contains("hidden"), false);
});

test("malformed list responses have a distinct message instead of an empty state", async () => {
  const client = { ...createInMemoryAnalysisClient(), async listAnalyses() { throw new SyntaxError("Invalid JSON"); } };
  const { ui, controller } = setup(client);
  await controller.refresh();
  assert.match(ui.get("crud-status").textContent, /malformed/i);
  assert.equal(ui.get("empty").classList.contains("hidden"), true);
});

test("a detail read pending before deletion cannot reopen the deleted record", async () => {
  const original = record(id, "Deleted");
  let resolveLate;
  const client = {
    ...createInMemoryAnalysisClient([original]),
    getAnalysis(recordId) {
      if (recordId === "older") return new Promise(resolve => { resolveLate = resolve; });
      return Promise.resolve(original);
    },
    async deleteAnalysis() {},
    async listAnalyses() { return []; }
  };
  const { ui, controller } = setup(client);
  const lateRead = controller.loadDetail("older");
  await Promise.resolve();
  await controller.loadDetail(id);
  await ui.get("detail-content").children.at(-1).fire("click");
  await ui.get("delete-confirm").fire("submit");
  resolveLate(record("older", "Late response"));
  await lateRead;
  assert.equal(ui.get("detail-panel").classList.contains("hidden"), true);
  assert.equal(ui.get("history-list").children.length, 0);
});

test("TF-IDF saved reports show their provider and preserve model identity", async () => {
  const data = record(id);
  data.analysis_mode = "real";
  data.analysis_provenance = { provider_mode: "tfidf", model: "word_plus_char_wb_C1p0", model_revision: "fixture-tfidf-revision" };
  const { ui, controller } = setup(createInMemoryAnalysisClient([data]));
  await controller.loadDetail(id);
  const text = ui.get("detail-content").children[9].children[1].textContent;
  assert.match(text, /Provider: TF-IDF/);
  assert.match(text, /Model: word_plus_char_wb_C1p0/);
  assert.match(text, /fixture-tfidf-revision/);
  assert.doesNotMatch(text, /Unrecognized/);
});

import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { connectContextAnalysis, createPopupController, renderContextAnalysis } from "../js/popup.js";
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

const ids = ["crud-status", "history-list", "empty", "loading", "create-form", "create-subject", "create-body", "detail-panel", "detail-content", "edit-form", "edit-notes", "edit-feedback", "delete-confirm", "delete-subject", "confirm-delete", "cancel-delete", "cancel-edit", "save-edit", "create-button", "empty-state", "loading-state", "error-state", "result-state", "error-message", "classification", "risk-level", "analysis-mode", "selected-text", "tactics", "recommendations", "clear-button"];
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

 test("HTML provides associated labels, focusable CRUD controls, and a bounded popup", async () => {
  const html = await readFile(new URL("../popup.html", import.meta.url), "utf8");
  const css = await readFile(new URL("../css/popup.css", import.meta.url), "utf8");
  const popup = await readFile(new URL("../js/popup.js", import.meta.url), "utf8");
  for (const [label, control] of [["create-subject", "create-subject"], ["create-body", "create-body"], ["edit-notes", "edit-notes"], ["edit-feedback", "edit-feedback"]]) {
    assert.match(html, new RegExp(`<label for="${label}">`));
    assert.match(html, new RegExp(`id="${control}"`));
  }
  assert.match(html, /role="status" aria-live="polite"/);
  assert.match(html, /id="edit-notes"[^>]*maxlength="2000"/);
  assert.match(html, /Analyze selection with VeriQo/);
  assert.doesNotMatch(html, /Analyze selection with PhishLens/);
  for (const id of ["empty-state", "loading-state", "error-state", "result-state", "clear-button"]) assert.match(html, new RegExp(`id="${id}"`));
  assert.match(css, /width:\s*380px/);
  assert.match(css, /max-height:\s*600px/);
  assert.match(css, /overflow-y:\s*auto/);
  assert.match(popup, /createAnalysisClient\(API_BASE_URL\)/);
  assert.doesNotMatch(popup, /in-memory-analysis-client/);
});

test("context-menu result, error, and Clear remain available beside CRUD", async () => {
  const { ui } = setup(createInMemoryAnalysisClient());
  renderContextAnalysis({ status: "success", selectedText: "Selected message", result: {
    classification: "phishing", risk_level: "high", mode: "mock", tactics: ["Urgency"], recommendations: ["Verify sender"]
  } }, { getElementById: id => ui.get(id), createElement: tag => Object.assign(new Element(), { tagName: tag }) });
  assert.equal(ui.get("result-state").classList.contains("hidden"), false);
  assert.equal(ui.get("classification").textContent, "phishing");
  assert.equal(ui.get("selected-text").textContent, "Selected message");
  assert.equal(ui.get("tactics").children[0].textContent, "Urgency");
  renderContextAnalysis({ status: "error", error: "Backend unavailable" }, { getElementById: id => ui.get(id), createElement: tag => Object.assign(new Element(), { tagName: tag }) });
  assert.equal(ui.get("error-message").textContent, "Backend unavailable");

  let cleared;
  const doc = { getElementById: id => ui.get(id), createElement: tag => Object.assign(new Element(), { tagName: tag }) };
  const chromeApi = {
    storage: { session: { get: async () => ({ veriqoAnalysis: null }) }, onChanged: { addListener() {} } },
    runtime: { sendMessage: async message => { cleared = message; return { ok: true }; } }
  };
  connectContextAnalysis(chromeApi, doc);
  await ui.get("clear-button").fire("click");
  assert.deepEqual(cleared, { type: "phishlens-clear-analysis" });
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

test("real AI provenance is labeled as real", async () => {
  const data = record(id); data.analysis_mode = "real";
  const { ui, controller } = setup(createInMemoryAnalysisClient([data]));
  await controller.loadDetail(id);
  assert.match(ui.get("detail-content").children[9].children[1].textContent, /Real AI/);
});

test("edit cancel and delete cancel preserve the saved record", async () => {
  const memory = createInMemoryAnalysisClient([record(id)]);
  const { ui, controller } = setup(memory);
  await controller.refresh(); await controller.loadDetail(id);
  const editButton = ui.get("detail-content").children.at(-2);
  await editButton.fire("click");
  ui.get("edit-notes").value = "unsaved";
  await ui.get("cancel-edit").fire("click");
  assert.equal((await memory.getAnalysis(id)).notes, null);
  const deleteButton = ui.get("detail-content").children.at(-1);
  await deleteButton.fire("click");
  await ui.get("cancel-delete").fire("click");
  assert.equal((await memory.listAnalyses()).length, 1);
});

test("editing notes alone preserves null feedback", async () => {
  const nullable = record(id);
  nullable.feedback = null;
  const memory = createInMemoryAnalysisClient([nullable]);
  const { ui, controller } = setup(memory);
  await controller.refresh();
  await controller.loadDetail(id);
  await ui.get("detail-content").children.at(-2).fire("click");
  assert.equal(ui.get("edit-feedback").value, "null");
  ui.get("edit-notes").value = "Notes only";
  await ui.get("edit-form").fire("submit");
  const updated = await memory.getAnalysis(id);
  assert.equal(updated.notes, "Notes only");
  assert.equal(updated.feedback, null);
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
  const first = ui.get("create-form").fire("submit");
  const second = ui.get("create-form").fire("submit");
  await Promise.resolve();
  assert.equal(creates, 2);
  release(); await Promise.all([first, second]);
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

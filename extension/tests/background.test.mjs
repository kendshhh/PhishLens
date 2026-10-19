import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import vm from "node:vm";

const source = await readFile(new URL("../background.js", import.meta.url), "utf8");
const { API_BASE_URL } = await import("../js/config.js");
assert.ok(source.startsWith('import { API_BASE_URL } from "./js/config.js";'));
const workerSource = source.replace('import { API_BASE_URL } from "./js/config.js";', "");

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((done, fail) => { resolve = done; reject = fail; });
  return { promise, resolve, reject };
}

function worker({ firstWrite } = {}) {
  const requests = [];
  const state = { analysis: undefined, badge: "" };
  let onMessage;
  let writes = 0;
  const timers = new Map();
  const context = vm.createContext({
    API_BASE_URL,
    AbortController,
    setTimeout(callback, delay) {
      const id = Symbol();
      timers.set(id, { callback, delay });
      return id;
    },
    clearTimeout(id) { timers.delete(id); },
    console: { error() {} },
    fetch: async (_url, options) => {
      assert.equal(_url, `${API_BASE_URL}/analyses`);
      const request = deferred();
      request.signal = options.signal;
      requests.push(request);
      return request.promise;
    },
    chrome: {
      runtime: {
        onInstalled: { addListener() {} },
        onMessage: { addListener(listener) { onMessage = listener; } }
      },
      contextMenus: { onClicked: { addListener() {} } },
      storage: { session: {
        async set(value) {
          if (writes++ === 0 && firstWrite) await firstWrite.promise;
          state.analysis = value.veriqoAnalysis;
        },
        async remove() { state.analysis = undefined; }
      } },
      action: { async setBadgeText({ text }) { state.badge = text; } }
    }
  });
  vm.runInContext(workerSource, context);
  return {
    state, requests, timers,
    expire: () => {
      for (const { callback, delay } of [...timers.values()]) {
        assert.equal(delay, 25_000);
        callback();
      }
    },
    analyze: text => context.analyzeSelectedText(text),
    clear: () => new Promise(resolve => {
      assert.equal(onMessage({ type: "phishlens-clear-analysis" }, {}, resolve), true);
    })
  };
}

const settle = () => new Promise(resolve => setImmediate(resolve));
const success = classification => ({ ok: true, json: async () => ({ classification }) });

for (const staleOutcome of ["success", "error"]) {
  test(`older ${staleOutcome} cannot replace the latest analysis or badge`, async () => {
    const app = worker();
    const older = app.analyze("Email A");
    await settle();
    const newer = app.analyze("Email B");
    await settle();
    app.requests[1].resolve(success("phishing"));
    await newer;
    if (staleOutcome === "success") app.requests[0].resolve(success("legitimate"));
    else app.requests[0].reject(new Error("Old request failed"));
    await older;
    assert.equal(app.state.analysis.selectedText, "Email B");
    assert.equal(app.state.analysis.result.classification, "phishing");
    assert.equal(app.state.badge, "✓");
  });

  test(`Clear invalidates an in-flight ${staleOutcome}`, async () => {
    const app = worker();
    const pending = app.analyze("Email A");
    await settle();
    assert.equal((await app.clear()).ok, true);
    if (staleOutcome === "success") app.requests[0].resolve(success("phishing"));
    else app.requests[0].reject(new Error("Cleared request failed"));
    await pending;
    assert.equal(app.state.analysis, undefined);
    assert.equal(app.state.badge, "");
  });
}

test("Clear waits for a pending storage write and prevents stale badges", async () => {
  const firstWrite = deferred();
  const app = worker({ firstWrite });
  const pending = app.analyze("Email A");
  await settle();
  const cleared = app.clear();
  firstWrite.resolve();
  await pending;
  await cleared;
  assert.equal(app.requests.length, 0);
  assert.equal(app.state.analysis, undefined);
  assert.equal(app.state.badge, "");
});

test("a new analysis works after Clear", async () => {
  const app = worker();
  await app.clear();
  const pending = app.analyze("Email B");
  await settle();
  app.requests[0].resolve(success("legitimate"));
  await pending;
  assert.equal(app.state.analysis.selectedText, "Email B");
  assert.equal(app.state.badge, "✓");
});

test("timeout aborts a stalled request, saves a retryable error, and allows retry", async () => {
  const app = worker();
  const pending = app.analyze("Email A");
  await settle();
  app.expire();
  await pending;
  assert.equal(app.requests[0].signal.aborted, true);
  assert.equal(app.state.analysis.status, "error");
  assert.match(app.state.analysis.error, /timed out.*try again/);
  assert.equal(app.state.badge, "!");
  assert.equal(app.timers.size, 0);
  const retry = app.analyze("Email B");
  await settle();
  app.requests[1].resolve(success("legitimate"));
  await retry;
  app.requests[0].resolve(success("phishing"));
  await settle();
  assert.equal(app.state.analysis.selectedText, "Email B");
  assert.equal(app.state.analysis.status, "success");
  assert.equal(app.state.badge, "✓");
  assert.equal(app.timers.size, 0);
});

test("deadline also covers stalled response bodies", async () => {
  const app = worker();
  const pending = app.analyze("Email A");
  await settle();
  const body = deferred();
  app.requests[0].resolve({ ok: true, json: () => body.promise });
  await settle();
  app.expire();
  await pending;
  assert.equal(app.state.analysis.status, "error");
  body.resolve({ classification: "phishing" });
  await settle();
  assert.equal(app.state.analysis.status, "error");
});

test("timeout after Clear cannot restore cleared state", async () => {
  const app = worker();
  const pending = app.analyze("Email A");
  await settle();
  await app.clear();
  app.expire();
  await pending;
  assert.equal(app.state.analysis, undefined);
  assert.equal(app.state.badge, "");
});

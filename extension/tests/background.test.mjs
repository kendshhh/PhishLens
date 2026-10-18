import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import vm from "node:vm";

const source = await readFile(new URL("../background.js", import.meta.url), "utf8");

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
  const context = vm.createContext({
    console: { error() {} },
    fetch: async () => {
      const request = deferred();
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
  vm.runInContext(source, context);
  return {
    state, requests,
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

import test from "node:test";
import assert from "node:assert/strict";

function element() {
  const classes = new Set(["hidden"]);
  return {
    textContent: "",
    children: [],
    classList: {
      add: value => classes.add(value),
      remove: value => classes.delete(value),
      contains: value => classes.has(value)
    },
    appendChild(child) { this.children.push(child); }
  };
}

for (const scenario of ["saved", "empty", "invalid"]) {
  test(`popup handles the API envelope: ${scenario}`, async (t) => {
    const previousDocument = globalThis.document;
    const previousFetch = globalThis.fetch;
    t.after(() => {
      globalThis.document = previousDocument;
      globalThis.fetch = previousFetch;
    });
    const nodes = Object.fromEntries(
      ["loading", "error", "empty", "history-list"].map(id => [id, element()])
    );
    nodes.loading.classList.remove("hidden");
    let onReady;
    globalThis.document = {
      addEventListener: (_name, handler) => { onReady = handler; },
      getElementById: id => nodes[id],
      createElement: () => element()
    };
    const subject = '<img src=x onerror="alert(1)">';
    const data = scenario === "saved"
      ? { items: [{ subject, risk_level: "high" }] }
      : scenario === "empty" ? { items: [] } : { wrong_field: [] };
    globalThis.fetch = async () => ({ ok: true, json: async () => data });
    await import(`../js/popup.js?scenario=${scenario}`);
    await onReady();
    assert.equal(nodes.loading.classList.contains("hidden"), true);
    if (scenario === "saved") {
      assert.equal(nodes["history-list"].children.length, 1);
      assert.equal(nodes["history-list"].children[0].textContent, `Subject: ${subject} | Risk: high`);
      assert.equal(nodes.empty.classList.contains("hidden"), true);
    } else if (scenario === "empty") {
      assert.equal(nodes.empty.classList.contains("hidden"), false);
    } else {
      assert.match(nodes.error.textContent, /Invalid history data/);
      assert.equal(nodes.error.classList.contains("hidden"), false);
    }
  });
}

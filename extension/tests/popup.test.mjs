import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { API_BASE_URL } from "../js/config.js";

// Execute the actual popup entry point with a small DOM fixture, not a copy
// of its rendering logic. All requests are mocked; no production calls occur.
let sequence = 0;
async function openPopup(t, response) {
  const html = await readFile(new URL("../popup.html", import.meta.url), "utf8");
  assert.match(html, /src="js\/popup\.js"/);
  const elements = new Map();
  for (const [, id, classes = ""] of html.matchAll(/id="([^"]+)"(?: class="([^"]*)")?/g)) {
    const names = new Set(classes.split(/\s+/));
    elements.set(id, {
      textContent: "",
      children: [],
      classList: {
        add: name => names.add(name),
        remove: name => names.delete(name),
        contains: name => names.has(name)
      },
      appendChild(child) { this.children.push(child); }
    });
  }
  const oldDocument = globalThis.document;
  const oldFetch = globalThis.fetch;
  t.after(() => {
    globalThis.document = oldDocument;
    globalThis.fetch = oldFetch;
  });
  let onReady;
  globalThis.document = {
    addEventListener(event, callback) {
      assert.equal(event, "DOMContentLoaded");
      onReady = callback;
    },
    getElementById: id => elements.get(id),
    createElement: tag => ({ tagName: tag, textContent: "" })
  };
  globalThis.fetch = async (url, options) => {
    assert.equal(url, `${API_BASE_URL}/api/analyses`);
    assert.ok(options.signal);
    return response;
  };
  await import(`../js/popup.js?test=${sequence++}`);
  await onReady();
  return elements;
}

test("popup renders the seeded API envelope safely with acceptance fields", async t => {
  const subject = "Synthetic account notice <img src=x onerror=alert(1)>";
  const dom = await openPopup(t, { ok: true, json: async () => ({ items: [{
    subject, prediction: "phishing", risk_level: "high", confidence: 0.93
  }] }) });
  const rows = dom.get("history-list").children;
  assert.equal(rows.length, 1);
  assert.equal(rows[0].textContent,
    `Subject: ${subject} | Prediction: phishing | Risk: high | Confidence: 93%`);
  assert.ok(dom.get("loading").classList.contains("hidden"));
  assert.ok(dom.get("empty").classList.contains("hidden"));
  assert.ok(dom.get("error").classList.contains("hidden"));
});

test("popup displays empty state only for an empty items array", async t => {
  const dom = await openPopup(t, { ok: true, json: async () => ({ items: [] }) });
  assert.equal(dom.get("history-list").children.length, 0);
  assert.equal(dom.get("empty").classList.contains("hidden"), false);
  assert.ok(dom.get("loading").classList.contains("hidden"));
});

test("popup treats malformed envelopes as errors instead of empty history", async t => {
  const dom = await openPopup(t, { ok: true, json: async () => ({ wrong: [] }) });
  assert.match(dom.get("error").textContent, /Invalid history data/);
  assert.equal(dom.get("error").classList.contains("hidden"), false);
  assert.ok(dom.get("empty").classList.contains("hidden"));
  assert.ok(dom.get("loading").classList.contains("hidden"));
});

test("popup displays failed requests as errors", async t => {
  const dom = await openPopup(t, { ok: false, status: 500 });
  assert.match(dom.get("error").textContent, /Failed to load history/);
  assert.equal(dom.get("error").classList.contains("hidden"), false);
  assert.ok(dom.get("empty").classList.contains("hidden"));
});

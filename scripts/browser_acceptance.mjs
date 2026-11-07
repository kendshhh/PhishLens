import assert from "node:assert/strict";
import { createServer } from "node:http";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { appendFile, mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";
import { MODEL_SHA256 } from "../extension/ai/local-analyzer.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const packagePath = path.join(root, "output", "extension", "PhishLens-Extension.zip");
const evidencePath = path.join(root, "output", "extension", "browser-acceptance.json");
const expectedTests = [
  "packaged popup loads synthetic history in the browser",
  "selection handler opens the action popup with the highlighted text",
  "synthetic analysis shows a clearly labeled local result or readable error",
  "local scan saves once and keeps its title and save marker after popup reload",
  "Clear during a local scan prevents a stale result from returning",
  "Cancel retains the selection and retry recovers from a controlled local failure",
  "synthetic saved analysis can be created and viewed",
  "synthetic saved analysis can be edited and deleted",
  "empty history and history API failure states render clearly",
];
let sourceCommit = process.env.SOURCE_COMMIT ?? null;
let testedCommit = process.env.GITHUB_SHA ?? null;
const evidence = {
  source_commit: sourceCommit ?? "unknown",
  tested_commit: testedCommit ?? "unknown",
  environment: "isolated synthetic browser",
  scope: "The exact packaged extension archive is unpacked into a disposable browser profile and checked against its SHA-256 sidecar. Playwright uses bundled Chromium and falls back to installed Edge on Windows when bundled Chromium cannot launch. The API origin/host permission are redirected only to a local synthetic server. Browser tests cover local-scan presentation, a test-only delayed stale completion through the production Clear handler, and synthetic saved-report CRUD. Native context-menu behavior is covered by extension unit tests; no real provider or production data is used.",
  tests: [],
  result: "failed",
};

const seededRecord = {
  id: "29d80c39-ec0d-4db8-a6e5-87444ba2600c",
  subject: "Synthetic account notice",
  prediction: "phishing",
  confidence: 0.93,
  risk_level: "high",
  threat_indicators: [],
  explanation: "Synthetic browser acceptance record",
  created_at: "2026-10-14T04:00:00Z",
  body: "Synthetic history content. No personal data.",
  notes: null,
  feedback: "none",
  analysis_mode: "mock",
  analysis_provenance: {
    provider_mode: "mock",
    model: null,
    model_revision: null,
    prompt_version: null,
    explanation_source: "mock",
    input_truncated: false,
    windows_processed: null,
  },
};

let historyMode = "seeded";
const records = new Map([[seededRecord.id, structuredClone(seededRecord)]]);
let createdRecordId = null;
const formattedSelection = 'Synthetic test: account closes today; enter your password at example.invalid\n\n' +
  '  Meeting notes:\n\tReview the agenda.\n\n' +
  Array.from({ length: 12 }, (_, index) => `  Item ${index + 1}: synthetic content.`).join('\n') +
  '\n\nRegards,\n  Synthetic sender';

function sendJson(response, status, body) {
  response.writeHead(status, { "content-type": "application/json" });
  response.end(JSON.stringify(body));
}

const server = createServer(async (request, response) => {
  if (request.url === "/__test/selection" && request.method === "GET") {
    response.writeHead(200, { "content-type": "text/html; charset=utf-8" });
    response.end('<!doctype html><html lang="en"><title>Synthetic selection</title><pre id="email">' + formattedSelection + '</pre></html>');
    return;
  }
  if (request.url === "/model-info" && request.method === "GET") {
    sendJson(response, 200, { provider_mode: "tfidf", model_sha256: MODEL_SHA256,
      accepts_tfidf_reports: true, accepts_local_reviews: true });
    return;
  }
  if (request.method === "POST" && request.url === "/__test/state") {
    let body = "";
    for await (const chunk of request) body += chunk;
    const state = JSON.parse(body || "{}");
    historyMode = state.historyMode ?? historyMode;
    sendJson(response, 200, { ok: true });
    return;
  }

  if (request.url === "/api/analyses" && request.method === "GET") {
    if (historyMode === "error") {
      sendJson(response, 503, { detail: "Synthetic history failure" });
    } else {
      sendJson(response, 200, {
        items: historyMode === "seeded" ? [...records.values()] : [],
      });
    }
    return;
  }

  if (request.url === "/api/analyses" && request.method === "POST") {
    let body = "";
    for await (const chunk of request) body += chunk;
    const payload = JSON.parse(body || "{}");
    const record = {
      ...structuredClone(seededRecord),
      id: crypto.randomUUID(),
      subject: payload.subject,
      body: payload.body,
      created_at: new Date().toISOString(),
    };
    records.set(record.id, record);
    createdRecordId = record.id;
    sendJson(response, 201, record);
    return;
  }

  const recordMatch = request.url.match(/^\/api\/analyses\/([0-9a-f-]{36})$/i);
  if (recordMatch) {
    const record = records.get(recordMatch[1]);
    if (!record) {
      sendJson(response, 404, { detail: "Synthetic record not found" });
      return;
    }
    if (request.method === "GET") {
      sendJson(response, 200, record);
      return;
    }
    if (request.method === "PATCH") {
      let body = "";
      for await (const chunk of request) body += chunk;
      Object.assign(record, JSON.parse(body || "{}"));
      sendJson(response, 200, record);
      return;
    }
    if (request.method === "DELETE") {
      records.delete(recordMatch[1]);
      response.writeHead(204);
      response.end();
      return;
    }
  }

  if (request.url === "/api/analyses" && request.method === "OPTIONS") {
    response.writeHead(204);
    response.end();
    return;
  }

  sendJson(response, 404, { detail: "Unexpected synthetic request" });
});

async function writeEvidence() {
  await mkdir(path.dirname(evidencePath), { recursive: true });
  await writeFile(evidencePath, JSON.stringify(evidence, null, 2) + "\n", "utf8");

  const summaryPath = process.env.GITHUB_STEP_SUMMARY;
  if (!summaryPath) return;
  const outcome = evidence.result === "passed" ? "PASS" : "FAIL";
  const browser = evidence.browser_channel
    ? `${evidence.browser_channel} ${evidence.browser_version ?? ""}`.trim()
    : "not started";
  const lines = [
    `## Packaged extension browser acceptance — ${outcome}`,
    "",
    `- Source commit: \`${evidence.source_commit}\``,
    `- Tested commit: \`${evidence.tested_commit}\``,
    `- Browser: ${browser}`,
    "",
    "### Automated scenarios",
    ...expectedTests.map(test => {
      const passed = evidence.tests.includes(test);
      return `- [${passed ? "x" : " "}] ${test}${passed ? "" : " — not completed"}`;
    }),
  ];
  if (evidence.error) lines.push("", `Failure: ${evidence.error.message}`);
  try {
    await appendFile(summaryPath, lines.join("\n") + "\n", "utf8");
  } catch (error) {
    console.warn(`Could not write GitHub step summary: ${error?.message ?? error}`);
  }
}

function makeTestExtension(archivePath, destination, apiOrigin, evidencePath) {
  const prepare = String.raw`
import hashlib
import json, sys
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

archive = Path(sys.argv[1])
target = Path(sys.argv[2]).resolve()
origin = sys.argv[3]
expected = json.loads(Path(sys.argv[4]).read_text(encoding="utf-8"))["files_sha256"]
if not isinstance(expected, dict) or not expected:
    raise SystemExit("Package identity evidence has no file hashes")
with ZipFile(archive) as package:
    bad = package.testzip()
    if bad:
        raise SystemExit(f"Invalid package member: {bad}")
    names = package.namelist()
    if len(names) != len(set(names)) or set(names) != set(expected):
        raise SystemExit("Unexpected extension package contents")
    for asset, expected_sha256 in expected.items():
        relative = PurePosixPath(asset)
        if relative.is_absolute() or ".." in relative.parts or "\\" in asset:
            raise SystemExit("Unsafe extension package path")
        output = (target / Path(*relative.parts)).resolve()
        if not output.is_relative_to(target):
            raise SystemExit("Extension package path escapes the temporary profile")
        content = package.read(asset)
        if hashlib.sha256(content).hexdigest() != expected_sha256:
            raise SystemExit(f"Extension asset digest differs from its sidecar: {asset}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(content)
manifest_path = target / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["host_permissions"] = [origin + "/*"]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
(target / "js" / "config.js").write_text(
    "export const API_BASE_URL = " + json.dumps(origin) + ";\n", encoding="utf-8"
)
worker_path = target / "background.js"
worker = worker_path.read_text(encoding="utf-8")
worker = worker.replace("chrome.contextMenus.onClicked.addListener(",
    "chrome.contextMenus.onClicked.addListener(globalThis.__phishlensTestSelection = ", 1)
worker += """
// Test-only delayed completion to exercise the production Clear generation guard.
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "__phishlens_test_slow_scan") return;
  const generation = ++analysisGeneration;
  const selectedText = "Synthetic delayed scan";
  activeJob = { generation, selectedText, jobId: crypto.randomUUID() };
  void updateAnalysis(generation, { status: "loading", selectedText, result: null, error: null }, "...")
    .then(() => setTimeout(() => {
      void updateAnalysis(generation, {
        status: "error", selectedText, result: null, error: "Synthetic stale completion",
      }, "?").then(() => sendResponse({ ok: true }));
    }, 1000));
  return true;
});
"""
worker_path.write_text(worker, encoding="utf-8")
`;
  const python = process.platform === "win32" ? "py" : (process.env.PYTHON ?? "python3");
  const pythonArgs = process.platform === "win32" ? ["-3.12"] : [];
  execFileSync(python, [...pythonArgs, "-c", prepare, archivePath, destination, apiOrigin, evidencePath], { stdio: "inherit" });
}

async function setState(baseUrl, state) {
  const response = await fetch(`${baseUrl}/__test/state`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(state),
  });
  assert.equal(response.status, 200);
}

async function run() {
  const archive = await readFile(packagePath);
  const packageSha256 = createHash("sha256").update(archive).digest("hex");
  evidence.package_sha256 = packageSha256;
  const identity = JSON.parse(await readFile(
    path.join(root, "output", "extension", "evidence.json"), "utf8"
  ));
  sourceCommit ??= identity.source_commit ?? "unknown";
  testedCommit ??= identity.tested_commit ?? "unknown";
  evidence.source_commit = sourceCommit;
  evidence.tested_commit = testedCommit;
  evidence.runtime_or_packaging_changes = identity.runtime_or_packaging_changes;
  assert.equal(identity.source_commit, sourceCommit, "Package source SHA differs from the PR head");
  assert.equal(identity.archive_sha256, packageSha256, "Package digest differs from its identity evidence");
  evidence.extension_version = identity.extension_version;
  if (process.env.GITHUB_ACTIONS === "true") {
    assert.match(sourceCommit, /^[0-9a-f]{40}$/i, "CI must provide the full PR source SHA");
    assert.match(testedCommit, /^[0-9a-f]{40}$/i, "CI must provide the full tested SHA");
    assert.equal(identity.runtime_or_packaging_changes, false, "CI package inputs must come from a clean checkout");
  }

  const tempRoot = await mkdtemp(path.join(os.tmpdir(), "phishlens-browser-"));
  const extensionPath = path.join(tempRoot, "extension");
  const profilePath = path.join(tempRoot, "chromium-profile");
  let context;

  try {
    await new Promise((resolve, reject) => {
      server.once("error", reject);
      server.listen(0, "127.0.0.1", resolve);
    });
    const address = server.address();
    const apiOrigin = `http://127.0.0.1:${address.port}`;
    makeTestExtension(
      packagePath,
      extensionPath,
      apiOrigin,
      path.join(root, "output", "extension", "evidence.json"),
    );

    const launchOptions = {
      headless: true,
      viewport: { width: 380, height: 600 },
      deviceScaleFactor: 2,
      ignoreDefaultArgs: ["--disable-extensions"],
      args: [
        `--disable-extensions-except=${extensionPath}`,
        `--load-extension=${extensionPath}`,
      ],
    };
    try {
      context = await chromium.launchPersistentContext(profilePath, {
        ...launchOptions,
        channel: "chromium",
      });
      evidence.browser_channel = "chromium";
    } catch (chromiumError) {
      if (process.platform !== "win32") throw chromiumError;
      try {
        context = await chromium.launchPersistentContext(profilePath, {
          ...launchOptions,
          channel: "msedge",
          headless: false,
        });
        evidence.browser_channel = "msedge";
        evidence.browser_launch_fallback = {
          requested: "chromium",
          used: "msedge",
          mode: "headed",
          reason: String(chromiumError?.message ?? chromiumError).split("\n", 1)[0],
        };
      } catch (edgeError) {
        throw new Error(
          `Playwright Chromium failed to start (${chromiumError?.message ?? chromiumError}); ` +
          `the installed Edge fallback also failed (${edgeError?.message ?? edgeError})`,
        );
      }
    }
    const worker = context.serviceWorkers()[0] ?? await context.waitForEvent("serviceworker");
    const extensionId = new URL(worker.url()).host;
    const page = await context.newPage();
    await page.goto(`chrome-extension://${extensionId}/popup.html`);

    await page.locator("#empty-state").waitFor({ state: "visible" });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await page.screenshot({ path: path.join(root, "output", "extension", "ui-check.png") });
    await page.locator("#show-reports").click();
    await page.locator("#load-history").click();
    await page.locator("#history-list li").getByText("Synthetic account notice").waitFor();
    assert.match(await page.locator("#history-list li").textContent(), /phishing/i);
    assert.ok(await page.locator("#history-list time").getAttribute('datetime'));
    assert.match(await page.locator("#history-list .history-preview").textContent(), /Synthetic browser acceptance/);
    await page.evaluate(() => scrollTo(0, 0));
    await page.screenshot({ path: path.join(root, "output", "extension", "ui-history-populated.png") });
    evidence.tests.push("packaged popup loads synthetic history in the browser");

    await page.locator("#show-check").click();
    const sourcePage = await context.newPage();
    await sourcePage.goto(apiOrigin + '/__test/selection');
    await sourcePage.locator('#email').evaluate(element => {
      const range = document.createRange(); range.selectNodeContents(element);
      const selection = getSelection(); selection.removeAllRanges(); selection.addRange(range);
    });
    const sourceTab = await worker.evaluate(async url => (await chrome.tabs.query({})).find(tab => tab.url === url), sourcePage.url());
    assert.ok(sourceTab, 'Synthetic selected-text source tab must exist');
    await worker.evaluate(({ tab, selected }) => {
      void globalThis.__phishlensTestSelection({ menuItemId: 'phishlens-analyze-selection',
        selectionText: selected.replace(/\s+/g, ' '), frameId: 0 }, tab);
    }, { tab: sourceTab, selected: formattedSelection });
    await page.locator("#loading-state").waitFor({ state: "visible" });
    assert.equal(await page.locator("#selection-content").textContent(), formattedSelection);
    await page.waitForFunction(() => {
      const result = document.querySelector("#result-state");
      const error = document.querySelector("#error-state");
      return !result.classList.contains("hidden") || !error.classList.contains("hidden");
    }, undefined, { timeout: 120000 });
    if (await page.locator("#result-state").isVisible()) {
      const label = (await page.locator("#classification").textContent()).trim();
      assert.match(label, /Suspicious|No strong warning signs|Uncertain/i);
      evidence.local_analysis_outcome = label;
    } else {
      const message = (await page.locator("#error-message").textContent()).trim();
      assert.ok(message.length > 0, "Local analysis errors must be readable");
      evidence.local_analysis_outcome = "readable error: " + message.slice(0, 240);
    }
    evidence.tests.push("synthetic analysis shows a clearly labeled local result or readable error");

    assert.equal(await page.locator("#result-state").isVisible(), true, "Packaged TF-IDF scan must produce a local result, including uncertainty");
    assert.equal(await page.locator("#selection-content").textContent(), formattedSelection);
    const preview = await page.locator("#selection-content").evaluate(element => {
      element.scrollTop = 100;
      const result = { height: element.getBoundingClientRect().height, scroll: element.scrollTop,
        overflows: element.scrollHeight > element.clientHeight, whitespace: getComputedStyle(element).whiteSpace };
      element.scrollTop = 0; return result;
    });
    assert.ok(preview.height <= 150 && preview.overflows && preview.scroll > 0, 'Selection preview must retain its height and scroll vertically');
    assert.equal(preview.whitespace, 'break-spaces');
    const popupContexts = await worker.evaluate(() => chrome.runtime.getContexts({ contextTypes: ['POPUP'] }));
    assert.ok(popupContexts.length > 0, 'The selection handler must open the real Chrome action popup');
    evidence.tests.push("selection handler opens the action popup with the highlighted text");
    await page.bringToFront();
    await sourcePage.close();
    await page.evaluate(() => scrollTo(0, 0));
    await page.screenshot({ path: path.join(root, "output", "extension", "ui-selection.png") });
    await page.locator("#classification").focus();
    await page.locator("#result-state").evaluate(element => element.scrollIntoView({ block: "start" }));
    await page.screenshot({ path: path.join(root, "output", "extension", "ui-result.png") });
    await page.locator("#report-subject").fill("Synthetic local scan report");
    await page.locator("#save-consent").check();
    await page.locator("#save-report").click();
    await page.locator("#save-status").getByText("Report saved.").waitFor();
    assert.equal(await page.locator("#save-report").isDisabled(), true);
    await page.screenshot({ path: path.join(root, "output", "extension", "ui-saved.png") });
    await page.locator("#view-saved-report").click();
    await page.locator("#detail-panel").waitFor({ state: "visible" });
    const localSavedId = createdRecordId;
    const savedCount = records.size;
    await page.reload();
    await page.locator("#save-status").getByText(/already saved/).waitFor();
    assert.equal(await page.locator("#report-subject").inputValue(), "Synthetic local scan report");
    assert.equal(await page.locator("#save-consent").isChecked(), false);
    assert.equal(await page.locator("#save-report").isDisabled(), true);
    assert.equal(await page.locator("#save-consent").isDisabled(), true);
    assert.equal(records.size, savedCount, "Reopening a saved scan must not create a duplicate report");
    await page.locator("#show-reports").click();
    await page.locator("#load-history").click();
    await page.locator("#history-list").getByRole("button", { name: "View Synthetic local scan report" }).click();
    await page.locator("#detail-content").getByRole("button", { name: "Delete report" }).click();
    await page.locator("#confirm-delete").click();
    await page.getByText("Report deleted.").waitFor();
    assert.equal(records.has(localSavedId), false);
    evidence.tests.push("local scan saves once and keeps its title and save marker after popup reload");

    await page.locator("#show-check").click();
    await page.evaluate(() => {
      void chrome.runtime.sendMessage({ type: "__phishlens_test_slow_scan" });
    });
    await page.locator("#loading-state").waitFor({ state: "visible" });
    await page.locator("#clear-button").click();
    await page.locator("#empty-state").waitFor({ state: "visible" });
    await page.waitForTimeout(1500);
    await page.locator("#empty-state").waitFor({ state: "visible" });
    assert.equal(await page.locator("#result-state").isVisible(), false);
    evidence.tests.push("Clear during a local scan prevents a stale result from returning");

    await page.evaluate(() => { void chrome.runtime.sendMessage({ type: "__phishlens_test_slow_scan" }); });
    await page.locator("#loading-state").waitFor({ state: "visible" });
    await page.locator("#cancel-scan").click();
    await page.locator("#cancelled-state").waitFor({ state: "visible" });
    assert.equal(await page.locator("#selection-content").textContent(), "Synthetic delayed scan");
    await page.waitForTimeout(1500);
    assert.equal(await page.locator("#cancelled-state").isVisible(), true);
    await page.locator("#resume-scan").click();
    await page.locator("#result-state").waitFor({ state: "visible", timeout: 120000 });
    assert.equal(await page.locator("#selection-content").textContent(), "Synthetic delayed scan");

    await page.locator("#paste-panel > summary").click();
    const pastedText = "Synthetic pasted email:\n\n  Review\tthe meeting agenda.\n\nRegards,\n  Sender";
    await page.locator("#scan-body").fill(pastedText);
    await page.evaluate(() => chrome.storage.session.set({ phishlensDebugFailNext: true }));
    await page.locator("#scan-button").click();
    await page.locator("#error-state").waitFor({ state: "visible" });
    await page.locator("#retry-scan").click();
    await page.locator("#result-state").waitFor({ state: "visible", timeout: 120000 });
    assert.equal(await page.locator("#selection-content").textContent(), pastedText);
    evidence.tests.push("Cancel retains the selection and retry recovers from a controlled local failure");

    await page.locator("#show-reports").click();
    await page.locator("#server-create > summary").click();
    await page.locator("#create-subject").fill("Synthetic browser CRUD");
    await page.locator("#create-body").fill("Synthetic browser acceptance. No personal data or credentials.");
    await page.locator("#create-button").click();
    await page.locator("#detail-panel").waitFor({ state: "visible" });
    assert.equal(await page.locator("#detail-content").getByText("Synthetic browser CRUD").count(), 1);
    assert.equal(await page.evaluate(() => document.activeElement?.id), "detail-heading");
    await page.locator("#detail-panel").evaluate(element => element.scrollIntoView({ block: "start" }));
    assert.ok(createdRecordId && records.has(createdRecordId), "Synthetic create must reach the local API");
    evidence.tests.push("synthetic saved analysis can be created and viewed");

    await page.locator("#back-to-reports").click();
    await page.locator('#report-search').fill('No matching report');
    await page.locator('#no-report-matches').waitFor({ state: 'visible' });
    assert.equal(await page.locator('#report-search').isVisible(), true);
    await page.locator('#reset-report-search').click();
    assert.equal(await page.locator('#history-list > li').count(), records.size);
    await page.locator('#report-search').fill('  CRUD   Synthetic  ');
    assert.equal(await page.locator('#history-list > li').count(), 1);
    await page.locator('#report-search').evaluate(element => element.scrollIntoView({ block: 'center' }));
    await page.screenshot({ path: path.join(root, 'output', 'extension', 'ui-search-results.png') });
    await page.locator('#clear-report-search').click();
    assert.equal(await page.locator('#report-search').inputValue(), '');
    assert.equal(await page.locator('#history-list > li').count(), records.size);
    await page.locator("#report-search").fill("Synthetic browser CRUD");
    await page.locator("#history-list").getByRole("button", { name: "View Synthetic browser CRUD" }).click();
    await page.locator("#detail-heading").waitFor({ state: "visible" });
    assert.equal(await page.evaluate(() => document.activeElement?.id), "detail-heading");
    await page.locator("#detail-panel").evaluate(element => element.scrollIntoView({ block: "start" }));
    await page.screenshot({ path: path.join(root, "output", "extension", "ui-detail.png") });

    await page.locator("#detail-content").getByRole("button", { name: "Edit notes" }).click();
    assert.equal(await page.evaluate(() => document.activeElement?.id), "edit-notes");
    await page.locator("#edit-notes").fill("Synthetic browser note");
    await page.locator("#edit-correction > summary").click();
    assert.deepEqual(await page.locator('#edit-feedback option').allTextContents(), [
      'No feedback to add', 'Flagged, but I think it’s legitimate', 'Not flagged, but I think it’s suspicious'
    ]);
    await page.locator("#edit-feedback").selectOption("false_positive");
    await page.locator('#edit-form').evaluate(element => element.scrollIntoView({ block: 'start' }));
    await page.screenshot({ path: path.join(root, 'output', 'extension', 'ui-edit-notes.png') });
    await page.locator("#save-edit").click();
    await page.getByText("Changes saved successfully.").waitFor();
    assert.equal(records.get(createdRecordId).notes, "Synthetic browser note");
    assert.equal(records.get(createdRecordId).feedback, "false_positive");

    await page.locator("#detail-content").getByRole("button", { name: "Delete report" }).click();
    assert.equal(await page.evaluate(() => document.activeElement?.id), "delete-heading");
    await page.locator("#cancel-delete").click();
    assert.equal(await page.evaluate(() => document.activeElement?.textContent), "Delete report");
    await page.locator("#detail-content").getByRole("button", { name: "Delete report" }).click();
    await page.locator("#confirm-delete").click();
    await page.getByText("Report deleted.").waitFor();
    assert.equal(records.has(createdRecordId), false, "Synthetic delete must remove the local API record");
    await page.locator("#report-search").fill('');
    evidence.tests.push("synthetic saved analysis can be edited and deleted");

    await setState(apiOrigin, { historyMode: "empty" });
    await page.locator("#load-history").click();
    await page.locator("#empty").waitFor({ state: "visible" });
    assert.equal(await page.locator('#report-search').isVisible(), true);
    await page.evaluate(() => scrollTo(0, 0));
    await page.screenshot({ path: path.join(root, "output", "extension", "ui-history.png") });

    await setState(apiOrigin, { historyMode: "error" });
    await page.locator("#load-history").click();
    await page.locator("#crud-status").getByText(/Saved reports are temporarily unavailable/).waitFor();
    evidence.tests.push("empty history and history API failure states render clearly");

    evidence.browser_version = context.browser()?.version() ?? "unknown";
    evidence.result = "passed";
  } finally {
    if (context) await context.close();
    await new Promise(resolve => server.close(resolve));
    await rm(tempRoot, {
      recursive: true,
      force: true,
      maxRetries: 8,
      retryDelay: 250,
    });
  }
  await writeEvidence();
}

run().catch(async error => {
  console.error(error);
  evidence.result = "failed";
  evidence.error = { name: error?.name ?? "Error", message: error?.message ?? String(error) };
  await writeEvidence();
  process.exitCode = 1;
});

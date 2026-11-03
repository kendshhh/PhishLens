import { API_BASE_URL } from './config.js';
import { createAnalysisClient } from './api.js';
import { saveLocalReport } from './report-workflow.js';
import { MODEL_SHA256 } from '../ai/local-analyzer.mjs';


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

function node(doc, tag, className, text) {
  const element = doc.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function show(element, visible) {
  element.classList.toggle("hidden", !visible);
}

export function createPopupController(client, doc = document, { onBusyChange = () => {}, onDeleted = async () => {} } = {}) {
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
    onBusyChange(value);
    if (value) { ++detailRequest; ++listRequest; show(ui.loading, false); }
    ui.subject.disabled = value;
    ui.body.disabled = value;
    ui.notes.disabled = value;
    ui.feedback.disabled = value;
    for (const button of [ui.createButton, ui.saveEdit, ui.cancelEdit, ui.deleteButton, ui.cancelDelete]) {
      button.disabled = value;
    }
    ui.createButton.textContent = value ? "Saving…" : "Save analysis";
    ui.saveEdit.textContent = value ? "Saving…" : "Save changes";
    ui.deleteButton.textContent = value ? "Deleting…" : "Delete analysis";
  }

  function predictionLabel(record) {
    if (record.review_status === "uncertain" || record.analysis_provenance?.local_review?.status === "uncertain") {
      return "Uncertain — local review not confirmed";
    }
    if (record.prediction === "legitimate") return "below threshold / historical legitimate label";
    return classificationLabels.get(record.prediction) ||
      (record.prediction == null ? "Not analyzed yet" : "Classification unavailable");
  }

  function renderDetail(record) {
    ui.detailContent.replaceChildren();
    const analyzed = classificationLabels.has(record.prediction);
    const provenance = record.analysis_provenance && typeof record.analysis_provenance === "object"
      ? record.analysis_provenance : {};
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
      ["Classification", predictionLabel(record)],
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
    if (provenance) {
      if (provenance.assessment) values.push(["Assessment", provenance.assessment]);
      if (provenance.local_review) values.push(["Local review", provenance.local_review.status],
        ["Audit source", "Browser-reported LLM; classifier checks replayed by server."]);
      if (provenance.model_revision === MODEL_SHA256 && Number.isFinite(provenance.phishing_score)) {
        values.push(["Research model score", (100 * provenance.phishing_score).toFixed(2) + "%"],
          ["Alert threshold", (100 * provenance.alert_threshold_score).toFixed(2) + "%"]);
      }
    }
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
      const meta = node(doc, "p", "muted", `${predictionLabel(record)} · ${record.risk_level || "Risk unknown"}`);
      const open = node(doc, "button", "link-button", "View details");
      open.type = "button";
      open.setAttribute("aria-label", `View ${record.subject || "untitled analysis"}`);
      open.addEventListener("click", () => loadDetail(record.id));
      item.append(title, meta, open);
      ui.list.append(item);
    }
  }

  function invalidatePendingDetail() {
    ++detailRequest;
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
      setStatus(error instanceof SyntaxError || /Invalid/.test(error.message)
        ? "The server returned malformed analysis details."
        : `Unable to load details: ${error.message}`, "error");
    }
  }

  function openEdit() {
    if (busy || !selected) return;
    ui.notes.value = selected.notes || "";
    ui.feedback.value = selected.feedback === null ? "null" : selected.feedback;
    show(ui.editForm, true);
    ui.notes.focus();
  }
  function openDelete() {
    if (busy || !selected) return;
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
      await onDeleted(deletedId);
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

  function acceptSavedReport(outcome) {
    invalidatePendingDetail();
    ++listRequest;
    show(ui.loading, false);
    records = outcome.history || [outcome.saved, ...records.filter(record => record.id !== outcome.saved.id)];
    renderList();
    selected = outcome.detail || outcome.saved;
    renderDetail(selected);
    show(ui.editForm, false);
    show(ui.deleteConfirm, false);
  }

  return { refresh, loadDetail, acceptSavedReport,
    beginSave() { if (busy) return false; invalidatePendingDetail(); setBusy(true); return true; },
    endSave() { setBusy(false); }, get records() { return records; } };

}


export function initializePopup({ documentImpl = document, chromeImpl = globalThis.chrome,
    fetchImpl = fetch } = {}) {
    const $ = id => documentImpl.getElementById(id);
    const client = createAnalysisClient(API_BASE_URL, fetchImpl, { requiredModel: MODEL_SHA256 });
    let state, stateGeneration = 0;
    const controller = createPopupController(client, documentImpl, {
        onBusyChange(value) { $('save-report').disabled = value; },
        async onDeleted(id) {
            try {
                const stored = await chromeImpl.storage.session.get('phishlensReportAttempt');
                if (stored.phishlensReportAttempt?.savedId === id) {
                    await chromeImpl.storage.session.remove('phishlensReportAttempt');
                    text('save-status', 'The saved report was deleted. You may explicitly save it again.');
                }
            } catch {
                text('save-status', 'The report was deleted, but its local save marker could not be cleared.');
            }
        }
    });
    const show = (id, visible) => $(id).classList.toggle('hidden', !visible);
    const text = (id, value) => { $(id).textContent = value; };
    const message = error => error instanceof Error ? error.message : 'The operation failed. Please retry.';
    function rows(id, values) {
        $(id).replaceChildren();
        for (const value of values) {
            const li = documentImpl.createElement('li');
            li.textContent = value;
            $(id).appendChild(li);
        }
    }
    function render(current) {
        const changed = state?.scanId !== current?.scanId || state?.status !== current?.status;
        state = current;
        for (const name of ['empty', 'loading', 'error', 'result']) show(name + '-state', false);
        if (changed) { text('save-status', ''); $('save-consent').checked = false; }
        if (!current) { show('empty-state', true); return; }
        if (current.status === 'loading') {
            text('workflow-progress', (current.stage || 'Preparing local review') +
                (Number.isFinite(current.progress) ? ' — ' + Math.round(current.progress * 100) + '%' : ''));
            show('loading-state', true); return;
        }
        const r = current.result;
        if (current.status !== 'success' || !r?.valid || r.model_sha256 !== MODEL_SHA256 ||
            !Number.isFinite(r.score) || !r.verification?.quote_spans_valid) {
            text('error-message', current.error || 'Invalid local scan. Reload the extension and scan again.');
            show('error-state', true); return;
        }
        text('classification', r.workflow?.released ? (r.alert ? 'Suspicious — review before acting' : 'Below alert threshold') : 'Uncertain — full review not confirmed');
        text('assessment', r.assessment);
        text('risk-score', (100 * r.score).toFixed(2) + '%');
        text('threshold', 'Frozen alert threshold: ' + (100 * r.alert_threshold_score).toFixed(2) +
            '%. A score above 50% alone does not trigger an alert.');
        text('coverage', r.input_truncated ? 'Long text: first 2,000 and last 300 normalized characters checked.' :
            'The complete normalized selection was checked. Highlight-only behavior has not had a separate held-out evaluation.');
        rows('evidence', r.evidence.length ? r.evidence.map(e =>
            '“' + e.quote + '” — ' + e.observation + ' ' + e.why + ' Next: ' + e.action) :
            ['No specific wording observation was established. This is not proof that the email is genuine.']);
        rows('drivers', r.model_drivers.map(e => '“' + e.quote + '” shifts the model ' +
            (e.direction === 'toward_phishing' ? 'toward phishing' : 'away from phishing') +
            ' (raw margin contribution ' + e.contribution.toFixed(4) + '). This is a statistical association.'));
        rows('recommendations', r.actions); rows('limitations', r.limitations);
        const audit = r.workflow?.judge;
        const failureTips = {
            model_assets_missing: 'Local LLM weights are missing. Run the model setup command or install the full model bundle.',
            webgpu_unavailable: 'WebGPU is unavailable on this browser/device.',
            webgpu_fp16_unavailable: 'This device does not provide the GPU feature needed by the local LLM.',
            model_integrity_failed: 'Local model integrity failed. Reinstall verified model assets.',
            judge_timeout: 'The local LLM exceeded its safety timeout. Retry after other GPU work finishes.',
            judge_input_too_long_without_truncation: 'The complete selection exceeds the judge token budget. No hidden extra truncation was applied.'
        };
        text('judge-review', audit?.valid ? '“' + audit.quote + '” — ' + audit.reason :
            (failureTips[audit?.code] || 'The local LLM review was unavailable or unusable. No reviewed verdict was released.'));
        text('workflow-status', r.workflow?.released ? 'All three classifiers agree and the local judge supports the finding.' :
            (r.workflow?.reasons || ['No completed full-workflow review is available.']).join(' '));
        rows('reevaluator-list', (r.workflow?.reevaluators || []).map(e =>
            e.kind.toUpperCase() + ': ' + (e.alert ? 'suspicious' : 'below its threshold') +
            ' — model score ' + (100 * e.score).toFixed(2) + '%; alert threshold ' +
            (100 * e.threshold_score).toFixed(2) + '%'));
        $('analysis-text').replaceChildren();
        let offset = 0;
        for (const e of [...r.evidence].sort((a, b) => a.start - b.start)) {
            if (e.start < offset || r.analysis_text.slice(e.start, e.end) !== e.quote) continue;
            $('analysis-text').append(documentImpl.createTextNode(r.analysis_text.slice(offset, e.start)));
            const mark = documentImpl.createElement('mark'); mark.textContent = e.quote;
            $('analysis-text').append(mark); offset = e.end;
        }
        $('analysis-text').append(documentImpl.createTextNode(r.analysis_text.slice(offset)));
        show('result-state', true);
    }
    $('load-history').addEventListener('click', controller.refresh);
    $('clear-button').addEventListener('click', async () => {
        const response = await chromeImpl.runtime.sendMessage({ type: 'phishlens-clear-analysis' }).catch(() => null);
        if (!response?.ok) { text('error-message', 'Local scan could not be cleared. Reload the extension.'); show('error-state', true); }
    });
    $('save-report').addEventListener('click', async () => {
        const snapshot = state;
        if (snapshot?.status !== 'success' || !snapshot.result?.valid) return;
        if (!$('save-consent').checked) { text('save-status', 'Confirm the upload checkbox first.'); return; }
        const w = snapshot.result.workflow;
        if (!w) { text('save-status', 'Scan again to obtain the required full workflow.'); return; }
        const j = w.judge;
        const input = { subject: $('report-subject').value.trim(), body: snapshot.selectedText,
            local_review: { version: w.version, status: w.status, primary_alert: w.primary_alert,
                judge: j?.valid ? { valid: true, audit: j.audit, quote: j.quote, reason_code: j.reason_code,
                    missing_context: j.missing_context, model_id: j.model_id, model_revision: j.model_revision,
                    prompt_version: j.prompt_version, seed_passed_to_runtime: j.seed_passed_to_runtime === true } :
                    { valid: false, code: j?.code || 'judge_unavailable' },
                reevaluators: w.reevaluators.map(e => ({ kind: e.kind, model_id: e.model_id, sha256: e.sha256,
                    raw_margin: e.raw_margin, score: e.score, threshold_score: e.threshold_score,
                    cutoff: e.cutoff, alert: e.alert, valid: e.valid })) } };
        if (!controller.beginSave()) return;
        try {
            const stored = await chromeImpl.storage.session.get('phishlensReportAttempt');
            let attempt = stored.phishlensReportAttempt;
            if (attempt?.scanId !== snapshot.scanId || attempt?.subject !== input.subject) {
                attempt = { scanId: snapshot.scanId, subject: input.subject, key: globalThis.crypto.randomUUID() };
                await chromeImpl.storage.session.set({ phishlensReportAttempt: attempt });
            }
            if (attempt.savedId) {
                text('save-status', 'This report was already saved. Refresh history to open it.'); return;
            }
            text('save-status', 'Checking the matching save service…');
            const outcome = await saveLocalReport({
                client, baseUrl: API_BASE_URL, modelSha: MODEL_SHA256, input,
                idempotencyKey: attempt.key, fetchImpl
            });
            await chromeImpl.storage.session.set({ phishlensReportAttempt: { ...attempt, savedId: outcome.saved.id } });
            if (state?.scanId === snapshot.scanId) {
                text('save-status', outcome.refreshErrors.length ? 'Saved. Some refreshes failed; use Load / refresh history.' :
                    'Saved and reread successfully.');
            }
            controller.acceptSavedReport(outcome);
        } catch (error) {
            if (state?.scanId === snapshot.scanId) text('save-status', message(error) +
                ' No automatic retry was made. Retry uses the same request key, including after reopening this popup.');
        } finally { controller.endSave(); }
    });
    chromeImpl.storage.onChanged.addListener((changes, area) => {
        if (area === 'session' && changes.veriqoAnalysis) {
            ++stateGeneration; render(changes.veriqoAnalysis.newValue);
        }
    });
    chromeImpl.storage.session.get('veriqoAnalysis').then(data => {
        if (stateGeneration === 0) render(data.veriqoAnalysis);
    }).catch(() => {
        if (stateGeneration === 0) render({ status: 'error', error: 'Local state could not be read. Reload the extension.' });
    });
    return { loadHistory: controller.refresh, render, openDetail: controller.loadDetail };
}

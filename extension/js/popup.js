import { API_BASE_URL } from './config.js';
import { createAnalysisClient } from './api.js';
import { saveLocalReport } from './report-workflow.js';
import { MODEL_SHA256 } from '../ai/local-analyzer.mjs';


const feedbackLabels = new Map([
  [null, "No feedback provided"], ["none", "No feedback provided"],
  ["false_positive", "Flagged, but I think it’s legitimate"],
  ["false_negative", "Not flagged, but I think it’s suspicious"]
]);
const provenanceLabels = new Map([
  ["mock", "Mock / demo result — not a real assessment"], ["real", "Automated analysis recorded when saved"],
  ["unknown", "Analysis source unknown"]
]);
const classificationLabels = new Map([
  ["phishing", "Phishing"], ["legitimate", "Legitimate"], ["spam", "Spam"]
]);
const providerLabels = new Map([
  ["mock", "Mock provider"], ["gemini", "Gemini"], ["local", "Local model"], ["tfidf", "TF-IDF"]
]);

function screeningLabel(prediction) {
    if (prediction === 'legitimate') return 'No strong warning signs';
    if (prediction === 'uncertain') return 'Uncertain — check before acting';
    return classificationLabels.get(prediction) ||
        (prediction == null ? 'Not analyzed yet' : 'Classification unavailable');
}

function screeningTone(prediction) {
    if (prediction === 'phishing') return 'suspicious';
    if (prediction === 'uncertain' || prediction === 'spam') return 'uncertain';
    return prediction === 'legitimate' ? 'below' : 'neutral';
}

function initialScreeningSummary(prediction) {
    if (prediction === 'legitimate') return 'Initial screening found no strong warning signs.';
    if (prediction === 'phishing') return 'Initial screening flagged this email as phishing.';
    return '';
}

function hasUncertainReview(record) {
    return record.review_status === 'uncertain' || record.analysis_provenance?.local_review?.status === 'uncertain';
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

export function createPopupController(client, doc = document, { onBusyChange = () => {}, onDeleted = async () => {},
    onDetailShown = () => {} } = {}) {
  const $ = id => doc.getElementById(id);
  const ui = {
    status: $("crud-status"), list: $("history-list"), empty: $("empty"),
    loading: $("loading"), detail: $("detail-panel"), detailHeading: $("detail-heading"),
    detailContent: $("detail-content"), deleteHeading: $("delete-heading"),
    editForm: $("edit-form"), notes: $("edit-notes"), feedback: $("edit-feedback"),
    deleteConfirm: $("delete-confirm"), deleteSubject: $("delete-subject"),
    deleteButton: $("confirm-delete"), cancelDelete: $("cancel-delete"),
    cancelEdit: $("cancel-edit"), saveEdit: $("save-edit"),
    listView: $("reports-list-view"), search: $("report-search"), count: $("report-count"),
    noMatches: $("no-report-matches"), back: $("back-to-reports"), historyHeading: $("history-heading"),
    modeWarning: $("report-mode-warning"), correction: $("edit-correction"),
    clearSearch: $("clear-report-search"), resetSearch: $("reset-report-search")
  };
  let records = [];
  let accountVersion = 0;
  let selected = null;
  let busy = false;
  let detailRequest = 0;
  let listRequest = 0;
  let editTrigger;
  let deleteTrigger;

  function setStatus(message, kind = "info") {
    ui.status.textContent = message;
    ui.status.className = `status ${kind}`;
    show(ui.status, Boolean(message));
  }

  function setBusy(value) {
    busy = value;
    if (value) { ++detailRequest; ++listRequest; show(ui.loading, false); ui.list.setAttribute('aria-busy', 'false'); }
    ui.notes.disabled = value;
    ui.feedback.disabled = value;
    for (const button of [ui.saveEdit, ui.cancelEdit, ui.deleteButton, ui.cancelDelete, ui.back]) {
      button.disabled = value;
    }
    ui.saveEdit.textContent = value ? "Saving…" : "Save changes";
    ui.deleteButton.textContent = value ? "Deleting…" : "Delete report";
    onBusyChange(value);
  }

  function revealDetail() {
    show(ui.listView, false);
    show(ui.detail, true);
    onDetailShown();
  }

  function renderDetail(record, { reveal = true } = {}) {
    ui.detailContent.replaceChildren();
    ui.detailHeading.textContent = record.subject || 'Untitled report';
    const analyzed = classificationLabels.has(record.prediction);
    const uncertain = hasUncertainReview(record);
    const prediction = uncertain ? 'uncertain' : record.prediction;
    const provenance = record.analysis_provenance && typeof record.analysis_provenance === "object"
      ? record.analysis_provenance : {};
    const provenanceLines = [provenanceLabels.get(record.analysis_mode) || "Analysis source unknown"];
    if (record.analysis_mode === "real") {
      const hasProvider = typeof provenance.provider_mode === "string" && Boolean(provenance.provider_mode.trim());
      const hasModel = typeof provenance.model === "string" && Boolean(provenance.model.trim());
      if (hasProvider) {
        provenanceLines.push(`Provider: ${providerLabels.get(provenance.provider_mode) || `Unrecognized (${provenance.provider_mode})`}`);
      }
      if (hasModel) provenanceLines.push(`Model: ${provenance.model}`);
      if (typeof provenance.model_revision === "string" && provenance.model_revision.trim()) {
        provenanceLines.push(`Model revision: ${provenance.model_revision}`);
      }
      if (typeof provenance.prompt_version === "string" && provenance.prompt_version.trim()) {
        provenanceLines.push(`Prompt version: ${provenance.prompt_version}`);
      }
      if (typeof provenance.explanation_source === "string" && provenance.explanation_source.trim()) {
        provenanceLines.push(`Explanation source: ${provenance.explanation_source}`);
      }
      if (provenance.local_review) provenanceLines.push('The local review was reported by the browser.');
      if (record.analysis_mode === "real" && !hasProvider) {
        provenanceLines.push(hasModel ? "Provider was not reported." : "Provider and model were not reported.");
      }
  
    }
    ui.modeWarning.textContent = record.analysis_mode === 'mock' ? 'Demo result — this is not a real email assessment.' :
      record.analysis_mode !== 'real' ? 'The analysis source was not recorded. Treat this report as unverified.' : '';
    show(ui.modeWarning, Boolean(ui.modeWarning.textContent));
    const values = [
      ["Report title", record.subject || "Untitled report"], ["Email text", record.body],
      ["Summary", record.explanation || (analyzed
        ? "No explanation was returned. Review the available indicators and verify independently."
        : "Unavailable because this report has not been analyzed.")],
      ["Assessment", screeningLabel(prediction)],
      ["Reported risk", record.risk_level || (analyzed ? "Not provided" : "Not assessed (analysis not completed)")],
      ["Reported score", record.confidence == null
        ? "Not provided; no confidence estimate is available."
        : `${Math.round(record.confidence * 100)}% (model-reported score, not a guarantee)`],
      ["Wording observations", !analyzed
        ? "Unavailable because this report has not been analyzed."
        : record.threat_indicators.length
        ? record.threat_indicators.map(indicator => `${indicator.type}: ${indicator.detail}${indicator.quote ? ` (“${indicator.quote}”)` : ""}`).join("\n")
        : "No validated indicators were returned."],
      ["Your notes", record.notes || "No notes yet. Add a note to keep track of what you checked."], ["Your opinion", feedbackLabels.get(record.feedback) || "Feedback unavailable"],
      ["About this result", provenanceLines.join("\n")]
    ];
    for (const [label, value] of values) {
      const collapsed = ['Email text', 'Reported risk', 'Reported score', 'Wording observations', 'About this result'].includes(label);
      const tone = screeningTone(prediction);
      const section = node(doc, collapsed ? "details" : "div", `detail-field${label === 'Assessment' ? ` report-assessment ${tone}` : ''}${label === 'Your notes' ? ' notes-field' : ''}`);
      section.append(node(doc, collapsed ? "summary" : "h4", "", label),
        node(doc, "p", label === 'Email text' ? 'report-email-content' : '', value));
      if (label === 'Report title') section.append(node(doc, 'p', 'saved-date', 'Saved ' + new Date(record.created_at).toLocaleString(undefined,
        { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' })));
      if (label === 'Assessment') section.append(node(doc, 'p', 'field-help', uncertain
        ? initialScreeningSummary(record.prediction) || 'The local review did not confirm a finding.'
        : 'Text screening is advisory. Verify unexpected requests independently.'));
      ui.detailContent.append(section);
    }
    const edit = node(doc, "button", "secondary", "Edit notes");
    edit.type = "button";
    edit.addEventListener("click", openEdit);
    const remove = node(doc, "button", "danger", "Delete report");
    remove.type = "button";
    remove.addEventListener("click", openDelete);
    editTrigger = edit;
    deleteTrigger = remove;
    ui.detailContent.append(edit, remove);
    ui.notes.value = record.notes || "";
    ui.feedback.value = record.feedback || "none";
    if (reveal) revealDetail();
    else { show(ui.detail, false); show(ui.listView, true); }
  }

  function renderList() {
    ui.list.replaceChildren();
    show(ui.empty, records.length === 0);
    const normalizeSearch = value => value.normalize('NFKC').toLocaleLowerCase().replace(/\s+/g, ' ').trim();
    const query = normalizeSearch(ui.search.value);
    show(ui.clearSearch, ui.search.value.length > 0);
    const terms = query.split(' ').filter(Boolean);
    const visible = records.filter(record => {
      const text = normalizeSearch([record.subject || 'Untitled analysis', record.explanation || record.threat_indicators?.[0]?.detail || ''].join(' '));
      return terms.every(term => text.includes(term));
    });
    show(ui.noMatches, records.length > 0 && visible.length === 0);
    ui.count.textContent = query ? `${visible.length} of ${records.length} reports` :
      `${records.length} ${records.length === 1 ? 'report' : 'reports'} loaded`;
    show(ui.count, records.length > 0);
    for (const record of visible) {
      const item = node(doc, "li", "history-item");
      const title = node(doc, "strong", "", record.subject || "Untitled analysis");
      const meta = node(doc, "div", "history-meta");
      const uncertain = hasUncertainReview(record);
      const prediction = uncertain ? 'uncertain' : record.prediction;
      const tone = screeningTone(prediction);
      const assessment = node(doc, 'span', `assessment-badge ${tone}`, screeningLabel(prediction));
      const date = node(doc, 'time', 'history-date', new Date(record.created_at).toLocaleDateString(undefined,
        { month: 'short', day: 'numeric', year: 'numeric' }));
      date.setAttribute('datetime', record.created_at);
      const preview = record.explanation?.trim() || record.threat_indicators?.[0]?.detail ||
        'Open this report to read the email and your notes.';
      meta.append(assessment, date, node(doc, 'p', 'history-preview', preview));
      if (uncertain && initialScreeningSummary(record.prediction)) {
        meta.append(node(doc, 'p', 'field-help', initialScreeningSummary(record.prediction)));
      }
      item.setAttribute('data-tone', tone);
      const open = node(doc, "button", "link-button report-open", "Open report →");
      open.type = "button";
      open.setAttribute("aria-label", `View ${record.subject || "untitled analysis"}`);
      open.addEventListener("click", () => loadDetail(record.id));
      item.append(title, meta, open);
      ui.list.append(item);
    }
  }

  ui.search.addEventListener('input', renderList);
  ui.search.addEventListener('search', renderList);
  function clearSearch() {
    ui.search.value = '';
    renderList();
    ui.search.focus();
  }
  ui.clearSearch.addEventListener('click', clearSearch);
  ui.resetSearch.addEventListener('click', clearSearch);
  ui.search.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !event.isComposing) { event.preventDefault(); clearSearch(); }
  });
  function showLibrary({ focus = true } = {}) {
    if (busy) return false;
    ++detailRequest;
    show(ui.detail, false); show(ui.editForm, false); show(ui.deleteConfirm, false);
    show(ui.listView, true);
    setStatus('');
    if (focus) ui.historyHeading.focus();
    return true;
  }
  ui.back.addEventListener('click', () => showLibrary());

  function invalidatePendingDetail() {
    ++detailRequest;
  }

  async function refresh() {
    const request = ++listRequest;
    show(ui.loading, true);
    ui.list.setAttribute('aria-busy', 'true');
    show(ui.empty, false);
    try {
      const latestRecords = await client.listAnalyses();
      if (request !== listRequest) return false;
      records = latestRecords;
      renderList();
      ui.list.setAttribute('aria-busy', 'false');
      show(ui.loading, false);
      setStatus('');
      return true;
    } catch (error) {
      if (request !== listRequest) return false;
      show(ui.loading, false);
      ui.list.setAttribute('aria-busy', 'false');
      if (records.length) renderList();
      else show(ui.empty, false);
      setStatus(error instanceof SyntaxError || /Invalid/.test(error.message)
        ? "The server returned malformed analysis data. Try again later."
        : error.status === 503 ? 'Saved reports are temporarily unavailable. Try refreshing later.'
        : `Saved analyses are unavailable: ${error.message}`, "error");
      return false;
    }
  }

  async function loadDetail(id, { announce = true, focus = announce, isCurrent = () => true } = {}) {
    if (busy) return;
    const request = ++detailRequest;
    selected = null;
    ui.detailContent.replaceChildren();
    show(ui.detail, false);
    show(ui.listView, true);
    show(ui.editForm, false);
    show(ui.deleteConfirm, false);
    if (announce) setStatus("Loading analysis details…", "info");
    try {
      const result = await client.getAnalysis(id);
      if (request !== detailRequest || !isCurrent()) return;
      selected = result;
      renderDetail(selected);
      show(ui.editForm, false);
      show(ui.deleteConfirm, false);
      if (focus) ui.detailHeading.focus();
      if (announce) setStatus('');
    } catch (error) {
      if (request !== detailRequest || !isCurrent()) return;
      setStatus(error instanceof SyntaxError || /Invalid/.test(error.message)
        ? "The server returned malformed analysis details."
        : `Unable to load details: ${error.message}`, "error");
    }
  }

  function openEdit() {
    if (busy || !selected) return;
    detailRequest++;
    ui.notes.value = selected.notes || "";
    ui.feedback.value = selected.feedback ?? 'none';
    ui.correction.open = ['false_positive', 'false_negative'].includes(selected.feedback);
    show(ui.editForm, true);
    ui.notes.focus();
  }
  function openDelete() {
    if (busy || !selected) return;
    ui.deleteSubject.textContent = selected.subject || "Untitled analysis";
    show(ui.deleteConfirm, true);
    ui.deleteHeading.focus();
  }

  async function saveServerReport(input, { isCurrent = () => true, onError = () => {} } = {}) {
    if (busy || !input.body) return false;
    invalidatePendingDetail();
    const operationVersion = accountVersion;
    setBusy(true);
    let created;
    try {
      created = await client.createAnalysis(input);
      if (operationVersion !== accountVersion) return false;
      records = [created, ...records.filter(record => record.id !== created.id)];
      renderList();
      const refreshed = await refresh();
      if (operationVersion !== accountVersion) return false;
      if (refreshed) setStatus("Analysis saved successfully.", "success");
    } catch (error) {
      if (operationVersion !== accountVersion) return false;
      const message = error instanceof SyntaxError || /Invalid/.test(error.message)
        ? "The server returned a malformed result. Your input is still here."
        : `Could not save analysis: ${error.message}. Your input is still here.`;
      setStatus(message, "error");
      if (isCurrent()) onError(message);
      return false;
    } finally {
      if (operationVersion === accountVersion) setBusy(false);
    }
    if (isCurrent()) await loadDetail(created.id, { announce: false, focus: true, isCurrent });
    return created;
  }

  ui.editForm.addEventListener("submit", async event => {
    event.preventDefault();
    if (busy || !selected) return;
    detailRequest++;
    const operationVersion = accountVersion;
    setBusy(true);
    try {
      const updated = await client.updateAnalysis(selected.id, {
        notes: ui.notes.value.trim() || null,
        feedback: ui.feedback.value === 'none' && selected.feedback === null ? null : ui.feedback.value
      });
      if (operationVersion !== accountVersion) return;
      selected = updated;
      show(ui.editForm, false);
      records = records.map(record => record.id === selected.id ? selected : record);
      renderList();
      renderDetail(selected);
      editTrigger.focus();
      const refreshed = await refresh();
      if (operationVersion !== accountVersion) return;
      if (refreshed) setStatus("Changes saved successfully.", "success");
    } catch (error) {
      if (operationVersion !== accountVersion) return;
      setStatus(error instanceof SyntaxError || /Invalid/.test(error.message)
        ? "The server returned a malformed result. Your edits are still here."
        : `Could not save changes: ${error.message}. Your edits are still here.`, "error");
    } finally { if (operationVersion === accountVersion) setBusy(false); }
  });
  ui.cancelEdit.addEventListener("click", () => {
    show(ui.editForm, false);
    if (selected) { renderDetail(selected); editTrigger.focus(); }
  });
  ui.cancelDelete.addEventListener("click", () => {
    show(ui.deleteConfirm, false);
    deleteTrigger?.focus();
  });
  ui.deleteConfirm.addEventListener("submit", async event => {
    event.preventDefault();
    if (busy || !selected) return;
    detailRequest++;
    const operationVersion = accountVersion;
    setBusy(true);
    try {
      const deletedId = selected.id;
      await client.deleteAnalysis(deletedId);
      if (operationVersion !== accountVersion) return;
      await onDeleted(deletedId);
      if (operationVersion !== accountVersion) return;
      records = records.filter(record => record.id !== deletedId);
      renderList();
      selected = null;
      show(ui.detail, false);
      show(ui.listView, true);
      show(ui.deleteConfirm, false);
      show(ui.editForm, false);
      const refreshed = await refresh();
      if (operationVersion !== accountVersion) return;
      if (refreshed) setStatus("Report deleted.", "success");
      ui.historyHeading.focus();
    } catch (error) {
      if (operationVersion !== accountVersion) return;
      setStatus(`Could not delete analysis: ${error.message}`, "error");
    } finally { if (operationVersion === accountVersion) setBusy(false); }
  });

  function acceptSavedReport(outcome, { reveal = true } = {}) {
    invalidatePendingDetail();
    ++listRequest;
    show(ui.loading, false);
    records = outcome.history || [outcome.saved, ...records.filter(record => record.id !== outcome.saved.id)];
    renderList();
    selected = outcome.detail || outcome.saved;
    renderDetail(selected, { reveal });
    if (reveal) ui.detailHeading.focus();
    show(ui.editForm, false);
    show(ui.deleteConfirm, false);
  }

  function reset() {
    ++accountVersion; ++detailRequest; ++listRequest;
    records = []; selected = null;
    ui.list.replaceChildren(); ui.detailContent.replaceChildren();
    ui.detailHeading.textContent = 'Report details'; ui.deleteSubject.textContent = '';
    ui.count.textContent = ''; ui.modeWarning.textContent = ''; ui.correction.open = false;
    for (const input of [ui.notes, ui.search]) input.value = '';
    ui.feedback.value = 'none';
    for (const panel of [ui.detail, ui.editForm, ui.deleteConfirm, ui.loading, ui.empty, ui.noMatches, ui.count]) show(panel, false);
    show(ui.listView, true);
    setStatus(''); setBusy(false);
  }
  return { refresh, loadDetail, acceptSavedReport, showLibrary, reset, saveServerReport,
    openSavedReport(id) {
      if (selected?.id === id) { revealDetail(); ui.detailHeading.focus(); return; }
      return loadDetail(id);
    },
    beginSave() { if (busy) return false; invalidatePendingDetail(); setBusy(true); return true; },
    endSave() { setBusy(false); }, get records() { return records; } };

}


export function initializePopup({ documentImpl = document, chromeImpl = globalThis.chrome,
    fetchImpl = fetch, clientImpl = null, canAccessReports = () => true, reportAccessReady = Promise.resolve(),
    locationImpl = globalThis.location, preview = false, apiOrigin = API_BASE_URL } = {}) {
    // Preserve fixed sizing for legacy popup URLs.
    if (new globalThis.URLSearchParams(locationImpl?.search ?? '').get('surface') === 'popup') {
        documentImpl.documentElement?.classList.add('popup-surface');
    }
    const $ = id => documentImpl.getElementById(id);
    const client = clientImpl || createAnalysisClient(apiOrigin, fetchImpl, { requiredModel: MODEL_SHA256 });
    let state, stateGeneration = 0, accountEpoch = 0;
    let savedReport = null;
    let reportBusy = false;
    let reportSaveState = 'unsaved';
    let serverRequest;
    const controller = createPopupController(client, documentImpl, {
        onDetailShown() { selectView('reports'); },
        onBusyChange(value) {
            reportBusy = value;
            updateSaveControls();
            updateScanControls();
        },
        async onDeleted(id) {
            if (savedReport?.id === id) {
                savedReport = null;
                reportSaveState = 'unsaved';
                show('view-saved-report', false);
                updateSaveControls();
            }
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
    show('reports-preview-notice', preview);
    function updateSaveControls() {
        const signedIn = canAccessReports();
        const alreadySaved = Boolean(state?.scanId && savedReport?.scanId === state.scanId);
        $('save-report').disabled = reportBusy || alreadySaved || !signedIn;
        $('report-subject').disabled = reportBusy || alreadySaved || !signedIn;
        $('save-consent').disabled = reportBusy || alreadySaved || !signedIn;
        $('view-saved-report').disabled = reportBusy;
        show('save-options', signedIn && !alreadySaved);
        show('save-sign-in', !signedIn);
        show('local-save-consent', state?.source !== 'server');
        text('report-save-state', alreadySaved ? 'Saved to your account.'
            : reportSaveState === 'unknown' ? 'Save not confirmed. Check Saved reports before trying again.'
                : reportBusy ? 'Saving your report…' : 'This result has not been saved.');
    }

    function abortServerRequest() {
        serverRequest?.abort();
        serverRequest = undefined;
    }

    function hasUsableResult(check) {
        const result = check?.result;
        return check?.status === 'success' && (check.source === 'server' ||
            (result?.valid && result.model_sha256 === MODEL_SHA256 && Number.isFinite(result.score) &&
                result.verification?.quote_spans_valid));
    }

    function canUseServerFallback(check) {
        const body = check?.selectedText?.trim();
        return (check?.status === 'error' || check?.status === 'success') && !hasUsableResult(check) &&
            Boolean(body) && body.length <= 30000;
    }

    async function startServerScan() {
        if (serverRequest || reportBusy || submittingScan || !canUseServerFallback(state)) return;
        const body = state.selectedText.trim();
        const subject = state.subject;
        const request = new globalThis.AbortController();
        serverRequest = request;
        ++stateGeneration;
        const check = { source: 'server', selectedText: body, subject };
        render({ ...check, status: 'loading' });
        try {
            // Retire the failed device check so it cannot reappear on reopening the panel.
            const cleared = await chromeImpl.runtime.sendMessage({ type: 'phishlens-clear-analysis' });
            if (serverRequest !== request) return;
            if (!cleared?.ok) throw new Error('Could not retire the previous check');
            const response = await fetchImpl(apiOrigin.replace(/\/+$/, '') + '/analyses', {
                method: 'POST', redirect: 'error',
                headers: { 'Content-Type': 'application/json', 'X-Require-Provider': 'tfidf' },
                body: JSON.stringify({ text: body }),
                signal: AbortSignal.any([request.signal, AbortSignal.timeout(15000)]),
            });
            if (!response.ok) throw new Error('Server check failed');
            const result = await response.json();
            if (result.mode !== 'tfidf' || result.model_revision !== MODEL_SHA256 ||
                typeof result.model_alert !== 'boolean' ||
                result.classification !== (result.model_alert ? 'phishing' : 'legitimate')) {
                throw new Error('Incompatible screening result');
            }
            if (serverRequest === request) {
                render({ ...check, status: 'success', scanId: globalThis.crypto.randomUUID(), result });
            }
        } catch {
            if (serverRequest === request) {
                render({ ...check, status: 'error', error: 'Server screening is unavailable. Your text is still here.' });
            }
        } finally {
            if (serverRequest === request) serverRequest = undefined;
        }
    }

    $('view-saved-report').addEventListener('click', () => {
        if (savedReport) return controller.openSavedReport(savedReport.id);
    });
    function selectView(view) {
        show('check-view', view === 'check');
        show('reports-view', view === 'reports');
        $('show-check').setAttribute('aria-pressed', String(view === 'check'));
        $('show-reports').setAttribute('aria-pressed', String(view === 'reports'));
    }
    $('show-check').addEventListener('click', () => selectView('check'));
    $('show-reports').addEventListener('click', () => {
        selectView('reports');
        if (controller.showLibrary({ focus: false })) void controller.refresh();
    });
    $('start-new-check').addEventListener('click', () => { selectView('check'); $('show-check').focus(); });
    let scanDraftGeneration = 0;
    let draftWrites = Promise.resolve();
    let submittingScan = false;
    let scanSubmission = 0;
    function storeScanDraft() {
        const body = $('scan-body').value;
        draftWrites = draftWrites.catch(() => {}).then(() =>
            chromeImpl.storage.session.set({ phishlensScanDraft: body }));
        return draftWrites;
    }
    $('scan-body').addEventListener('input', () => {
        ++scanDraftGeneration;
        storeScanDraft().catch(() => text('scan-status', 'The draft could not be kept for reopening. Your text is still here.'));
    });
    chromeImpl.storage.session.get('phishlensScanDraft').then(data => {
        if (scanDraftGeneration === 0 && typeof data.phishlensScanDraft === 'string') {
            $('scan-body').value = data.phishlensScanDraft;
        }
    }).catch(() => text('scan-status', 'The previous draft could not be restored. You can paste text to start a new scan.'));

    function updateScanControls() {
        const busy = submittingScan || state?.status === 'loading' || reportBusy;
        for (const id of ['scan-button', 'retry-scan', 'resume-scan', 'scan-body', 'scan-subject']) {
            $(id).disabled = busy;
        }
        $('retry-scan').disabled = busy || !state?.selectedText;
        $('server-fallback-button').disabled = busy || !canUseServerFallback(state);
    }
    async function startLocalScan(body, { subject = '', keepDraft = false } = {}) {
        if (submittingScan || reportBusy || state?.status === 'loading') return;
        abortServerRequest();
        if (state?.source === 'server') render(undefined);
        const submission = ++scanSubmission;
        submittingScan = true;
        updateScanControls();
        text('scan-status', 'Starting the on-device check…');
        try {
            if (keepDraft) void storeScanDraft().catch(() => {});
            const response = await chromeImpl.runtime.sendMessage({ type: 'phishlens-analyze-text', text: body,
                ...(subject ? { subject } : {}) });
            if (submission !== scanSubmission) return;
            if (!response?.ok) throw new Error('Could not start check');
            text('scan-status', '');
        } catch {
            if (submission !== scanSubmission) return;
            render({ status: 'error', selectedText: body, subject, error: 'The on-device check could not start. Your text is retained.' });
            text('scan-status', 'The on-device check could not start. Your text is retained.');
        } finally {
            if (submission === scanSubmission) { submittingScan = false; updateScanControls(); }
        }
    }
    $('scan-form').addEventListener('submit', async event => {
        event.preventDefault();
        const body = $('scan-body').value;
        const subject = $('scan-subject').value.trim();
        if (!body.trim() || body.length > 30000) {
            text('scan-status', 'Enter an email body up to 30,000 characters.');
            $('scan-body').focus();
            return;
        }
        await startLocalScan(body, { subject, keepDraft: true });
    });
    $('server-fallback-button').addEventListener('click', startServerScan);
    for (const id of ['retry-scan', 'resume-scan']) $(id).addEventListener('click', () => {
        if (!state?.selectedText) return;
        return startLocalScan(state.selectedText, { subject: state.subject });
    });
    $('cancel-scan').addEventListener('click', async () => {
        if (state?.source === 'server') {
            abortServerRequest();
            render({ ...state, status: 'cancelled' });
            return;
        }
        $('cancel-scan').disabled = true;
        try {
            const response = await chromeImpl.runtime.sendMessage({ type: 'phishlens-cancel-analysis' });
            if (!response?.ok) throw new Error('Cancel failed');
            ++scanSubmission;
            submittingScan = false;
            updateScanControls();
        } catch {
            text('cancel-status', 'The check could not be cancelled. Try again or clear the check.');
        } finally { $('cancel-scan').disabled = false; }
    });
    function rows(id, values) {
        $(id).replaceChildren();
        for (const value of values) {
            const li = documentImpl.createElement('li');
            li.textContent = value;
            $(id).appendChild(li);
        }
    }
    function observationRows(id, observations) {
        $(id).replaceChildren();
        for (const observation of observations) {
            const item = node(documentImpl, 'li');
            item.append(node(documentImpl, 'p', '', observation.observation));
            const detail = node(documentImpl, 'details', 'observation-detail');
            detail.append(node(documentImpl, 'summary', '', 'See wording'),
                node(documentImpl, 'blockquote', '', observation.quote),
                node(documentImpl, 'p', '', observation.why));
            item.append(detail);
            $(id).appendChild(item);
        }
    }
    function render(current) {
        const previous = state;
        const changed = previous?.scanId !== current?.scanId || previous?.status !== current?.status ||
            previous?.source !== current?.source;
        state = current;
        const server = current?.source === 'server';
        const selectedText = typeof current?.selectedText === 'string' ? current.selectedText : '';
        show('clear-button', Boolean(current));
        show('server-fallback', canUseServerFallback(current));
        show('empty-state', !current);
        show('selection-preview', Boolean(selectedText));
        text('selection-content', selectedText);
        if (selectedText !== previous?.selectedText) {
            $('selection-content').scrollTop = 0;
            $('selection-preview').open = false;
        }
        for (const name of ['loading-state', 'cancelled-state', 'error-state', 'result-state', 'save-panel']) show(name, false);
        if (changed) {
            text('save-status', '');
            $('save-consent').checked = false;
            $('save-status').setAttribute('data-kind', 'info');
            $('save-status').setAttribute('role', 'status');
            reportSaveState = 'unsaved';
            if (savedReport?.scanId !== current?.scanId) { savedReport = null; show('view-saved-report', false); }
        }
        updateSaveControls();
        updateScanControls();
        if (!current) {
            $('scan-editor').open = true;
            text('scan-heading', 'Paste an email to check');
            if (previous && !$('check-view').classList.contains('hidden')) $('show-check').focus();
            return;
        }
        text('scan-heading', 'Check another email');
        if (current.status === 'loading') {
            selectView('check');
            if (changed) {
                $('scan-editor').open = false;
                $('analysis-details').open = false;
                $('save-panel').open = false;
                text('scan-status', '');
            }
            const stage = (current.stage || '').toLowerCase();
            const progress = server ? 'Waiting for PhishLens server screening…' :
                /load|download|initial|gpu/.test(stage) ? 'Preparing the on-device review…' :
                /retriev/.test(stage) ? 'Retrieving local review guidance…' :
                /judge|llm/.test(stage) ? 'Reviewing the email’s wording…' :
                /reeval|classifier|krr|lightgbm/.test(stage) ? 'Comparing the checks…' : 'Checking the email text…';
            text('loading-heading', server ? 'Checking on server…' : 'Checking on this device…');
            text('workflow-progress', progress + (Number.isFinite(current.progress)
                ? ' ' + Math.round(Math.max(0, Math.min(1, current.progress)) * 100) + '%' : ''));
            text('cancel-status', '');
            show('loading-state', true);
            return;
        }
        if (current.status === 'cancelled') { show('cancelled-state', true); return; }
        const result = current.result;
        if (!hasUsableResult(current)) {
            text('error-message', current.error || 'The check did not return a usable result. Try again.');
            show('error-state', true);
            return;
        }
        if (changed) {
            $('report-subject').value = current.subject || '';
            $('scan-editor').open = false;
        }
        const workflow = result.workflow;
        const localAlert = workflow?.primary_alert ?? result.alert;
        const screening = server ? result.classification :
            typeof localAlert === 'boolean' ? (localAlert ? 'phishing' : 'legitimate') :
                result.verdict === 'uncertain' ? 'uncertain' : null;
        const reviewUncertain = !server && workflow?.released !== true;
        const prediction = reviewUncertain ? 'uncertain' : screening;
        $('result-state').setAttribute('data-tone', screeningTone(prediction));
        text('analysis-source', server ? 'Server screening' : 'On-device review');
        text('classification', !server && prediction === 'phishing' ? 'Suspicious — review before acting' :
            prediction ? screeningLabel(prediction) : 'Screening unavailable');
        const incompleteReason = {
            model_assets_missing: 'The review model files could not be opened.',
            webgpu_unavailable: 'Chrome could not access the graphics support needed for the review.',
            webgpu_fp16_unavailable: 'Chrome’s graphics support could not run the review model.',
            judge_timeout: 'The review took too long to finish.',
            judge_input_too_long_without_truncation: 'This text is too long for the additional review.',
        }[workflow?.judge?.code];
        const initialScreening = initialScreeningSummary(screening);
        const reviewIncomplete = reviewUncertain && workflow?.judge?.valid !== true;
        const assessment = reviewIncomplete
            ? `Local review incomplete.${incompleteReason ? ' ' + incompleteReason : ''}`
            : reviewUncertain ? 'The local review couldn’t confirm the initial screening.'
                : prediction === 'phishing' ? 'Avoid links and requests in this email until you verify them.'
                    : prediction === 'legitimate'
                        ? 'The screening found few warning signs. Verify unexpected requests independently.'
                        : 'Verify the email independently before taking action.';
        text('assessment', assessment);
        $('review-state').setAttribute('data-kind', 'uncertain');
        text('review-state', reviewUncertain ? initialScreening || '' : '');
        show('review-state', reviewUncertain && Boolean(initialScreening));
        text('coverage', result.input_truncated ? 'Only part of this long email was checked.' : '');
        const evidence = server ? [] : result.evidence;
        show('observations', evidence.length > 0);
        observationRows('evidence', evidence.slice(0, 3));
        observationRows('additional-evidence', evidence.slice(3));
        show('more-observations', evidence.length > 3);
        const retrievedSources = server ? [] : (workflow?.judge?.retrieval?.sources || []);
        rows('guidance-sources', retrievedSources.map(source => `${source.title} (${source.id})`));
        show('guidance-context', retrievedSources.length > 0);
        const actions = server ? [] : result.actions;
        text('next-action', actions[0] || 'Verify unexpected requests through a website or contact method you already know.');
        rows('recommendations', actions.slice(1));
        rows('limitations', ['Screening assesses email text. The sender, hidden links, and attachments remain unverified.']);
        show('result-state', true);
        show('save-panel', Boolean(screening));
        if (previous?.status === 'loading') $('classification').focus();
    }
    $('load-history').addEventListener('click', controller.refresh);
    $('clear-button').addEventListener('click', async () => {
        if (state?.source === 'server') {
            abortServerRequest();
            render(undefined);
            return;
        }
        const response = await chromeImpl.runtime.sendMessage({ type: 'phishlens-clear-analysis' }).catch(() => null);
        if (!response?.ok) render({ ...state, status: 'error', error: 'The check could not be cleared. Try again.' });
    });
    $('save-report').addEventListener('click', async () => {
        const snapshot = state;
        const saveEpoch = accountEpoch;
        if (!canAccessReports()) { text('save-status', 'Sign in to save a personal report. Your local scan stays on this device.'); return; }
        if (snapshot?.status !== 'success' || savedReport?.scanId === snapshot.scanId) return;
        if (snapshot.source === 'server') {
            const input = { subject: $('report-subject').value.trim(), body: snapshot.selectedText };
            const saved = await controller.saveServerReport(input, {
                isCurrent: () => state === snapshot && accountEpoch === saveEpoch,
                onError(message) {
                    $('save-status').setAttribute('data-kind', 'error');
                    $('save-status').setAttribute('role', 'alert');
                    text('save-status', message);
                    $('save-status').focus();
                }
            });
            if (saved && state === snapshot && accountEpoch === saveEpoch) {
                if (!$('check-view').classList.contains('hidden')) {
                    savedReport = { scanId: snapshot.scanId, id: saved.id };
                    $('save-status').setAttribute('data-kind', 'success');
                    text('save-status', 'Report saved. Open it to retry loading the details.');
                    show('view-saved-report', true);
                    updateSaveControls();
                    $('view-saved-report').focus();
                    return;
                }
                render(undefined);
            }
            return;
        }
        if (!snapshot.result?.valid) return;
        if (!$('save-consent').checked) {
            $('save-status').setAttribute('data-kind', 'error');
            $('save-status').setAttribute('role', 'alert');
            text('save-status', 'Report not saved. To save it, check the consent box to agree to upload this email text, then select Save report again. You can leave it unchecked to keep this result on your device.');
            $('save-status').focus();
            return;
        }
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
        let requestMayHaveBeenSent = false;
        let previousSaveUnconfirmed = false;
        try {
            const stored = await chromeImpl.storage.session.get('phishlensReportAttempt');
            if (saveEpoch !== accountEpoch) return;
            let attempt = stored.phishlensReportAttempt;
            if (attempt?.scanId !== snapshot.scanId || attempt?.subject !== input.subject) {
                attempt = { scanId: snapshot.scanId, subject: input.subject, key: globalThis.crypto.randomUUID(), submitted: false };
                await chromeImpl.storage.session.set({ phishlensReportAttempt: attempt });
            }
            previousSaveUnconfirmed = !attempt.savedId && attempt.submitted !== false;
            if (attempt.savedId) {
                savedReport = { scanId: snapshot.scanId, id: attempt.savedId };
                show('view-saved-report', true);
                text('save-status', 'Report already saved.'); return;
            }
            text('save-status', 'Preparing to save your report…');
            $('save-status').setAttribute('data-kind', 'info');
            $('save-status').setAttribute('role', 'status');
            const outcome = await saveLocalReport({
                client, baseUrl: apiOrigin, modelSha: MODEL_SHA256, input,
                idempotencyKey: attempt.key, fetchImpl,
                async beforeCreate() {
                    if (saveEpoch !== accountEpoch) throw new Error('The account changed before saving.');
                    attempt = { ...attempt, submitted: true };
                    await chromeImpl.storage.session.set({ phishlensReportAttempt: attempt });
                    if (saveEpoch !== accountEpoch) throw new Error('The account changed before saving.');
                    requestMayHaveBeenSent = true;
                }
            });
            if (saveEpoch !== accountEpoch) return;
            let markerStored = true;
            try {
                await chromeImpl.storage.session.set({ phishlensReportAttempt: { ...attempt, savedId: outcome.saved.id } });
            } catch { markerStored = false; }
            if (state?.scanId === snapshot.scanId) {
                savedReport = { scanId: snapshot.scanId, id: outcome.saved.id };
                $('save-status').setAttribute('data-kind', 'success');
                show('view-saved-report', true);
                text('save-status', !markerStored ? 'Report saved. Its local marker could not be updated. View the report before trying again.' :
                    outcome.refreshErrors.length ? 'Report saved. Some refreshes failed; view the report or refresh history.' : 'Report saved.');
            }
            controller.acceptSavedReport(outcome, { reveal: false });
        } catch (error) {
            if (saveEpoch !== accountEpoch) return;
            if (state?.scanId === snapshot.scanId) {
                $('save-status').setAttribute('data-kind', 'error');
                $('save-status').setAttribute('role', 'alert');
                reportSaveState = requestMayHaveBeenSent || previousSaveUnconfirmed ? 'unknown' : 'unsaved';
                text('save-status', reportSaveState === 'unknown'
                    ? 'Save not confirmed. Your report may have been saved. Check Saved reports before trying again; your local result is still here.'
                    : error.code === 'save_service_unavailable'
                        ? 'Report not saved. Saving is temporarily unavailable. Your local result is still here. Please try again later.'
                        : 'Report not saved. The save could not start. Your local result is still here. Please try again.');
                $('save-status').focus();
            }
        } finally {
            if (saveEpoch === accountEpoch) controller.endSave();
            if (savedReport?.scanId === snapshot.scanId && state?.scanId === snapshot.scanId) $('view-saved-report').focus();
        }
    });
    chromeImpl.storage.onChanged.addListener((changes, area) => {
        if (area === 'session' && changes.veriqoAnalysis) {
            const next = changes.veriqoAnalysis.newValue;
            if (state?.source === 'server' && !next) return;
            abortServerRequest();
            ++stateGeneration;
            render(next);
        }
    });
    chromeImpl.storage.session.get('veriqoAnalysis').then(async data => {
        if (stateGeneration === 0) render(data.veriqoAnalysis);
        await reportAccessReady;
        const markerEpoch = accountEpoch;
        const saved = await chromeImpl.storage.session.get('phishlensReportAttempt').catch(() => ({}));
        if (markerEpoch === accountEpoch) {
            const attempt = saved.phishlensReportAttempt;
            if (canAccessReports() && state?.scanId && attempt?.scanId === state.scanId && typeof attempt.subject === 'string') {
                $('report-subject').value = attempt.subject;
                if (attempt.savedId) {
                    savedReport = { scanId: state.scanId, id: attempt.savedId };
                    show('view-saved-report', true);
                    text('save-status', 'Report already saved.');
                    updateSaveControls();
                } else if (attempt.submitted !== false) {
                    reportSaveState = 'unknown';
                    updateSaveControls();
                    $('save-status').setAttribute('data-kind', 'error');
                    $('save-status').setAttribute('role', 'alert');
                    text('save-status', 'Save not confirmed. Check Saved reports before trying again. Your local result is still here.');
                }
            }
        }
    }).catch(() => {
        if (stateGeneration === 0) render({ status: 'error', error: 'Local state could not be read. Reload the extension.' });
    });
    return { loadHistory: controller.refresh, render, openDetail: controller.loadDetail, updateAccountAccess: updateSaveControls,
        resetReports({ preserveServerDraft = false } = {}) {
            ++accountEpoch;
            controller.reset();
            if (!preserveServerDraft && state?.source === 'server') {
                abortServerRequest();
                render(undefined);
            }
            savedReport = null; reportSaveState = 'unsaved';
            show('view-saved-report', false);
            text('save-status', '');
            $('report-subject').value = ''; $('save-consent').checked = false;
            updateSaveControls();
        }
    };
}

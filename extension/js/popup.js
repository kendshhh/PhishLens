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

function node(doc, tag, className, text) {
  const element = doc.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function show(element, visible) {
  element.classList.toggle("hidden", !visible);
}

export function createPopupController(client, doc = document, { onBusyChange = () => {}, onDeleted = async () => {}, onDetailShown = () => {} } = {}) {
  const $ = id => doc.getElementById(id);
  const ui = {
    status: $("crud-status"), list: $("history-list"), empty: $("empty"),
    loading: $("loading"), createForm: $("create-form"), subject: $("create-subject"),
    body: $("create-body"), detail: $("detail-panel"), detailHeading: $("detail-heading"),
    detailContent: $("detail-content"), deleteHeading: $("delete-heading"),
    editForm: $("edit-form"), notes: $("edit-notes"), feedback: $("edit-feedback"),
    deleteConfirm: $("delete-confirm"), deleteSubject: $("delete-subject"),
    deleteButton: $("confirm-delete"), cancelDelete: $("cancel-delete"),
    cancelEdit: $("cancel-edit"), saveEdit: $("save-edit"), createButton: $("create-button"),
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
    onBusyChange(value);
    if (value) { ++detailRequest; ++listRequest; show(ui.loading, false); ui.list.setAttribute('aria-busy', 'false'); }
    ui.subject.disabled = value;
    ui.body.disabled = value;
    ui.notes.disabled = value;
    ui.feedback.disabled = value;
    for (const button of [ui.createButton, ui.saveEdit, ui.cancelEdit, ui.deleteButton, ui.cancelDelete, ui.back]) {
      button.disabled = value;
    }
    ui.createButton.textContent = value ? "Saving…" : "Save analysis";
    ui.saveEdit.textContent = value ? "Saving…" : "Save changes";
    ui.deleteButton.textContent = value ? "Deleting…" : "Delete report";
  }

  function revealDetail() {
    show(ui.listView, false);
    show(ui.detail, true);
    onDetailShown();
  }

  function predictionLabel(record) {
    if (record.review_status === "uncertain" || record.analysis_provenance?.local_review?.status === "uncertain") {
      return "Uncertain — review needed";
    }
    if (record.prediction === "legitimate") return "No strong warning signs";
    return classificationLabels.get(record.prediction) ||
      (record.prediction == null ? "Not analyzed yet" : "Classification unavailable");
  }

  function renderDetail(record, { reveal = true } = {}) {
    ui.detailContent.replaceChildren();
    ui.detailHeading.textContent = record.subject || 'Untitled report';
    const analyzed = classificationLabels.has(record.prediction);
    const provenance = record.analysis_provenance && typeof record.analysis_provenance === "object"
      ? record.analysis_provenance : {};
    const provenanceLines = [provenanceLabels.get(record.analysis_mode) || "Analysis source unknown"];
    if (provenance.local_review) provenanceLines.push('The local review was reported by the browser.');
    ui.modeWarning.textContent = record.analysis_mode === 'mock' ? 'Demo result — this is not a real email assessment.' :
      record.analysis_mode !== 'real' ? 'The analysis source was not recorded. Treat this report as unverified.' : '';
    show(ui.modeWarning, Boolean(ui.modeWarning.textContent));
    const values = [
      ["Report title", record.subject || "Untitled report"], ["Email text", record.body],
      ["Summary", record.explanation || (analyzed
        ? "No explanation was returned. Review the available indicators and verify independently."
        : "Unavailable because this report has not been analyzed.")],
      ["Assessment", predictionLabel(record)],
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
      const tone = predictionLabel(record).startsWith('Uncertain') ? 'uncertain' : record.prediction === 'phishing' ? 'suspicious' : 'neutral';
      const section = node(doc, collapsed ? "details" : "div", `detail-field${label === 'Assessment' ? ` report-assessment ${tone}` : ''}${label === 'Your notes' ? ' notes-field' : ''}`);
      section.append(node(doc, collapsed ? "summary" : "h4", "", label),
        node(doc, "p", label === 'Email text' ? 'report-email-content' : '', value));
      if (label === 'Report title') section.append(node(doc, 'p', 'saved-date', 'Saved ' + new Date(record.created_at).toLocaleString(undefined,
        { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' })));
      if (label === 'Assessment') section.append(node(doc, 'p', 'field-help', 'Text screening is advisory. Verify unexpected requests independently.'));
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
      const uncertain = record.review_status === 'uncertain' || record.analysis_provenance?.local_review?.status === 'uncertain';
      const assessment = node(doc, 'span', `assessment-badge ${uncertain ? 'uncertain' : record.prediction === 'phishing' ? 'suspicious' : 'neutral'}`,
        predictionLabel(record));
      const date = node(doc, 'time', 'history-date', new Date(record.created_at).toLocaleDateString(undefined,
        { month: 'short', day: 'numeric', year: 'numeric' }));
      date.setAttribute('datetime', record.created_at);
      const preview = record.explanation?.trim() || record.threat_indicators?.[0]?.detail ||
        'Open this report to read the email and your notes.';
      meta.append(assessment, date, node(doc, 'p', 'history-preview', preview));
      item.setAttribute('data-tone', uncertain ? 'uncertain' : record.prediction === 'phishing' ? 'suspicious' : 'neutral');
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

  async function loadDetail(id, { announce = true, focus = announce } = {}) {
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
      if (request !== detailRequest) return;
      selected = result;
      renderDetail(selected);
      show(ui.editForm, false);
      show(ui.deleteConfirm, false);
      if (focus) ui.detailHeading.focus();
      if (announce) setStatus('');
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
    const operationVersion = accountVersion;
    setBusy(true);
    let created;
    try {
      created = await client.createAnalysis(input);
      if (operationVersion !== accountVersion) return;
      records = [created, ...records.filter(record => record.id !== created.id)];
      renderList();
      ui.subject.value = "";
      ui.body.value = "";
      const refreshed = await refresh();
      if (operationVersion !== accountVersion) return;
      if (refreshed) setStatus("Analysis saved successfully.", "success");
    } catch (error) {
      if (operationVersion !== accountVersion) return;
      setStatus(error instanceof SyntaxError || /Invalid/.test(error.message)
        ? "The server returned a malformed result. Your input is still here."
        : `Could not save analysis: ${error.message}. Your input is still here.`, "error");
    } finally { if (operationVersion === accountVersion) setBusy(false); }
    if (created) await loadDetail(created.id, { announce: false, focus: true });
  });

  ui.editForm.addEventListener("submit", async event => {
    event.preventDefault();
    if (busy || !selected) return;
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
    for (const input of [ui.subject, ui.body, ui.notes, ui.search]) input.value = '';
    ui.feedback.value = 'none';
    for (const panel of [ui.detail, ui.editForm, ui.deleteConfirm, ui.loading, ui.empty, ui.noMatches, ui.count]) show(panel, false);
    show(ui.listView, true);
    setStatus(''); setBusy(false);
  }
  return { refresh, loadDetail, acceptSavedReport, showLibrary, reset,
    openSavedReport(id) {
      if (selected?.id === id) { revealDetail(); ui.detailHeading.focus(); return; }
      return loadDetail(id);
    },
    beginSave() { if (busy) return false; invalidatePendingDetail(); setBusy(true); return true; },
    endSave() { setBusy(false); }, get records() { return records; } };

}


export function initializePopup({ documentImpl = document, chromeImpl = globalThis.chrome,
    fetchImpl = fetch, clientImpl = null, canAccessReports = () => true, reportAccessReady = Promise.resolve() } = {}) {
    const $ = id => documentImpl.getElementById(id);
    const client = clientImpl || createAnalysisClient(API_BASE_URL, fetchImpl, { requiredModel: MODEL_SHA256 });
    let state, stateGeneration = 0, accountEpoch = 0;
    let savedReport = null;
    let reportBusy = false;
    let reportSaveState = 'unsaved';
    const controller = createPopupController(client, documentImpl, {
        onDetailShown() { selectView('reports'); $('server-create').open = false; },
        onBusyChange(value) {
            reportBusy = value;
            updateSaveControls();
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
    function updateSaveControls() {
        const alreadySaved = Boolean(state?.scanId && savedReport?.scanId === state.scanId);
        for (const id of ['save-report', 'report-subject', 'save-consent']) $(id).disabled = reportBusy || alreadySaved || !canAccessReports();
        $('view-saved-report').disabled = reportBusy;
        show('report-save-state', !alreadySaved);
        text('report-save-state', reportSaveState === 'unknown'
            ? 'Save not confirmed. Check Saved reports before trying again.'
            : reportBusy ? 'Saving your report. Please wait for confirmation.'
                : 'Not saved yet. This result has no confirmed copy in Saved reports.');
        $('save-report').textContent = reportBusy ? 'Saving report…' : alreadySaved ? 'Report saved' : 'Save report';
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
    let submittingScan = false;
    let scanSubmission = 0;
    function setScanBusy(value) {
        for (const id of ['scan-button', 'retry-scan', 'resume-scan']) $(id).disabled = value;
    }
    async function startLocalScan(body, { keepDraft = false } = {}) {
        if (submittingScan || state?.status === 'loading') return;
        if (!body.trim() || (keepDraft && body.length > 30000)) {
            text('scan-status', 'Enter email text up to 30,000 characters.');
            $('scan-body').focus(); return;
        }
        const submission = ++scanSubmission;
        submittingScan = true;
        setScanBusy(true);
        text('scan-status', 'Starting the local scan…');
        try {
            if (keepDraft) await storeScanDraft();
            const response = await chromeImpl.runtime.sendMessage({ type: 'phishlens-analyze-text', text: body });
            if (submission !== scanSubmission) return;
            text('scan-status', response?.ok ? 'Local scan finished. Review the outcome below.' :
                'The local scan could not start. Your text is retained; try again.');
        } catch {
            if (submission !== scanSubmission) return;
            text('scan-status', 'The local scan could not start. Your text is retained; try again.');
            if (state?.status === 'error') text('error-message', 'The check could not restart. Your text is retained; try again.');
        } finally {
            if (submission === scanSubmission) { submittingScan = false; setScanBusy(false); }
        }
    }
    $('scan-form').addEventListener('submit', async event => {
        event.preventDefault();
        await startLocalScan($('scan-body').value, { keepDraft: true });
    });
    for (const id of ['retry-scan', 'resume-scan']) $(id).addEventListener('click', () => {
        if (state?.selectedText) return startLocalScan(state.selectedText);
    });
    $('cancel-scan').addEventListener('click', async () => {
        $('cancel-scan').disabled = true;
        try {
            const response = await chromeImpl.runtime.sendMessage({ type: 'phishlens-cancel-analysis' });
            if (!response?.ok) throw new Error('Cancel failed');
            ++scanSubmission;
            submittingScan = false;
            setScanBusy(false);
        } catch { text('cancel-status', 'The check could not be cancelled. Try again or clear the local scan.'); }
        finally { $('cancel-scan').disabled = false; }
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
        const stateBeforeRender = state;
        const changed = state?.scanId !== current?.scanId || state?.status !== current?.status;
        state = current;
        show('clear-button', Boolean(current));
        show('selection-instructions', !current);
        const selectedText = typeof current?.selectedText === 'string' ? current.selectedText : '';
        show('selection-preview', Boolean(selectedText));
        text('selection-content', selectedText);
        if (selectedText !== stateBeforeRender?.selectedText) $('selection-content').scrollTop = 0;
        text('selection-heading', current?.status === 'success' ? 'Analyzed email text' :
            current?.status === 'loading' ? 'Email text being checked' : 'Selected email text');
        for (const name of ['empty', 'loading', 'cancelled', 'error', 'result']) show(name + '-state', false);
        if (changed) {
            text('save-status', ''); $('save-consent').checked = false;
            $('save-status').setAttribute('data-kind', 'info');
            $('save-status').setAttribute('role', 'status');
            reportSaveState = 'unsaved';
            if (savedReport?.scanId !== current?.scanId) { savedReport = null; show('view-saved-report', false); }
        }
        updateSaveControls();
        setScanBusy(current?.status === 'loading');
        $('retry-scan').disabled = !selectedText || current?.status === 'loading';
        if (changed && current?.scanId !== stateBeforeRender?.scanId) $('report-subject').value = '';
        if (!current) {
            show('empty-state', true);
            if (stateBeforeRender) $('show-check').focus();
            return;
        }
        if (current.status === 'loading') {
            selectView('check');
            $('paste-panel').open = false;
            const stage = (current.stage || '').toLowerCase();
            const progress = /load|download|initial|gpu/.test(stage) ? 'Preparing the local review…' :
                /judge|llm/.test(stage) ? 'Reviewing the email’s wording…' :
                /reeval|classifier|krr|lightgbm/.test(stage) ? 'Comparing the checks…' : 'Checking the selected text…';
            text('workflow-progress', progress + (Number.isFinite(current.progress)
                ? ' ' + Math.round(Math.max(0, Math.min(1, current.progress)) * 100) + '%' : ''));
            text('cancel-status', '');
            show('loading-state', true); return;
        }
        if (current.status === 'cancelled') { show('cancelled-state', true); return; }
        const r = current.result;
        if (current.status !== 'success' || !r?.valid || r.model_sha256 !== MODEL_SHA256 ||
            !Number.isFinite(r.score) || !r.verification?.quote_spans_valid) {
            text('error-message', current.error || 'Invalid local scan. Reload the extension and scan again.');
            show('error-state', true); return;
        }
        $('result-state').setAttribute('data-tone', !r.workflow?.released ? 'uncertain' : r.alert ? 'suspicious' : 'below');
        text('classification', r.workflow?.released ? (r.alert ? 'Suspicious — review before acting' : 'No strong warning signs') : 'Uncertain — check before acting');
        const incompleteReason = {
            model_assets_missing: 'The local review model isn’t installed or its files could not be opened.',
            webgpu_unavailable: 'Chrome could not access the graphics support needed for the local review.',
            webgpu_fp16_unavailable: 'The graphics support available in Chrome cannot run the local review model.',
            judge_timeout: 'The local review took too long to finish.',
            judge_input_too_long_without_truncation: 'This selection is too long for the local review. Try checking a shorter section.',
            local_judge_failed: 'The local review could not start or finish in Chrome.',
            judge_service_unavailable: 'Chrome could not start the local review service.',
        }[r.workflow?.judge?.code];
        text('assessment', !r.workflow?.released
            ? (incompleteReason ? `${incompleteReason} This check is incomplete. Verify the email independently before taking action.`
                : r.workflow?.judge?.valid
                    ? 'The checks did not reach an agreed result. Verify the email independently before taking action.'
                    : 'The local review did not return a usable result. This check is incomplete. Verify the email independently before taking action.')
            : r.alert ? 'The wording raises warning signs. Avoid links or requests in this email until you verify them through a trusted contact.'
                : 'The wording checks did not find strong warning signs. This does not confirm the email is genuine; verify unexpected requests independently.');
        text('coverage', r.input_truncated ? 'Only part of this long email was checked. The result may miss details elsewhere in the text.' : '');
        if (r.evidence.length) observationRows('evidence', r.evidence.slice(0, 3));
        else rows('evidence', ['No specific wording observation was established. This is not proof that the email is genuine.']);
        observationRows('additional-evidence', r.evidence.slice(3));
        show('more-observations', r.evidence.length > 3);
        text('next-action', r.actions[0] || 'Verify unexpected requests through a trusted contact before taking action.');
        rows('recommendations', r.actions.slice(1)); rows('limitations', r.limitations);
        show('result-state', true);
        if (stateBeforeRender?.status === 'loading') $('classification').focus();
    }
    $('load-history').addEventListener('click', controller.refresh);
    $('clear-button').addEventListener('click', async () => {
        const response = await chromeImpl.runtime.sendMessage({ type: 'phishlens-clear-analysis' }).catch(() => null);
        if (!response?.ok) { text('error-message', 'Local scan could not be cleared. Reload the extension.'); show('error-state', true); }
    });
    $('save-report').addEventListener('click', async () => {
        const snapshot = state;
        const saveEpoch = accountEpoch;
        if (!canAccessReports()) { text('save-status', 'Sign in to save a personal report. Your local scan stays on this device.'); return; }
        if (snapshot?.status !== 'success' || !snapshot.result?.valid) return;
        if (savedReport?.scanId === snapshot.scanId) return;
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
                client, baseUrl: API_BASE_URL, modelSha: MODEL_SHA256, input,
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
            ++stateGeneration; render(changes.veriqoAnalysis.newValue);
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
        resetReports() {
            ++accountEpoch;
            controller.reset();
            savedReport = null; reportSaveState = 'unsaved';
            show('view-saved-report', false);
            text('save-status', '');
            $('report-subject').value = ''; $('save-consent').checked = false;
            updateSaveControls();
        }
    };
}

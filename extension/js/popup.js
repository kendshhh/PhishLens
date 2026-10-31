import { API_BASE_URL } from './config.js';
import { createAnalysisClient } from './api.js';
import { saveLocalReport } from './report-workflow.js';
import { MODEL_SHA256 } from '../ai/local-analyzer.mjs';

export function initializePopup({ documentImpl = document, chromeImpl = globalThis.chrome,
    fetchImpl = fetch } = {}) {
    const $ = id => documentImpl.getElementById(id);
    const client = createAnalysisClient(API_BASE_URL, fetchImpl, { requiredModel: MODEL_SHA256 });
    let state, detail, busy = false, historyGeneration = 0, detailGeneration = 0, stateGeneration = 0;
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
    function renderHistory(items) {
        $('history-list').replaceChildren(); show('empty', items.length === 0);
        for (const item of items) {
            const li = documentImpl.createElement('li'), button = documentImpl.createElement('button');
            const prediction = item.review_status === 'uncertain' ? 'Uncertain — local review not confirmed' : item.prediction === 'legitimate' ? 'below threshold / historical legitimate label' :
                item.prediction || 'pending';
            button.textContent = (item.subject || 'Untitled report') + ' — ' + prediction + ' — ' + item.created_at;
            button.addEventListener('click', () => openDetail(item.id));
            li.appendChild(button); $('history-list').appendChild(li);
        }
    }
    async function loadHistory() {
        const generation = ++historyGeneration;
        show('loading', true); show('error', false); show('empty', false);
        try {
            const items = await client.listAnalyses();
            if (generation === historyGeneration) renderHistory(items);
        } catch (error) {
            if (generation === historyGeneration) { text('error', message(error)); show('error', true); }
        } finally { if (generation === historyGeneration) show('loading', false); }
    }
    function renderDetail(record) {
        detail = record; show('detail-panel', true); text('detail-status', '');
        const p = record.analysis_provenance || {};
        const local = p.local_review;
        text('detail-text', [
            'Title: ' + record.subject, 'Model: ' + (p.model || 'historical / unknown'),
            'Assessment: ' + (p.assessment || record.prediction || 'unavailable'),
            ...(local ? ['Local review: ' + local.status,
                'Audit source: browser-reported LLM; classifier checks replayed by server.'] : []),
            ...(p.model_revision === MODEL_SHA256 && Number.isFinite(p.phishing_score) ?
                ['Research model score: ' + (100 * p.phishing_score).toFixed(2) + '%',
                    'Alert threshold: ' + (100 * p.alert_threshold_score).toFixed(2) + '%'] : []),
            'Saved: ' + record.created_at, '', record.explanation || 'No explanation recorded.',
            '', ...record.threat_indicators.map(i => (i.quote ? '“' + i.quote + '” — ' : '') + i.detail),
            '', 'Saved text:', record.body
        ].join('\n'));
        $('report-notes').value = record.notes || ''; $('report-feedback').value = record.feedback || 'none';
        $('delete-consent').checked = false;
    }
    async function openDetail(id) {
        if (busy) return;
        const generation = ++detailGeneration;
        try {
            const record = await client.getAnalysis(id);
            if (generation === detailGeneration) renderDetail(record);
        } catch (error) { text('error', message(error)); show('error', true); }
    }
    $('load-history').addEventListener('click', loadHistory);
    $('clear-button').addEventListener('click', async () => {
        const response = await chromeImpl.runtime.sendMessage({ type: 'phishlens-clear-analysis' }).catch(() => null);
        if (!response?.ok) { text('error-message', 'Local scan could not be cleared. Reload the extension.'); show('error-state', true); }
    });
    $('save-report').addEventListener('click', async () => {
        if (busy) return;
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
        busy = true; $('save-report').disabled = true;
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
            ++detailGeneration;
            if (outcome.history) {
                ++historyGeneration; show('loading', false); renderHistory(outcome.history);
            }
            renderDetail(outcome.detail || outcome.saved);
        } catch (error) {
            if (state?.scanId === snapshot.scanId) text('save-status', message(error) +
                ' No automatic retry was made. Retry uses the same request key, including after reopening this popup.');
        } finally { busy = false; $('save-report').disabled = false; }
    });
    $('update-report').addEventListener('click', async () => {
        if (!detail || busy) return;
        busy = true; ++detailGeneration;
        try {
            renderDetail(await client.updateAnalysis(detail.id, {
                notes: $('report-notes').value, feedback: $('report-feedback').value
            }));
            text('detail-status', 'Notes and feedback saved. Feedback does not retrain the model.');
        } catch (error) { text('detail-status', message(error)); }
        finally { busy = false; }
    });
    $('delete-report').addEventListener('click', async () => {
        if (!detail || busy) return;
        if (!$('delete-consent').checked) { text('detail-status', 'Confirm the delete checkbox first.'); return; }
        busy = true; ++detailGeneration;
        try {
            const id = detail.id;
            await client.deleteAnalysis(id);
            const stored = await chromeImpl.storage.session.get('phishlensReportAttempt');
            if (stored.phishlensReportAttempt?.savedId === id) {
                await chromeImpl.storage.session.remove('phishlensReportAttempt');
                text('save-status', 'The saved report was deleted. You may explicitly save it again.');
            }
            detail = undefined;
            show('detail-panel', false); await loadHistory();
        } catch (error) { text('detail-status', message(error)); }
        finally { busy = false; }
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
    return { loadHistory, render, openDetail };
}

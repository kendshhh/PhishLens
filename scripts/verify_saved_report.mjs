import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import { createAnalysisClient } from '../extension/js/api.js';
import { saveAnalysisAndRefresh } from '../extension/js/report-client.js';
import { verifyTarget } from './verify_crud.mjs';

export async function verifySavedReport(baseUrl, options = {}) {
    const { expectedModelSha } = options;
    if (expectedModelSha !== undefined && !/^[0-9a-f]{64}$/.test(expectedModelSha)) {
        throw new Error('A full lowercase TF-IDF model SHA-256 is required');
    }
    const target = await verifyTarget(baseUrl, options);
    if (expectedModelSha !== undefined) {
        const response = await target.safeFetch(target.baseUrl + '/model-info', {
            cache: 'no-store', signal: AbortSignal.timeout(10000)
        });
        assert.equal(response.status, 200, 'Target model identity check failed');
        const model = await response.json();
        assert.equal(model.provider_mode, 'tfidf', 'Target is not serving TF-IDF');
        assert.equal(model.accepts_tfidf_reports, true, 'Target does not accept TF-IDF reports');
        assert.equal(model.model_sha256, expectedModelSha, 'Target model SHA-256 differs');
    }
    const client = createAnalysisClient(target.baseUrl, target.safeFetch, { requiredModel: expectedModelSha });
    const input = {
        subject: 'Synthetic saved-report check ' + crypto.randomUUID(),
        body: 'Synthetic verification message. No personal content or credentials.'
    };
    const idempotencyKey = crypto.randomUUID();
    let created;
    let result;
    let failure;

    try {
        const trackedClient = {
            ...client,
            async createAnalysis(value, createOptions) {
                created = await client.createAnalysis(value, createOptions);
                return created;
            }
        };
        const report = await saveAnalysisAndRefresh(trackedClient, input, { idempotencyKey });
        assert.ok(['legitimate', 'spam', 'phishing'].includes(report.saved.prediction),
            'New report prediction must be legitimate, spam or phishing');
        assert.ok(['mock', 'real'].includes(report.saved.analysis_mode), 'New report mode must be mock or real');
        const provenance = report.saved.analysis_provenance;
        assert.ok(provenance && typeof provenance === 'object' && !Array.isArray(provenance),
            'New report requires a provenance object');
        const providers = report.saved.analysis_mode === 'mock' ? ['mock'] : ['gemini', 'local', 'tfidf'];
        assert.ok(providers.includes(provenance.provider_mode), 'New report provenance must match its mode');
        if (provenance.provider_mode === 'tfidf') {
            assert.ok(/^[0-9a-f]{64}$/.test(provenance.model_revision),
                'Saved TF-IDF report requires a model SHA-256');
        }
        if (expectedModelSha !== undefined) {
            assert.equal(provenance.provider_mode, 'tfidf', 'Saved report provider differs from TF-IDF');
            assert.equal(provenance.model_revision, expectedModelSha, 'Saved model SHA-256 differs');
        }
        if (report.refreshErrors.length) {
            throw new AggregateError(
                report.refreshErrors.map(item => item.error),
                'Creation succeeded, but report refresh failed'
            );
        }
        assert.equal(report.saved.subject, input.subject);
        assert.equal(report.saved.body, input.body);
        assert.equal(report.detail.id, report.saved.id);
        assert.equal(report.detail.body, input.body);
        const listed = report.history.find(item => item.id === report.saved.id);
        assert.ok(listed, 'Saved ID is missing from refreshed history');
        for (const field of ['subject', 'prediction', 'confidence', 'risk_level', 'explanation', 'threat_indicators']) {
            assert.deepEqual(report.detail[field], report.saved[field], 'Detail differs: ' + field);
            assert.deepEqual(listed[field], report.saved[field], 'History differs: ' + field);
        }
        const createdAt = Date.parse(report.saved.created_at);
        assert.equal(Date.parse(report.detail.created_at), createdAt, 'Detail timestamp differs');
        assert.equal(Date.parse(listed.created_at), createdAt, 'History timestamp differs');
        assert.deepEqual(report.detail.analysis_provenance, report.saved.analysis_provenance);
        assert.equal(report.detail.analysis_mode, report.saved.analysis_mode);
        result = {
            result: 'passed',
            baseUrl: target.baseUrl,
            backendSha: options.expectedSha,
            environment: options.environment,
            recordId: report.saved.id,
            analysisMode: report.saved.analysis_mode,
            providerMode: provenance.provider_mode,
            modelRevision: provenance.model_revision ?? null,
            cleanedUp: false
        };
    } catch (error) {
        failure = error;
    }

    if (created) {
        try {
            await client.deleteAnalysis(created.id);
            await assert.rejects(client.getAnalysis(created.id), error => error.status === 404);
            if (result) result.cleanedUp = true;
        } catch (cleanupError) {
            const error = new AggregateError(
                failure ? [failure, cleanupError] : [cleanupError],
                'Synthetic record cleanup could not be confirmed'
            );
            error.recordId = created.id;
            throw error;
        }
    }
    if (failure) throw failure;
    return result;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
    const args = process.argv.slice(2);
    const value = flag => {
        const index = args.indexOf(flag);
        return index === -1 ? undefined : args[index + 1];
    };
    try {
        const expectedModelSha = value('--expected-model-sha');
        if (args.includes('--expected-model-sha') && !expectedModelSha) {
            throw new Error('--expected-model-sha requires a value');
        }
        console.log(JSON.stringify(await verifySavedReport(value('--base-url'), {
            environment: value('--environment'),
            expectedSha: value('--expected-sha'),
            expectedModelSha,
            allowWrites: args.includes('--allow-writes')
        }), null, 2));
    } catch (error) {
        console.error(JSON.stringify({
            result: 'failed',
            message: error.message,
            status: error.status,
            recordId: error.recordId,
            idempotencyKey: error.idempotencyKey
        }, null, 2));
        process.exitCode = 1;
    }
}

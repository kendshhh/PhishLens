import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import { createAnalysisClient } from '../extension/js/api.js';
import { saveAnalysisAndRefresh } from '../extension/js/report-client.js';
import { verifyTarget } from './verify_crud.mjs';

export async function verifySavedReport(baseUrl, options = {}) {
    const target = await verifyTarget(baseUrl, options);
    const client = createAnalysisClient(target.baseUrl, target.safeFetch);
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
        for (const field of ['subject', 'prediction', 'confidence', 'risk_level', 'created_at']) {
            assert.deepEqual(report.detail[field], report.saved[field], 'Detail differs: ' + field);
            assert.deepEqual(listed[field], report.saved[field], 'History differs: ' + field);
        }
        assert.deepEqual(report.detail.threat_indicators, report.saved.threat_indicators);
        assert.deepEqual(report.detail.analysis_provenance, report.saved.analysis_provenance);
        assert.equal(report.detail.analysis_mode, report.saved.analysis_mode);
        result = {
            result: 'passed',
            baseUrl: target.baseUrl,
            backendSha: options.expectedSha,
            environment: options.environment,
            recordId: report.saved.id,
            analysisMode: report.saved.analysis_mode,
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
        console.log(JSON.stringify(await verifySavedReport(value('--base-url'), {
            environment: value('--environment'),
            expectedSha: value('--expected-sha'),
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

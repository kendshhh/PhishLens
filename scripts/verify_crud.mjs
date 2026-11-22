import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import { createAnalysisClient } from '../extension/js/api.js';
import { validateStagingAuthAccounts, withStagingAuth } from './staging_auth.mjs';

const ANALYSIS_MODES = new Set(['mock', 'real']);
const PROVIDER_MODES = new Set(['mock', 'gemini', 'local', 'tfidf']);
const PROVENANCE_FIELDS = [
    'provider_mode', 'model', 'model_revision', 'prompt_version',
    'explanation_source', 'input_truncated', 'windows_processed'
];

function assertReportProvenance(report) {
    assert.ok(ANALYSIS_MODES.has(report.analysis_mode), 'Invalid analysis_mode');
    const provenance = report.analysis_provenance;
    assert.ok(provenance && typeof provenance === 'object' && !Array.isArray(provenance),
        'Saved report must include analysis_provenance');
    for (const field of PROVENANCE_FIELDS) {
        assert.ok(Object.hasOwn(provenance, field), 'Provenance is missing: ' + field);
    }
    assert.ok(PROVIDER_MODES.has(provenance.provider_mode), 'Invalid provider_mode');
    assert.equal(report.analysis_mode,
        provenance.provider_mode === 'mock' ? 'mock' : 'real',
        'analysis_mode does not match provider_mode');
    for (const field of ['model', 'model_revision', 'prompt_version']) {
        assert.ok(provenance[field] === null || typeof provenance[field] === 'string',
            'Invalid provenance field: ' + field);
    }
    assert.ok(provenance.explanation_source === null ||
        ['model', 'rules', 'mock'].includes(provenance.explanation_source),
        'Invalid explanation_source');
    assert.ok(provenance.input_truncated === null || typeof provenance.input_truncated === 'boolean',
        'Invalid input_truncated');
    assert.ok(provenance.windows_processed === null ||
        (Number.isInteger(provenance.windows_processed) && provenance.windows_processed >= 1),
        'Invalid windows_processed');
}

function assertReportMatches(actual, expected) {
    for (const field of [
        'subject', 'prediction', 'confidence', 'risk_level', 'threat_indicators',
        'explanation', 'created_at', 'analysis_mode', 'analysis_provenance'
    ]) {
        assert.deepEqual(actual[field], expected[field], 'Report differs in ' + field);
    }
}

function assertSummaryMatches(actual, expected) {
    // The history endpoint deliberately exposes summaries. Provenance, body,
    // notes, and feedback are available only from the detail endpoint.
    for (const field of [
        'id', 'subject', 'prediction', 'confidence', 'risk_level',
        'threat_indicators', 'explanation'
    ]) {
        assert.deepEqual(actual[field], expected[field], 'Summary differs in ' + field);
    }
    assert.equal(Date.parse(actual.created_at), Date.parse(expected.created_at),
        'Summary differs in created_at');
}

export async function verifyTarget(baseUrl, options) {
    const { environment, expectedSha, allowWrites } = options;
    if (allowWrites !== true) throw new Error('Explicit write permission is required');
    if (!/^[0-9a-f]{40}$/i.test(expectedSha || '')) {
        throw new Error('A full expected backend commit SHA is required');
    }
    const url = new URL(baseUrl);
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password ||
        url.pathname !== '/' || url.search || url.hash) {
        throw new Error('Use a plain HTTP(S) origin without credentials, paths or queries');
    }
    const local = ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname);
    const staging = url.origin === 'https://phishlens-staging.onrender.com';
    if (!(local && ['demo', 'disposable'].includes(environment)) &&
        !(staging && environment === 'staging')) {
        throw new Error('Target must be loopback demo/disposable or the approved staging origin');
    }
    const safeFetch = (address, init = {}) => {
        if (new URL(address).origin !== url.origin) throw new Error('Cross-origin request refused');
        return fetch(address, { ...init, redirect: 'error' });
    };
    // Render can report the requested commit live just before its public
    // routing has fully converged. Retry only on the approved hosted staging
    // origin, and block every write until the exact environment and SHA match.
    const identityDeadline = staging ? Date.now() + 180000 : Date.now();
    let identityMatches = false;
    while (!identityMatches) {
        try {
            const response = await safeFetch(url.origin + '/version', {
                cache: 'no-store',
                headers: { 'Cache-Control': 'no-cache', 'Pragma': 'no-cache' },
                signal: AbortSignal.timeout(10000)
            });
            if (response.status === 200) {
                const identity = await response.json();
                identityMatches = identity.environment === environment &&
                    identity.commit === expectedSha;
                if (!identityMatches && !staging) {
                    throw new Error('Target environment or backend SHA does not match');
                }
            } else if (!staging) {
                throw new Error('Target identity check failed');
            }
        } catch (error) {
            // Only the remote staging rollout gets bounded retries. Local
            // fixtures and every other target retain immediate failure.
            if (!staging) throw error;
        }
        if (identityMatches) break;
        const remaining = identityDeadline - Date.now();
        if (remaining <= 0) {
            throw new Error(staging
                ? 'Target environment or backend SHA did not match after waiting for staging to converge'
                : 'Target identity check failed');
        }
        await new Promise(resolve => setTimeout(resolve, Math.min(5000, remaining)));
    }
    const ready = await safeFetch(url.origin + '/ready', {
        signal: AbortSignal.timeout(10000)
    });
    if (ready.status !== 200) throw new Error('Test database is not ready');
    const readiness = await ready.json();
    if (readiness.status !== 'ready' || readiness.database !== 'connected') {
        throw new Error('Test database is not ready');
    }
    return { baseUrl: url.origin, safeFetch };
}

export async function verifyReportIsolation(client, analysisId) {
    const visibleRecords = await client.listAnalyses();
    assert.ok(!visibleRecords.some(record => record.id === analysisId),
        'Another Auth user can list this saved report');
    await assert.rejects(client.getAnalysis(analysisId), error => error.status === 404,
        'Another Auth user can read this saved report');
    await assert.rejects(
        client.updateAnalysis(analysisId, { notes: 'Unauthorized isolation probe' }),
        error => error.status === 404,
        'Another Auth user can update this saved report'
    );
    await assert.rejects(client.deleteAnalysis(analysisId), error => error.status === 404,
        'Another Auth user can delete this saved report');
    return 'passed';
}

async function verifyCrudWithClient(target, options, getAccessToken, verifyIsolation) {
    const client = createAnalysisClient(target.baseUrl, target.safeFetch, { getAccessToken });
    const requireRealAI = options.requireRealAI === true;
    const subject = 'Synthetic CRUD check ' + crypto.randomUUID();
    const body = 'Synthetic test email. No real user data or credentials.';
    let created;
    let deleted = false;
    try {
        created = await client.createAnalysis({ subject, body });
        assertReportProvenance(created);
        if (requireRealAI && created.analysis_mode !== 'real') {
            throw new Error('Mock output is not AI acceptance');
        }
        assert.equal(created.subject, subject);
        if (verifyIsolation) await verifyIsolation(created.id);
        const reloadedClient = createAnalysisClient(target.baseUrl, target.safeFetch, {
            getAccessToken
        });
        const persistedItems = await reloadedClient.listAnalyses();
        const persisted = persistedItems.find(record => record.id === created.id);
        assert.ok(persisted, 'Created report must persist after a fresh client is created');
        assertSummaryMatches(persisted, created);
        const read = await client.getAnalysis(created.id);
        assertReportProvenance(read);
        assert.equal(read.subject, subject);
        assert.equal(read.body, body);
        assertReportMatches(read, created);
        const records = await client.listAnalyses();
        const listed = records.find(record => record.id === created.id);
        assert.ok(listed, 'Created report must persist in history');
        assertSummaryMatches(listed, created);
        const createdAt = Date.parse(created.created_at);
        assert.ok(Number.isFinite(createdAt), 'Created report timestamp is invalid');
        await client.updateAnalysis(created.id, { notes: 'CRUD verification', feedback: 'false_positive' });
        const edited = await client.getAnalysis(created.id);
        assertReportProvenance(edited);
        assert.equal(edited.notes, 'CRUD verification');
        assert.equal(edited.feedback, 'false_positive');
        assertReportMatches(edited, created);
        await client.updateAnalysis(created.id, { notes: null });
        const cleared = await client.getAnalysis(created.id);
        assertReportProvenance(cleared);
        assert.equal(cleared.notes, null);
        assert.equal(cleared.feedback, 'false_positive');
        assertReportMatches(cleared, created);
        await client.deleteAnalysis(created.id);
        deleted = true;
        await assert.rejects(client.getAnalysis(created.id), error => error.status === 404);
        return { result: 'passed', baseUrl: target.baseUrl, recordId: created.id,
                 analysisMode: created.analysis_mode,
                 analysisProvenance: {
                     providerMode: created.analysis_provenance.provider_mode,
                     model: created.analysis_provenance.model,
                     modelRevision: created.analysis_provenance.model_revision,
                     promptVersion: created.analysis_provenance.prompt_version
                 },
                 persistenceAfterReload: true,
                 userIsolation: verifyIsolation ? 'passed' : 'not_checked',
                 cleanedUp: true };
    } finally {
        // Clean up only the record created by this run.
        if (created && !deleted) {
            try {
                await client.deleteAnalysis(created.id);
            } catch (error) {
                // An isolation failure may have allowed the second account to
                // delete this record. Preserve that failure after confirming
                // that the run-created record is already gone.
                if (error.status !== 404) throw error;
            }
        }
    }
}

export async function verifyCrud(baseUrl, options = {}) {
    const target = await verifyTarget(baseUrl, options);
    if (options.authenticate !== true) {
        return verifyCrudWithClient(target, options);
    }

    const anonymous = await target.safeFetch(target.baseUrl + '/api/analyses', {
        cache: 'no-store', signal: AbortSignal.timeout(10000)
    });
    assert.equal(anonymous.status, 401,
        'Authenticated staging must reject anonymous saved-report access');
    assert.match(anonymous.headers.get('www-authenticate') || '', /^Bearer(?:\s|$)/i,
        'Anonymous rejection must include a Bearer challenge');

    const authEnvironment = options.authEnvironment ?? process.env;
    validateStagingAuthAccounts(authEnvironment);
    return withStagingAuth(async getAccessTokenA =>
        verifyCrudWithClient(target, options, getAccessTokenA, async analysisId =>
            withStagingAuth(async getAccessTokenB => {
                const accountBClient = createAnalysisClient(target.baseUrl, target.safeFetch, {
                    getAccessToken: getAccessTokenB
                });
                return verifyReportIsolation(accountBClient, analysisId);
            }, authEnvironment, 'B')),
    authEnvironment, 'A');
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
    const args = process.argv.slice(2);
    const authenticated = args.includes('--authenticate');
    function value(flag) {
        const index = args.indexOf(flag);
        return index === -1 ? undefined : args[index + 1];
    }
    try {
        const result = await verifyCrud(value('--base-url'), {
            environment: value('--environment'),
            expectedSha: value('--expected-sha'),
            allowWrites: args.includes('--allow-writes'),
            authenticate: authenticated,
            requireRealAI: args.includes('--require-real-ai')
        });
        console.log(JSON.stringify(result, null, 2));
    } catch (error) {
        console.error(authenticated
            ? JSON.stringify({
                result: 'failed',
                message: error.message || 'Authenticated staging verification failed.',
                status: error.status ?? null,
                recordId: error.recordId ?? null
            }, null, 2)
            : error.message);
        process.exitCode = 1;
    }
}


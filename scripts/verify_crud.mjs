import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import { createAnalysisClient } from '../extension/js/api.js';
import { createNeonAccounts } from '../extension/js/neon-accounts.js';
import { BetterAuthVanillaAdapter, createAuthClient } from '../extension/vendor/neon/sdk.mjs';

const ANALYSIS_MODES = new Set(['mock', 'real']);
const PROVIDER_MODES = new Set(['mock', 'gemini', 'local', 'tfidf']);
const PROVENANCE_FIELDS = [
    'provider_mode', 'model', 'model_revision', 'prompt_version',
    'explanation_source', 'input_truncated', 'windows_processed'
];
const STAGING_NEON_AUTH_HOST = 'ep-winter-wind-a1y2r1db.neonauth.ap-southeast-1.aws.neon.tech';
const STAGING_NEON_AUTH_DATABASE = 'neondb';
const STAGING_CHROME_ORIGIN = /^chrome-extension:\/\/[a-p]{32}$/;

function cookiePathMatches(pathname, cookiePath) {
    if (!cookiePath.startsWith('/')) return false;
    return pathname === cookiePath || pathname.startsWith(cookiePath.endsWith('/') ? cookiePath : cookiePath + '/');
}

export function validateStagingAuthConfig({ authUrl, database, trustedOrigin }) {
    let target;
    try { target = new URL(authUrl); }
    catch { throw new Error('Staging Auth configuration is missing or invalid.'); }
    if (target.protocol !== 'https:' || target.username || target.password || target.search || target.hash ||
        target.host !== STAGING_NEON_AUTH_HOST || database !== STAGING_NEON_AUTH_DATABASE ||
        target.pathname !== `/${STAGING_NEON_AUTH_DATABASE}/auth` || !STAGING_CHROME_ORIGIN.test(trustedOrigin || '')) {
        throw new Error('Staging Auth must target the reviewed isolated Neon Auth endpoint and extension origin.');
    }
    return target;
}

export function createAuthCookieFetch({ authOrigin, trustedOrigin, fetchImpl = globalThis.fetch }) {
    const cookies = new Map();
    const target = new URL(authOrigin);
    if (target.protocol !== 'https:' || target.origin !== authOrigin || !STAGING_CHROME_ORIGIN.test(trustedOrigin || '')) {
        throw new Error('Staging Auth transport configuration is invalid.');
    }
    const wrapped = async (input, init = {}) => {
        const requestUrl = new URL(typeof input === 'string' || input instanceof URL ? input.toString() : input.url);
        if (requestUrl.origin !== target.origin) throw new Error('Staging Auth attempted an unexpected origin.');
        const headers = new Headers(input instanceof Request ? input.headers : undefined);
        new Headers(init.headers || {}).forEach((value, name) => headers.set(name, value));
        headers.set('Origin', trustedOrigin);
        const cookie = [...cookies.values()]
            .filter(entry => cookiePathMatches(requestUrl.pathname, entry.path))
            .map(entry => `${entry.name}=${entry.value}`)
            .join('; ');
        if (cookie) headers.set('Cookie', cookie);
        else headers.delete('Cookie');
        const response = await fetchImpl(input, { ...init, headers });
        if (typeof response.headers.getSetCookie !== 'function') {
            throw new Error('Staging Auth transport cannot safely retain session cookies.');
        }
        for (const value of response.headers.getSetCookie()) {
            const [pair = '', ...attributes] = value.split(';');
            const separator = pair.indexOf('=');
            if (separator < 1) continue;
            const name = pair.slice(0, separator).trim();
            const cookieValue = pair.slice(separator + 1).trim();
            const pathAttribute = attributes.find(attribute => /^\s*path=/i.test(attribute));
            const path = pathAttribute ? pathAttribute.slice(pathAttribute.indexOf('=') + 1).trim() : '/';
            const maxAgeAttribute = attributes.find(attribute => /^\s*max-age=/i.test(attribute));
            const maxAge = maxAgeAttribute ? Number(maxAgeAttribute.slice(maxAgeAttribute.indexOf('=') + 1)) : null;
            const expiresAttribute = attributes.find(attribute => /^\s*expires=/i.test(attribute));
            const expired = expiresAttribute && Date.parse(expiresAttribute.slice(expiresAttribute.indexOf('=') + 1)) <= Date.now();
            if (!cookieValue || maxAge !== null && Number.isFinite(maxAge) && maxAge <= 0 || expired) cookies.delete(name);
            else cookies.set(name, { name, value: cookieValue, path });
        }
        return response;
    };
    wrapped.clearCookies = () => cookies.clear();
    return wrapped;
}

async function stagingAccessToken({ label, email, password, authUrl, database, trustedOrigin }) {
    const target = validateStagingAuthConfig({ authUrl, database, trustedOrigin });
    if (!email || !password) throw new Error(`Staging synthetic account ${label} credentials are not configured.`);
    const originalFetch = globalThis.fetch;
    const authFetch = createAuthCookieFetch({ authOrigin: target.origin, trustedOrigin });
    globalThis.fetch = authFetch;
    let succeeded = false;
    let accounts;
    try {
        const auth = createAuthClient(target.href, {
            adapter: BetterAuthVanillaAdapter({ fetchOptions: {
                credentials: 'include', redirect: 'error', timeout: 10000, retry: 0
            } })
        });
        accounts = createNeonAccounts(auth, { timeoutMs: 15000 });
        const session = await accounts.signIn({ email, password });
        if (!session?.user?.id || session.user.emailVerified !== true) {
            throw new Error('Verified account session unavailable.');
        }
        const token = await accounts.getAccessToken(session.user.id);
        if (typeof token !== 'string' || !token) throw new Error('Verified access token unavailable.');
        succeeded = true;
        return {
            token,
            signOut: async () => {
                const activeFetch = globalThis.fetch;
                globalThis.fetch = authFetch;
                try {
                    await accounts.signOut();
                } catch {
                    throw new Error(`Staging synthetic account ${label} could not close its test session.`);
                } finally {
                    globalThis.fetch = activeFetch;
                    authFetch.clearCookies();
                }
            }
        };
    } catch {
        authFetch.clearCookies();
        throw new Error(`Staging synthetic account ${label} could not sign in with a verified session.`);
    } finally {
        globalThis.fetch = originalFetch;
        if (!succeeded) authFetch.clearCookies();
    }
}

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

export async function verifyCrud(baseUrl, options = {}) {
    const target = await verifyTarget(baseUrl, options);
    const client = createAnalysisClient(target.baseUrl, target.safeFetch);
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
                 cleanedUp: true };
    } finally {
        // Clean up only the record created by this run.
        if (created && !deleted) await client.deleteAnalysis(created.id);
    }
}

export async function verifyAuthenticatedCrud(baseUrl, options = {}) {
    const target = await verifyTarget(baseUrl, options);
    const authConfig = {
        authUrl: options.authUrl || process.env.STAGING_NEON_AUTH_URL,
        database: options.authDatabase || process.env.STAGING_NEON_AUTH_DATABASE,
        trustedOrigin: options.trustedOrigin || process.env.STAGING_AUTH_TRUSTED_CHROME_ORIGIN
    };
    let accountA, accountB, clientA, clientB;
    const runId = crypto.randomUUID();
    const inputA = { subject: `Synthetic hosted staging CRUD ${runId} A`, body: 'Synthetic verification message; no personal content or credentials.' };
    const inputB = { subject: `Synthetic hosted staging CRUD ${runId} B`, body: 'Synthetic verification message; no personal content or credentials.' };
    const keyA = `hosted-staging-${runId}-a`, keyB = `hosted-staging-${runId}-b`;
    let createdA, createdB, cleanedUp = false;
    try {
        accountA = await stagingAccessToken({
            ...authConfig, label: 'A',
            email: options.accountAEmail || process.env.STAGING_AUTH_USER_A_EMAIL,
            password: options.accountAPassword || process.env.STAGING_AUTH_USER_A_PASSWORD
        });
        accountB = await stagingAccessToken({
            ...authConfig, label: 'B',
            email: options.accountBEmail || process.env.STAGING_AUTH_USER_B_EMAIL,
            password: options.accountBPassword || process.env.STAGING_AUTH_USER_B_PASSWORD
        });
        clientA = createAnalysisClient(target.baseUrl, target.safeFetch, { getAccessToken: async () => accountA.token });
        clientB = createAnalysisClient(target.baseUrl, target.safeFetch, { getAccessToken: async () => accountB.token });
        createdA = await clientA.createAnalysis(inputA, { idempotencyKey: keyA });
        assertReportProvenance(createdA);
        assert.equal(createdA.subject, inputA.subject);
        const replayA = await clientA.createAnalysis(inputA, { idempotencyKey: keyA });
        assert.equal(replayA.id, createdA.id, 'An identical create must replay the original report');
        await assert.rejects(
            clientA.createAnalysis({ ...inputA, body: inputA.body + ' changed' }, { idempotencyKey: keyA }),
            error => error.status === 409,
            'A changed create with the same key must conflict'
        );
        createdB = await clientB.createAnalysis(inputB, { idempotencyKey: keyB });
        assertReportProvenance(createdB);
        assert.equal(createdB.subject, inputB.subject);

        const [listA, listB] = await Promise.all([clientA.listAnalyses(), clientB.listAnalyses()]);
        assert.ok(listA.some(report => report.id === createdA.id), 'Account A must list its report');
        assert.ok(!listA.some(report => report.id === createdB.id), 'Account A must not list account B reports');
        assert.ok(listB.some(report => report.id === createdB.id), 'Account B must list its report');
        assert.ok(!listB.some(report => report.id === createdA.id), 'Account B must not list account A reports');

        await assert.rejects(clientB.getAnalysis(createdA.id), error => error.status === 404);
        await assert.rejects(clientB.updateAnalysis(createdA.id, { notes: 'cross-account write probe' }), error => error.status === 404);
        await assert.rejects(clientB.deleteAnalysis(createdA.id), error => error.status === 404);
        await assert.rejects(clientA.getAnalysis(createdB.id), error => error.status === 404);
        await assert.rejects(clientA.updateAnalysis(createdB.id, { notes: 'cross-account write probe' }), error => error.status === 404);
        await assert.rejects(clientA.deleteAnalysis(createdB.id), error => error.status === 404);

        const beforeEditA = await clientA.getAnalysis(createdA.id);
        assertReportProvenance(beforeEditA);
        assert.equal(beforeEditA.body, inputA.body);
        await clientA.updateAnalysis(createdA.id, { notes: 'CRUD verification', feedback: 'false_positive' });
        const editedA = await clientA.getAnalysis(createdA.id);
        assert.equal(editedA.notes, 'CRUD verification');
        assert.equal(editedA.feedback, 'false_positive');
        await clientA.updateAnalysis(createdA.id, { notes: null });
        const clearedA = await clientA.getAnalysis(createdA.id);
        assert.equal(clearedA.notes, null);
        assert.equal(clearedA.feedback, 'false_positive');
        assert.equal((await clientB.getAnalysis(createdB.id)).id, createdB.id);

        await clientA.deleteAnalysis(createdA.id);
        await clientB.deleteAnalysis(createdB.id);
        createdA = null; createdB = null; cleanedUp = true;
        return {
            result: 'passed', baseUrl: target.baseUrl, authMode: 'neon',
            analysisMode: beforeEditA.analysis_mode,
            analysisProvenance: {
                providerMode: beforeEditA.analysis_provenance.provider_mode,
                model: beforeEditA.analysis_provenance.model,
                modelRevision: beforeEditA.analysis_provenance.model_revision,
                promptVersion: beforeEditA.analysis_provenance.prompt_version
            },
            checks: ['verified sign-in for two synthetic accounts', 'create/replay/conflict',
                'per-account list isolation', 'cross-account read/patch/delete return 404',
                'owner read/edit/clear/delete', 'synthetic report provenance'],
            cleanedUp
        };
    } finally {
        let cleanupFailed = false;
        if (createdA && clientA) await clientA.deleteAnalysis(createdA.id).catch(error => { if (error.status !== 404) cleanupFailed = true; });
        if (createdB && clientB) await clientB.deleteAnalysis(createdB.id).catch(error => { if (error.status !== 404) cleanupFailed = true; });
        for (const account of [accountA, accountB]) {
            if (!account) continue;
            try { await account.signOut(); }
            catch { cleanupFailed = true; }
        }
        if (cleanupFailed) throw new Error('Hosted staging synthetic records or account sessions could not be cleaned up.');
    }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
    const args = process.argv.slice(2);
    function value(flag) {
        const index = args.indexOf(flag);
        return index === -1 ? undefined : args[index + 1];
    }
    try {
        const options = {
            environment: value('--environment'),
            expectedSha: value('--expected-sha'),
            allowWrites: args.includes('--allow-writes'),
            requireRealAI: args.includes('--require-real-ai')
        };
        const result = options.environment === 'staging'
            ? await verifyAuthenticatedCrud(value('--base-url'), options)
            : await verifyCrud(value('--base-url'), options);
        console.log(JSON.stringify(result, null, 2));
    } catch (error) {
        console.error(error.message);
        process.exitCode = 1;
    }
}


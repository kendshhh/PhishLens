import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import { createAnalysisClient } from '../extension/js/api.js';

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
    const response = await safeFetch(url.origin + '/version', {
        signal: AbortSignal.timeout(10000)
    });
    if (response.status !== 200) throw new Error('Target identity check failed');
    const identity = await response.json();
    if (identity.environment !== environment || identity.commit !== expectedSha) {
        throw new Error('Target environment or backend SHA does not match');
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
    const subject = 'Synthetic CRUD check ' + crypto.randomUUID();
    let created;
    let deleted = false;
    try {
        created = await client.createAnalysis({ subject, body: 'Synthetic test email. No real user data.' });
        assert.equal(created.subject, subject);
        const read = await client.getAnalysis(created.id);
        assert.equal(read.subject, subject);
        assert.equal(read.body, 'Synthetic test email. No real user data.');
        const records = await client.listAnalyses();
        assert.ok(records.some(record => record.id === created.id));
        await client.updateAnalysis(created.id, { notes: 'CRUD verification', feedback: 'false_positive' });
        const edited = await client.getAnalysis(created.id);
        assert.equal(edited.notes, 'CRUD verification');
        assert.equal(edited.feedback, 'false_positive');
        assert.equal(edited.subject, subject);
        await client.updateAnalysis(created.id, { notes: null });
        const cleared = await client.getAnalysis(created.id);
        assert.equal(cleared.notes, null);
        assert.equal(cleared.feedback, 'false_positive');
        await client.deleteAnalysis(created.id);
        deleted = true;
        await assert.rejects(client.getAnalysis(created.id), error => error.status === 404);
        return { result: 'passed', baseUrl, recordId: created.id };
    } finally {
        // Clean up only the record created by this run.
        if (created && !deleted) await client.deleteAnalysis(created.id);
    }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
    const args = process.argv.slice(2);
    function value(flag) {
        const index = args.indexOf(flag);
        return index === -1 ? undefined : args[index + 1];
    }
    try {
        const result = await verifyCrud(value('--base-url'), {
            environment: value('--environment'),
            expectedSha: value('--expected-sha'),
            allowWrites: args.includes('--allow-writes')
        });
        console.log(JSON.stringify(result, null, 2));
    } catch (error) {
        console.error(error.message);
        process.exitCode = 1;
    }
}

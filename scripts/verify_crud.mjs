import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import { createAnalysisClient } from '../extension/js/api.js';

export async function verifyCrud(baseUrl) {
    const client = createAnalysisClient(baseUrl);
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
    const baseUrl = args[args.indexOf('--base-url') + 1];
    const environment = args[args.indexOf('--environment') + 1];
    if (!args.includes('--base-url') || !baseUrl ||
        !args.includes('--allow-writes') ||
        !['demo', 'disposable'].includes(environment)) {
        console.error('Use --base-url URL --environment demo|disposable --allow-writes only for a confirmed test database.');
        process.exitCode = 1;
    } else {
        try {
            const url = new URL(baseUrl);
            if (!['http:', 'https:'].includes(url.protocol)) throw new Error('Use an HTTP or HTTPS URL');
            console.log(JSON.stringify(await verifyCrud(baseUrl), null, 2));
        } catch (error) {
            console.error(error.message);
            process.exitCode = 1;
        }
    }
}

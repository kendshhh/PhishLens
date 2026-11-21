import assert from 'node:assert/strict';
import test from 'node:test';

import { readStagingHistory } from '../staging_history.mjs';

test('accepts anonymous history rejection when the API requires Bearer auth', async () => {
    const items = await readStagingHistory('https://staging.example.test/', async url => {
        assert.equal(url, 'https://staging.example.test/api/analyses');
        return new Response(JSON.stringify({ detail: 'Sign in to access saved reports' }), {
            status: 401,
            headers: { 'WWW-Authenticate': 'Bearer' }
        });
    });

    assert.equal(items, null);
});

test('rejects an unauthorized response without a Bearer challenge', async () => {
    await assert.rejects(
        readStagingHistory('https://staging.example.test', async () => new Response(null, { status: 401 })),
        /without a Bearer challenge/
    );
});

test('reports other staging history HTTP errors with their status', async () => {
    await assert.rejects(
        readStagingHistory('https://staging.example.test', async () => new Response(null, { status: 503 })),
        /HTTP 503/
    );
});

test('returns seeded history items in demo mode', async () => {
    const expected = [{ id: 'demo-id', subject: 'Synthetic account notice' }];
    const items = await readStagingHistory('https://staging.example.test', async () =>
        Response.json({ items: expected })
    );

    assert.deepEqual(items, expected);
});

test('rejects an invalid history response wrapper', async () => {
    await assert.rejects(
        readStagingHistory('https://staging.example.test', async () => Response.json({ analyses: [] })),
        /Invalid staging history data/
    );
});

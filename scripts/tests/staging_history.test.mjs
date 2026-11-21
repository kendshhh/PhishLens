import assert from 'node:assert/strict';
import test from 'node:test';

import {
    isRetryableStagingHistoryError,
    readStagingHistory,
} from '../staging_history.mjs';

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

for (const [status, body] of [
    [400, 'request timeout'],
    [401, 'fetch failed'],
    [403, 'timeout while checking authorization'],
]) {
    test(`does not retry permanent HTTP ${status} when the body looks transient`, async () => {
        let error;
        try {
            await readStagingHistory('https://staging.example.test', async () =>
                new Response(body, { status })
            );
        } catch (caught) {
            error = caught;
        }

        assert.ok(error);
        assert.equal(error.status, status);
        assert.match(error.message, /timeout|fetch failed/i);
        assert.equal(isRetryableStagingHistoryError(error), false);
    });
}

test('retries only explicitly transient HTTP statuses', () => {
    for (const status of [408, 425, 429, 500, 502, 503, 504, 599]) {
        assert.equal(isRetryableStagingHistoryError({ status }), true, `HTTP ${status}`);
    }
    for (const status of [400, 401, 403, 404]) {
        assert.equal(isRetryableStagingHistoryError({ status }), false, `HTTP ${status}`);
    }
});

test('matches network failure text only when no HTTP response exists', () => {
    assert.equal(isRetryableStagingHistoryError(new TypeError('fetch failed')), true);
    assert.equal(isRetryableStagingHistoryError(new Error('request timed out')), true);
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

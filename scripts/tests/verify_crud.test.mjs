import test from 'node:test';
import assert from 'node:assert/strict';
import { createAuthCookieFetch, validateStagingAuthConfig } from '../verify_crud.mjs';

const authUrl = 'https://ep-winter-wind-a1y2r1db.neonauth.ap-southeast-1.aws.neon.tech/neondb/auth';
const trustedOrigin = 'chrome-extension://abcdefghijklmnopabcdefghijklmnop';

test('hosted auth is pinned to the isolated staging Neon endpoint and extension origin', () => {
    assert.equal(validateStagingAuthConfig({ authUrl, database: 'neondb', trustedOrigin }).href, authUrl);
    assert.throws(() => validateStagingAuthConfig({
        authUrl: authUrl.replace('ep-winter-wind-a1y2r1db', 'ep-dawn-band-b37l1bil'),
        database: 'neondb', trustedOrigin
    }), /reviewed isolated Neon Auth endpoint/);
    assert.throws(() => validateStagingAuthConfig({ authUrl, database: 'other', trustedOrigin }),
        /reviewed isolated Neon Auth endpoint/);
    assert.throws(() => validateStagingAuthConfig({ authUrl, database: 'neondb', trustedOrigin: 'https://example.test' }),
        /reviewed isolated Neon Auth endpoint/);
});

test('auth cookie transport retains only scoped cookies and refuses cross-origin requests', async () => {
    const requests = [];
    const fetchImpl = async (input, init) => {
        requests.push({ url: new URL(input.toString()), headers: new Headers(init.headers) });
        return new Response('{}', {
            status: 200,
            headers: [['set-cookie', 'session=opaque-cookie; Path=/neondb/auth; Secure; HttpOnly; SameSite=Lax']]
        });
    };
    const authFetch = createAuthCookieFetch({ authOrigin: new URL(authUrl).origin, trustedOrigin, fetchImpl });
    await authFetch(authUrl + '/sign-in/email', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
    await authFetch(authUrl + '/get-session', { method: 'GET' });
    assert.equal(requests[0].headers.get('cookie'), null);
    assert.equal(requests[1].headers.get('cookie'), 'session=opaque-cookie');
    assert.equal(requests[1].headers.get('origin'), trustedOrigin);
    await authFetch(new URL('/outside/auth', authUrl), { method: 'GET' });
    assert.equal(requests[2].headers.get('cookie'), null);
    assert.equal(requests[2].headers.get('origin'), trustedOrigin);
    await assert.rejects(authFetch('https://example.test/neondb/auth/get-session'), /unexpected origin/);
    authFetch.clearCookies();
    await authFetch(authUrl + '/get-session', { method: 'GET' });
    assert.equal(requests[3].headers.get('cookie'), null);
});


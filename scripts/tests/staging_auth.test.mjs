import test from 'node:test';
import assert from 'node:assert/strict';
import {
    createAuthCookieFetch,
    validateStagingAccessToken,
    validateStagingAuthAccounts,
    validateStagingAuthConfig,
    withStagingAuth
} from '../staging_auth.mjs';
import { createAuthCookieFetch as createAuthCookieFetchFromVerifier,
    validateStagingAuthConfig as validateStagingAuthConfigFromVerifier,
    verifyReportIsolation,
    verifyReportPairIsolation,
    verifyTarget
} from '../verify_crud.mjs';

const authUrl = 'https://ep-winter-wind-a1y2r1db.neonauth.ap-southeast-1.aws.neon.tech/neondb/auth';
const authOrigin = new URL(authUrl).origin;
const trustedOrigin = 'chrome-extension://abcdefghijklmnopabcdefghijklmnop';
const authEnvironment = {
    STAGING_BASE_URL: 'https://phishlens-staging.onrender.com',
    STAGING_NEON_AUTH_URL: authUrl,
    PHISHLENS_STAGING_AUTH_DATABASE: 'neondb',
    STAGING_AUTH_TRUSTED_CHROME_ORIGIN: trustedOrigin,
    STAGING_AUTH_USER_A_EMAIL: 'account-a@example.test',
    STAGING_AUTH_USER_A_PASSWORD: 'synthetic-a-password',
    STAGING_AUTH_USER_B_EMAIL: 'account-b@example.test',
    STAGING_AUTH_USER_B_PASSWORD: 'synthetic-b-password'
};

function jwt(claims) {
    return 'header.' + Buffer.from(JSON.stringify(claims)).toString('base64url') + '.signature';
}

function claims(overrides = {}) {
    return {
        sub: 'synthetic-user-a',
        iss: authOrigin,
        aud: authOrigin,
        email: 'account-a@example.test',
        emailVerified: true,
        banned: false,
        exp: Math.floor(Date.now() / 1000) + 300,
        ...overrides
    };
}

test('Auth config requires the staging Neon path, protected extension origin, and distinct A/B accounts', () => {
    assert.equal(validateStagingAuthConfig({
        authUrl, database: 'neondb', trustedOrigin
    }).href, authUrl);
    assert.equal(validateStagingAuthAccounts(authEnvironment).A.email, 'account-a@example.test');
    assert.throws(() => validateStagingAuthConfig({
        ...authEnvironment, STAGING_NEON_AUTH_URL: authUrl.replace('ep-winter-wind-a1y2r1db', 'ep-other-branch')
    }), /reviewed isolated Neon Auth endpoint/);
    assert.equal(typeof createAuthCookieFetchFromVerifier, 'function');
    assert.equal(validateStagingAuthConfigFromVerifier({ authUrl, database: 'neondb', trustedOrigin }).href, authUrl);

    assert.throws(() => validateStagingAuthConfig({
        ...authEnvironment, STAGING_NEON_AUTH_URL: authUrl.replace('/neondb/auth', '/other/auth')
    }), /reviewed isolated Neon Auth endpoint/);
    assert.throws(() => validateStagingAuthConfig({
        ...authEnvironment, STAGING_NEON_AUTH_URL: authUrl.replace('https://', 'http://')
    }), /reviewed isolated Neon Auth endpoint/);
    assert.throws(() => validateStagingAuthConfig({
        ...authEnvironment, STAGING_AUTH_TRUSTED_CHROME_ORIGIN: 'https://example.test'
    }), /reviewed isolated Neon Auth endpoint/);
    assert.throws(() => validateStagingAuthAccounts({
        ...authEnvironment, STAGING_AUTH_USER_B_EMAIL: 'ACCOUNT-A@example.test'
    }), /two distinct synthetic Auth accounts/);
});

test('Auth cookie transport scopes cookies by name, domain, and path', async () => {
    const requests = [];
    const fetchImpl = async (input, init = {}) => {
        const url = new URL(input instanceof Request ? input.url : input.toString());
        const headers = new Headers(init.headers);
        requests.push({ url, headers });
        const responseHeaders = new Headers();
        if (requests.length === 1) {
            responseHeaders.append('set-cookie', 'session=root; Path=/neondb; Secure; HttpOnly; SameSite=Lax');
            responseHeaders.append('set-cookie', 'session=auth; Path=/neondb/auth; Secure; HttpOnly; SameSite=Lax');
            responseHeaders.append('set-cookie', 'empty=; Path=/neondb/auth; Max-Age=60; Secure');
        } else if (requests.length === 2) {
            responseHeaders.append('set-cookie', 'session=; Path=/neondb/auth; Max-Age=0; Secure');
        }
        return new Response('{}', { status: 200, headers: responseHeaders });
    };
    const authFetch = createAuthCookieFetch({
        authOrigin, trustedOrigin, fetchImpl
    });
    await authFetch(authUrl + '/sign-in/email', { method: 'POST' });
    await authFetch(authUrl + '/get-session');
    assert.equal(requests[1].headers.get('cookie'), 'session=auth; empty=; session=root');
    assert.equal(requests[1].headers.get('origin'), trustedOrigin);
    assert.equal(requests[1].init, undefined);
    await authFetch(authUrl + '/get-session');
    assert.equal(requests[2].headers.get('cookie'), 'empty=; session=root');

    await authFetch(authOrigin + '/outside/auth');
    assert.equal(requests[3].headers.get('cookie'), null);
    assert.equal(requests[3].headers.get('origin'), trustedOrigin);
    await assert.rejects(authFetch('https://example.test/neondb/auth/get-session'),
        /unexpected origin/);
    authFetch.clearCookies();
    await authFetch(authUrl + '/get-session');
    assert.equal(requests[4].headers.get('cookie'), null);
});

test('Auth transport refuses unsafe combined Set-Cookie headers and cross-origin fetches', async () => {
    let calls = 0;
    const authFetch = createAuthCookieFetch({
        authOrigin,
        trustedOrigin,
        fetchImpl: async () => {
            calls++;
            return {
                headers: {
                    getSetCookie: undefined,
                    get: name => name === 'set-cookie' ? 'one=1, two=2' : null
                }
            };
        }
    });
    await assert.rejects(authFetch(authUrl + '/sign-in/email'), /cannot safely split/);
    await assert.rejects(authFetch('https://other.example/neondb/auth/sign-in/email'),
        /unexpected origin/);
    assert.equal(calls, 1);
});

test('JWT claim validation binds the token to the signed-in user and live staging Auth origin', () => {
    const user = { id: 'synthetic-user-a', email: 'account-a@example.test' };
    const token = jwt(claims());
    assert.equal(validateStagingAccessToken(token, user, authOrigin), token);
    assert.throws(() => validateStagingAccessToken(jwt(claims({ iss: 'https://other.example' })), user, authOrigin),
        /current verified token/);
    assert.throws(() => validateStagingAccessToken(jwt(claims({ aud: 'https://other.example' })), user, authOrigin),
        /current verified token/);
    assert.throws(() => validateStagingAccessToken(jwt(claims({ sub: 'other-user' })), user, authOrigin),
        /current verified token/);
    assert.throws(() => validateStagingAccessToken(jwt(claims({ exp: 1 })), user, authOrigin),
        /current verified token/);
    assert.throws(() => validateStagingAccessToken(jwt(claims({ emailVerified: false })), user, authOrigin),
        /current verified token/);
    assert.throws(() => validateStagingAccessToken(jwt(claims({ banned: true })), user, authOrigin),
        /current verified token/);
});

function mockAuthDependencies(options = {}) {
    const user = { id: 'synthetic-user-a', email: authEnvironment.STAGING_AUTH_USER_A_EMAIL,
        emailVerified: true };
    const session = {
        user,
        session: {
            expiresAt: new Date(Date.now() + 60000).toISOString(),
            token: jwt(claims())
        }
    };
    let active = false;
    let signOutCalls = 0;
    const requests = [];
    return {
        requests,
        get signOutCalls() { return signOutCalls; },
        get active() { return active; },
        BetterAuthVanillaAdapter() { return {}; },
        createAuthClient(baseUrl, config) {
            assert.equal(baseUrl, authUrl);
            assert.ok(config.adapter);
            return {
                signIn: {
                    email: async () => {
                        await globalThis.fetch(authUrl + '/sign-in/email', { method: 'POST' });
                        if (options.signInError) {
                            active = options.signInErrorWithSession === true;
                            return { error: { status: 401 } };
                        }
                        active = true;
                        return { data: { user } };
                    }
                },
                getSession: async () => {
                    await globalThis.fetch(authUrl + '/get-session');
                    if (active || options.staleAfterSignOut) return { data: session };
                    return { data: { user: null, session: null } };
                },
                signOut: async () => {
                    signOutCalls++;
                    await globalThis.fetch(authUrl + '/sign-out', { method: 'POST' });
                    if (options.failSignOut) return { error: { status: 500 } };
                    active = false;
                    return { data: null };
                }
            };
        },
        fetchImpl: async (input, init = {}) => {
            const url = new URL(input instanceof Request ? input.url : input.toString());
            const headers = new Headers(init.headers);
            requests.push({ url, headers });
            const responseHeaders = new Headers();
            if (url.pathname.endsWith('/sign-in/email')) {
                responseHeaders.append('set-cookie', 'session=opaque; Path=/neondb/auth; Secure; HttpOnly');
            }
            if (url.pathname.endsWith('/sign-out')) {
                responseHeaders.append('set-cookie', 'session=; Path=/neondb/auth; Max-Age=0; Secure');
            }
            return new Response('{}', { status: 200, headers: responseHeaders });
        }
    };
}

test('withStagingAuth closes a session even when sign-in reports an error', async () => {
    const originalFetch = globalThis.fetch;
    for (const signInErrorWithSession of [false, true]) {
        const dependencies = mockAuthDependencies({ signInError: true, signInErrorWithSession });
        globalThis.fetch = dependencies.fetchImpl;
        await assert.rejects(withStagingAuth(async () => 'unused',
            authEnvironment, 'A', dependencies), /sign-in failed/);
        assert.equal(dependencies.signOutCalls, 1);
        assert.equal(dependencies.active, false);
    }
    globalThis.fetch = originalFetch;
});
test('withStagingAuth sends the trusted extension Origin, validates JWT, and confirms sign-out', async () => {
    const originalFetch = globalThis.fetch;
    const dependencies = mockAuthDependencies();
    globalThis.fetch = dependencies.fetchImpl;
    try {
        const result = await withStagingAuth(async getAccessToken => {
            const token = await getAccessToken();
            assert.equal(validateStagingAccessToken(token, {
                id: 'synthetic-user-a', email: 'account-a@example.test'
            }, authOrigin), token);
            return 'callback-result';
        }, authEnvironment, 'A', dependencies);
        assert.equal(result, 'callback-result');
        assert.equal(dependencies.signOutCalls, 1);
        assert.equal(dependencies.active, false);
        assert.equal(dependencies.requests[1].headers.get('cookie'), 'session=opaque');
        assert.equal(dependencies.requests[0].headers.get('origin'), trustedOrigin);
        assert.equal(dependencies.requests[1].headers.get('origin'), trustedOrigin);
        assert.equal(globalThis.fetch, dependencies.fetchImpl);
    } finally {
        globalThis.fetch = originalFetch;
    }
});

test('withStagingAuth cleans up after callback failure and reports an unconfirmed session close', async () => {
    const originalFetch = globalThis.fetch;
    const dependencies = mockAuthDependencies();
    globalThis.fetch = dependencies.fetchImpl;
    try {
        await assert.rejects(withStagingAuth(async () => {
            throw new Error('synthetic callback failure');
        }, authEnvironment, 'A', dependencies), /synthetic callback failure/);
        assert.equal(dependencies.signOutCalls, 1);
        assert.equal(dependencies.active, false);

        const staleSession = mockAuthDependencies({ staleAfterSignOut: true });
        globalThis.fetch = staleSession.fetchImpl;
        await assert.rejects(withStagingAuth(async () => 'unused',
            authEnvironment, 'A', staleSession), /could not be closed safely/);
        assert.equal(staleSession.signOutCalls, 1);
    } finally {
        globalThis.fetch = originalFetch;
    }
});

test('two-account ownership checks require cross-account list, read, update, and delete isolation', async () => {
    const hidden = id => async () => {
        throw Object.assign(new Error('Analysis not found'), { status: 404, id });
    };
    const clientA = {
        listAnalyses: async () => [{ id: 'report-a' }],
        getAnalysis: hidden('report-b'),
        updateAnalysis: hidden('report-b'),
        deleteAnalysis: hidden('report-b')
    };
    const clientB = {
        listAnalyses: async () => [{ id: 'report-b' }],
        getAnalysis: hidden('report-a'),
        updateAnalysis: hidden('report-a'),
        deleteAnalysis: hidden('report-a')
    };
    assert.equal(await verifyReportPairIsolation(clientA, clientB, 'report-a', 'report-b'), 'passed');

    const leakingClient = {
        ...clientB,
        listAnalyses: async () => [{ id: 'report-a' }, { id: 'report-b' }]
    };
    await assert.rejects(verifyReportIsolation(leakingClient, 'report-a'),
        /Another Auth user can list this saved report/);
    await assert.rejects(verifyReportPairIsolation(clientA, clientB, 'report-a', 'report-a'),
        /Two distinct account-owned reports/);
});

test('write verifier keeps targets pinned to loopback or the approved staging origin', async () => {
    await assert.rejects(verifyTarget('https://example.test', {
        environment: 'staging', expectedSha: 'a'.repeat(40), allowWrites: true
    }), /Target must be loopback/);
    await assert.rejects(verifyTarget('http://127.0.0.1:8000/path', {
        environment: 'demo', expectedSha: 'a'.repeat(40), allowWrites: true
    }), /plain HTTP\(S\) origin/);
    await assert.rejects(verifyTarget('http://127.0.0.1:8000', {
        environment: 'demo', expectedSha: 'a'.repeat(40), allowWrites: false
    }), /Explicit write permission/);
});


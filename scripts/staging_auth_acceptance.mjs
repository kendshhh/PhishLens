import { createAuthClient, BetterAuthVanillaAdapter } from '../extension/vendor/neon/sdk.mjs';
import { createNeonAccounts } from '../extension/js/neon-accounts.js';
import { verifyCrud, verifyTarget } from './verify_crud.mjs';

function required(name) {
    const value = process.env[name];
    if (typeof value !== 'string' || !value.trim()) throw new Error(`Missing required staging setting: ${name}`);
    return value.trim();
}

function authConfiguration() {
    const authUrl = new URL(required('STAGING_AUTH_URL'));
    const database = required('STAGING_AUTH_DATABASE');
    const expectedNeonHost = required('STAGING_NEON_EXPECTED_HOST').toLowerCase();
    const expectedAuthHost = expectedNeonHost.replace(/^([^.]+)\./, '$1.neonauth.');
    if (authUrl.protocol !== 'https:' || authUrl.username || authUrl.password || authUrl.search || authUrl.hash ||
        authUrl.pathname !== `/${encodeURIComponent(database)}/auth` ||
        !/^ep-[a-z0-9-]+\.(?:[a-z0-9-]+\.)?[a-z0-9-]+\.aws\.neon\.tech$/.test(expectedNeonHost) ||
        authUrl.port || authUrl.hostname !== expectedAuthHost) {
        throw new Error('Staging Auth URL, database, and expected Neon host do not match');
    }
    return { authUrl };
}

function createScopedFetch(authUrl, apiUrl) {
    const nativeFetch = globalThis.fetch.bind(globalThis);
    const cookies = new Map();
    const authBasePath = authUrl.pathname.replace(/\/+$/, '');
    const apiOrigin = apiUrl.origin;

    function saveCookies(response) {
        const lines = typeof response.headers.getSetCookie === 'function'
            ? response.headers.getSetCookie()
            : [];
        for (const line of lines) {
            const [pair, ...attributes] = line.split(';');
            const separator = pair.indexOf('=');
            if (separator < 1) continue;
            const name = pair.slice(0, separator).trim();
            const expired = attributes.some(attribute => {
                const match = /^\s*max-age\s*=\s*(-?\d+)\s*$/i.exec(attribute);
                return match && Number(match[1]) <= 0;
            }) ||
                attributes.some(attribute => {
                    const match = /^\s*expires\s*=\s*(.+)\s*$/i.exec(attribute);
                    return match && Date.parse(match[1]) <= Date.now();
                });
            if (expired) cookies.delete(name);
            else cookies.set(name, pair.trim());
        }
    }

    return async (input, init = {}) => {
        const requestUrl = input instanceof Request
            ? new URL(input.url)
            : new URL(String(input), authUrl);
        const isAuth = requestUrl.origin === authUrl.origin &&
            (requestUrl.pathname === authBasePath || requestUrl.pathname.startsWith(`${authBasePath}/`));
        const isApi = requestUrl.origin === apiOrigin &&
            (requestUrl.pathname === '/version' || requestUrl.pathname === '/ready' ||
                requestUrl.pathname === '/api/analyses' || requestUrl.pathname.startsWith('/api/analyses/'));
        if (!isAuth && !isApi) throw new Error('Staging acceptance attempted an unapproved request target');

        const headers = new Headers(input instanceof Request ? input.headers : undefined);
        new Headers(init.headers).forEach((value, name) => headers.set(name, value));
        if (isAuth && cookies.size) headers.set('Cookie', [...cookies.values()].join('; '));
        else headers.delete('Cookie');

        const response = await nativeFetch(input, { ...init, headers, redirect: 'error' });
        if (isAuth) saveCookies(response);
        return response;
    };
}

function redact(message, values) {
    let safe = String(message);
    for (const value of values) {
        if (typeof value === 'string' && value) safe = safe.split(value).join('[redacted]');
    }
    return safe.replace(/\bBearer\s+[^\s,;]+/gi, 'Bearer [redacted]');
}

async function main() {
    const baseUrl = required('STAGING_BASE_URL');
    const expectedSha = required('STAGING_EXPECTED_SHA');
    const email = required('STAGING_AUTH_EMAIL');
    const password = required('STAGING_AUTH_PASSWORD');
    const { authUrl } = authConfiguration();
    const apiUrl = new URL(baseUrl);
    if (apiUrl.origin !== 'https://phishlens-staging.onrender.com' || apiUrl.pathname !== '/' ||
        apiUrl.search || apiUrl.hash || apiUrl.username || apiUrl.password) {
        throw new Error('Authenticated acceptance is restricted to the approved staging API origin');
    }

    globalThis.fetch = createScopedFetch(authUrl, apiUrl);
    await verifyTarget(baseUrl, { environment: 'staging', expectedSha, allowWrites: true });

    const sdk = createAuthClient(authUrl.href, {
        adapter: BetterAuthVanillaAdapter({ fetchOptions: {
            credentials: 'include', redirect: 'error', timeout: 10000, retry: 0
        } })
    });
    const accounts = createNeonAccounts(sdk);
    let signInAttempted = false;
    let accessToken;
    let result;
    let failure;
    try {
        signInAttempted = true;
        const session = await accounts.signIn({ email, password });
        if (!session?.user?.id) throw new Error('Staging test account sign-in could not be confirmed');
        accessToken = await accounts.getAccessToken(session.user.id);
        if (!accessToken) throw new Error('Staging test account did not provide a valid session JWT');
        result = await verifyCrud(baseUrl, {
            environment: 'staging', expectedSha, allowWrites: true, accessToken
        });
    } catch (error) {
        failure = error;
    } finally {
        if (signInAttempted) {
            try {
                await accounts.signOut();
            } catch {
                failure = new Error('Could not revoke the staging acceptance session');
            }
        }
    }

    if (failure) throw new Error(redact(failure.message, [email, password, accessToken]));
    console.log(JSON.stringify(result, null, 2));
}

main().catch(error => {
    console.error(error instanceof Error ? error.message : 'Authenticated staging acceptance failed');
    process.exitCode = 1;
});

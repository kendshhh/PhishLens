const STAGING_BASE_URL = 'https://phishlens-staging.onrender.com';
const STAGING_NEON_AUTH_HOST = 'ep-winter-wind-a1y2r1db.neonauth.ap-southeast-1.aws.neon.tech';
const STAGING_CHROME_ORIGIN = /^chrome-extension:\/\/[a-p]{32}$/;
const DEFAULT_AUTH_DATABASE = 'neondb';

function endpointSettings(environment = process.env) {
    const rawUrl = environment.STAGING_NEON_AUTH_URL ??
        environment.STAGING_AUTH_URL ??
        environment.PHISHLENS_STAGING_AUTH_URL ??
        environment.authUrl;
    const rawDatabase = environment.PHISHLENS_STAGING_AUTH_DATABASE ??
        environment.STAGING_AUTH_DATABASE ??
        environment.database;
    const database = typeof rawDatabase === 'string' ? rawDatabase.trim() : '';
    const trustedOrigin = environment.STAGING_AUTH_TRUSTED_CHROME_ORIGIN ??
        environment.trustedOrigin;
    if (!/^[a-z0-9_]+$/.test(database)) {
        throw new Error('Hosted staging requires PHISHLENS_STAGING_AUTH_DATABASE to identify the Auth database.');
    }
    let url;
    try {
        url = new URL(rawUrl);
    } catch {
        throw new Error('Hosted staging requires a valid STAGING_NEON_AUTH_URL.');
    }
    if (url.protocol !== 'https:' || url.username || url.password || url.port ||
        url.search || url.hash || url.pathname !== '/' + database + '/auth' ||
        url.hostname !== STAGING_NEON_AUTH_HOST || database !== DEFAULT_AUTH_DATABASE ||
        !STAGING_CHROME_ORIGIN.test(trustedOrigin || '')) {
        throw new Error('STAGING_NEON_AUTH_URL must be the reviewed isolated Neon Auth endpoint over HTTPS with the trusted extension origin.');
    }
    return { url, database, trustedOrigin };
}

// Kept as a URL-returning validator for callers that only need endpoint validation.
export function validateStagingAuthConfig(environment = process.env) {
    return endpointSettings(environment).url;
}

function accountConfig(environment, account, endpoint = endpointSettings(environment)) {
    if (!['A', 'B'].includes(account)) {
        throw new Error('Hosted staging supports only synthetic Auth accounts A and B.');
    }
    const prefix = 'STAGING_AUTH_USER_' + account;
    const legacyEmail = account === 'A' ? environment.STAGING_AUTH_TEST_EMAIL : undefined;
    const legacyPassword = account === 'A' ? environment.STAGING_AUTH_TEST_PASSWORD : undefined;
    const email = environment[prefix + '_EMAIL'] ?? legacyEmail;
    const password = environment[prefix + '_PASSWORD'] ?? legacyPassword;
    if (typeof email !== 'string' || !email.trim() ||
        typeof password !== 'string' || !password) {
        throw new Error('Hosted staging requires the protected ' + prefix + '_EMAIL and ' + prefix + '_PASSWORD secrets.');
    }
    return { ...endpoint, email: email.trim(), password, account };
}

export function validateStagingAuthAccounts(environment = process.env) {
    const endpoint = endpointSettings(environment);
    const A = accountConfig(environment, 'A', endpoint);
    const B = accountConfig(environment, 'B', endpoint);
    if (A.email.toLowerCase() === B.email.toLowerCase()) {
        throw new Error('Hosted staging isolation checks require two distinct synthetic Auth accounts.');
    }
    return { A, B };
}

function cookiePathMatches(requestPath, cookiePath) {
    if (!cookiePath || !cookiePath.startsWith('/')) return false;
    if (requestPath === cookiePath) return true;
    if (!requestPath.startsWith(cookiePath)) return false;
    return cookiePath.endsWith('/') || requestPath[cookiePath.length] === '/';
}

function defaultCookiePath(requestPath) {
    if (!requestPath || requestPath[0] !== '/' || requestPath === '/') return '/';
    const lastSlash = requestPath.lastIndexOf('/');
    return lastSlash <= 0 ? '/' : requestPath.slice(0, lastSlash);
}

function domainMatches(hostname, domain) {
    return hostname === domain || hostname.endsWith('.' + domain);
}

function createCookieJar() {
    const cookies = new Map();
    let sequence = 0;

    function cookieKey(name, domain, path) {
        return domain + '\u0000' + path + '\u0000' + name;
    }

    function setCookieLines(headers) {
        if (typeof headers?.getSetCookie === 'function') {
            return headers.getSetCookie();
        }
        const combined = headers?.get?.('set-cookie');
        if (!combined) return [];
        if (/,\s*[^;,=\s]+\s*=/.test(combined)) {
            throw new Error('Staging Auth transport cannot safely split combined Set-Cookie headers.');
        }
        return [combined];
    }

    return {
        header(requestUrl) {
            const now = Date.now();
            for (const [key, cookie] of cookies) {
                if (cookie.expiresAt !== null && cookie.expiresAt <= now) cookies.delete(key);
            }
            return [...cookies.values()]
                .filter(cookie =>
                    domainMatches(requestUrl.hostname, cookie.domain) &&
                    cookiePathMatches(requestUrl.pathname, cookie.path) &&
                    (!cookie.secure || requestUrl.protocol === 'https:'))
                .sort((left, right) =>
                    right.path.length - left.path.length || left.sequence - right.sequence)
                .map(cookie => cookie.name + '=' + cookie.value)
                .join('; ');
        },
        absorb(headers, requestUrl) {
            for (const line of setCookieLines(headers)) {
                if (typeof line !== 'string') continue;
                const parts = line.split(';');
                const pair = (parts.shift() || '').trim();
                const splitAt = pair.indexOf('=');
                if (splitAt <= 0) continue;
                const name = pair.slice(0, splitAt).trim();
                const value = pair.slice(splitAt + 1).trim();
                if (!/^[!#$%&'*+.^_\x60|~0-9A-Za-z-]+$/.test(name)) continue;

                const attributes = new Map();
                for (const part of parts) {
                    const index = part.indexOf('=');
                    const key = (index < 0 ? part : part.slice(0, index)).trim().toLowerCase();
                    const attributeValue = index < 0 ? '' : part.slice(index + 1).trim();
                    attributes.set(key, attributeValue);
                }
                const domainAttribute = attributes.get('domain');
                const domain = domainAttribute
                    ? domainAttribute.replace(/^\./, '').toLowerCase()
                    : requestUrl.hostname.toLowerCase();
                if (domainAttribute && (!domain || !domainMatches(requestUrl.hostname.toLowerCase(), domain))) {
                    continue;
                }
                const pathAttribute = attributes.get('path');
                const path = pathAttribute && pathAttribute.startsWith('/')
                    ? pathAttribute
                    : defaultCookiePath(requestUrl.pathname);
                const key = cookieKey(name, domain, path);

                const maxAgeText = attributes.get('max-age');
                const maxAge = typeof maxAgeText === 'string' && /^-?\d+$/.test(maxAgeText)
                    ? Number(maxAgeText)
                    : null;
                const expires = Date.parse(attributes.get('expires') || '');
                const expiresAt = maxAge !== null
                    ? Date.now() + maxAge * 1000
                    : Number.isFinite(expires) ? expires : null;
                if ((maxAge !== null && maxAge <= 0) ||
                    (maxAge === null && expiresAt !== null && expiresAt <= Date.now())) {
                    cookies.delete(key);
                    continue;
                }
                cookies.set(key, {
                    name, value, domain, path, expiresAt,
                    secure: attributes.has('secure'), sequence: sequence++
                });
            }
        },
        clear() {
            cookies.clear();
        }
    };
}

export function createAuthCookieFetch({
    authOrigin,
    authPath = '/' + DEFAULT_AUTH_DATABASE + '/auth',
    trustedOrigin,
    fetchImpl = globalThis.fetch
}) {
    let target;
    try {
        target = new URL(authOrigin);
    } catch {
        throw new Error('Staging Auth transport configuration is invalid.');
    }
    if (target.protocol !== 'https:' || target.origin !== authOrigin ||
        target.hostname !== STAGING_NEON_AUTH_HOST ||
        !/^\/[a-z0-9_]+\/auth$/.test(authPath) ||
        !STAGING_CHROME_ORIGIN.test(trustedOrigin || '') || typeof fetchImpl !== 'function') {
        throw new Error('Staging Auth transport configuration is invalid.');
    }
    const jar = createCookieJar();
    const inAuthPath = pathname =>
        pathname === authPath || pathname.startsWith(authPath + '/');
    const wrapped = async (input, init = {}) => {
        let requestUrl;
        try {
            requestUrl = input instanceof Request
                ? new URL(input.url)
                : input instanceof URL ? input : new URL(String(input));
        } catch {
            throw new Error('Staging Auth request URL is invalid.');
        }
        if (requestUrl.origin !== target.origin) {
            throw new Error('Staging Auth attempted an unexpected origin.');
        }

        const headers = new Headers(input instanceof Request ? input.headers : undefined);
        new Headers(init.headers || {}).forEach((value, name) => headers.set(name, value));
        headers.set('Origin', trustedOrigin);
        const cookie = inAuthPath(requestUrl.pathname) ? jar.header(requestUrl) : '';
        if (cookie) headers.set('Cookie', cookie);
        else headers.delete('Cookie');

        const response = await fetchImpl(input, { ...init, headers, redirect: 'error' });
        if (inAuthPath(requestUrl.pathname)) jar.absorb(response.headers, requestUrl);
        return response;
    };
    wrapped.clearCookies = () => jar.clear();
    return wrapped;
}

export function validateStagingAccessToken(token, user, authOrigin, now = Date.now()) {
    if (typeof token !== 'string') throw new Error('Neon Auth did not return a staging access token.');
    const parts = token.split('.');
    if (parts.length !== 3 || !parts.every(part => /^[A-Za-z0-9_-]+$/.test(part))) {
        throw new Error('Neon Auth did not return a JWT access token.');
    }
    let claims;
    try {
        claims = JSON.parse(Buffer.from(parts[1], 'base64url').toString('utf8'));
    } catch {
        throw new Error('Neon Auth returned an unreadable access token.');
    }
    const audienceMatches = claims.aud === authOrigin ||
        (Array.isArray(claims.aud) && claims.aud.includes(authOrigin));
    if (typeof claims.sub !== 'string' || !claims.sub ||
        claims.iss !== authOrigin || !audienceMatches ||
        claims.emailVerified !== true || claims.banned !== false ||
        typeof claims.email !== 'string' || !claims.email ||
        (user && (claims.sub !== user.id ||
            typeof user.email !== 'string' ||
            claims.email.toLowerCase() !== user.email.toLowerCase())) ||
        !Number.isFinite(claims.exp) || claims.exp * 1000 <= now ||
        (Number.isFinite(claims.nbf) && claims.nbf * 1000 > now)) {
        throw new Error('Neon Auth did not return a current verified token for the synthetic staging account.');
    }
    return token;
}

function forceFetchOptions() {
    return { fetchOptions: { headers: { 'X-Force-Fetch': 'true' } } };
}

async function withAuthFetch(authFetch, action) {
    const previousFetch = globalThis.fetch;
    globalThis.fetch = authFetch;
    try {
        return await action();
    } finally {
        globalThis.fetch = previousFetch;
    }
}

export async function withStagingAuth(callback, environment = process.env, account = 'A', dependencies = {}) {
    if (typeof callback !== 'function') throw new TypeError('A staging Auth callback is required.');
    if (environment.STAGING_BASE_URL !== STAGING_BASE_URL) {
        throw new Error('Authenticated staging sign-in is limited to the approved staging origin.');
    }
    const config = accountConfig(environment, account);
    const authFetch = createAuthCookieFetch({
        authOrigin: config.url.origin,
        authPath: config.url.pathname,
        trustedOrigin: config.trustedOrigin,
        fetchImpl: globalThis.fetch.bind(globalThis)
    });
    const modules = dependencies.createAuthClient && dependencies.BetterAuthVanillaAdapter
        ? dependencies
        : await import('../extension/vendor/neon/sdk.mjs');
    const { createAuthClient, BetterAuthVanillaAdapter } = modules;
    let sdk;
    let signInAttempted = false;
    let primaryError;
    let cleanupError;
    let result;
    try {
        const signIn = await withAuthFetch(authFetch, async () => {
            sdk = createAuthClient(config.url.href, {
                adapter: BetterAuthVanillaAdapter({ fetchOptions: {
                    credentials: 'include', redirect: 'error', timeout: 10000, retry: 0
                } })
            });
            signInAttempted = true;
            return sdk.signIn.email({
                email: config.email, password: config.password, rememberMe: false
            });
        });
        if (signIn?.error || !signIn?.data?.user) {
            const error = new Error('Neon Auth sign-in failed for synthetic staging account ' + account + '.');
            if (Number.isInteger(signIn?.error?.status)) error.status = signIn.error.status;
            throw error;
        }


        const current = await withAuthFetch(authFetch, () =>
            sdk.getSession(forceFetchOptions()));
        const session = current?.data;
        if (current?.error || !session?.user || !session?.session) {
            const error = new Error('Neon Auth could not confirm the synthetic staging session.');
            if (Number.isInteger(current?.error?.status)) error.status = current.error.status;
            throw error;
        }
        if (session.user.id !== signIn.data.user.id ||
            typeof session.user.email !== 'string' ||
            session.user.email.toLowerCase() !== config.email.toLowerCase() ||
            session.user.emailVerified !== true) {
            throw new Error('Neon Auth returned a different or unverified staging account.');
        }
        const expiresAt = Date.parse(session.session.expiresAt);
        if (!Number.isFinite(expiresAt) || expiresAt <= Date.now()) {
            throw new Error('Neon Auth returned an expired staging session.');
        }
        const token = validateStagingAccessToken(session.session.token, session.user, config.url.origin);
        result = await callback(async () => token);
    } catch (error) {
        primaryError = error;
    }

    if (signInAttempted) {
        try {
            const signedOut = await withAuthFetch(authFetch, () => sdk.signOut());
            if (signedOut?.error) throw new Error('Auth sign-out was rejected.');
            const current = await withAuthFetch(authFetch, () =>
                sdk.getSession(forceFetchOptions()));
            const remaining = current?.data;
            const status = Number(current?.error?.status);
            if ((current?.error && ![401, 404].includes(status)) ||
                remaining?.session || remaining?.user) {
                throw new Error('Auth sign-out did not clear the synthetic staging session.');
            }
        } catch {
            cleanupError = new Error('The synthetic staging Auth session could not be closed safely.');
        }
    }
    authFetch.clearCookies();

    if (primaryError && cleanupError) {
        throw new AggregateError([primaryError, cleanupError],
            'Authenticated staging verification and Auth session cleanup both failed.');
    }
    if (primaryError) throw primaryError;
    if (cleanupError) throw cleanupError;
    return result;
}

export const stagingAuthDefaults = Object.freeze({
    authDatabase: DEFAULT_AUTH_DATABASE,
    stagingBaseUrl: STAGING_BASE_URL
});


const NEON_AUTH_SUFFIX = '.aws.neon.tech';

export function validateStagingAuthConfig(environment = process.env, account = 'A') {
    if (!['A', 'B'].includes(account)) {
        throw new Error('Hosted staging supports only synthetic Auth accounts A and B.');
    }
    const rawUrl = environment.STAGING_NEON_AUTH_URL;
    const authDatabase = environment.PHISHLENS_STAGING_AUTH_DATABASE;
    const authPath = typeof authDatabase === 'string' ? '/' + authDatabase + '/auth' : '';
    const prefix = `STAGING_AUTH_USER_${account}`;
    const email = environment[`${prefix}_EMAIL`];
    const password = environment[`${prefix}_PASSWORD`];
    let url;
    try {
        url = new URL(rawUrl);
    } catch {
        throw new Error('Hosted staging requires a valid STAGING_NEON_AUTH_URL.');
    }
    if (typeof authDatabase !== 'string' || !/^[a-z0-9_]+$/.test(authDatabase) ||
        url.protocol !== 'https:' || url.username || url.password || url.search || url.hash ||
        url.pathname !== authPath || !url.hostname.includes('.neonauth.') ||
        !url.hostname.endsWith(NEON_AUTH_SUFFIX)) {
        throw new Error('STAGING_NEON_AUTH_URL must be the HTTPS Neon Auth URL matching PHISHLENS_STAGING_AUTH_DATABASE.');
    }
    if (typeof email !== 'string' || !email.trim() ||
        typeof password !== 'string' || !password) {
        throw new Error(`Hosted staging requires the protected ${prefix}_EMAIL and ${prefix}_PASSWORD secrets.`);
    }
    return { url, email: email.trim(), password, account };
}

export function validateStagingAuthAccounts(environment = process.env) {
    const accountA = validateStagingAuthConfig(environment, 'A');
    const accountB = validateStagingAuthConfig(environment, 'B');
    if (accountA.email.toLowerCase() === accountB.email.toLowerCase()) {
        throw new Error('Hosted staging isolation checks require two distinct synthetic Auth accounts.');
    }
    return { A: accountA, B: accountB };
}

function createCookieJar() {
    const cookies = new Map();

    function pathMatches(requestPath, cookiePath) {
        const normalized = cookiePath || '/';
        return requestPath === normalized ||
            requestPath.startsWith(normalized.endsWith('/') ? normalized : normalized + '/');
    }

    return {
        header(requestPath) {
            const now = Date.now();
            for (const [name, cookie] of cookies) {
                if (cookie.expiresAt !== null && cookie.expiresAt <= now) cookies.delete(name);
            }
            return [...cookies]
                .filter(([, cookie]) => pathMatches(requestPath, cookie.path))
                .map(([name, cookie]) => name + '=' + cookie.value)
                .join('; ');
        },
        absorb(headers, requestUrl) {
            const setCookies = typeof headers.getSetCookie === 'function'
                ? headers.getSetCookie()
                : (headers.get('set-cookie') ? [headers.get('set-cookie')] : []);
            for (const line of setCookies) {
                if (typeof line !== 'string') continue;
                const parts = line.split(';');
                const pair = parts.shift()?.trim() || '';
                const splitAt = pair.indexOf('=');
                if (splitAt <= 0) continue;
                const name = pair.slice(0, splitAt).trim();
                const value = pair.slice(splitAt + 1).trim();
                if (!/^[!#$%&'*+.^_`|~0-9A-Za-z-]+$/.test(name)) continue;

                const attributes = new Map(parts.map(part => {
                    const index = part.indexOf('=');
                    const key = (index < 0 ? part : part.slice(0, index)).trim().toLowerCase();
                    const attributeValue = index < 0 ? '' : part.slice(index + 1).trim();
                    return [key, attributeValue];
                }));
                const domain = (attributes.get('domain') || '').replace(/^\./, '').toLowerCase();
                if (domain && requestUrl.hostname !== domain &&
                    !requestUrl.hostname.endsWith('.' + domain)) continue;

                const maxAge = Number(attributes.get('max-age'));
                const expires = Date.parse(attributes.get('expires') || '');
                if ((Number.isFinite(maxAge) && maxAge <= 0) ||
                    (!Number.isFinite(maxAge) && Number.isFinite(expires) && expires <= Date.now())) {
                    cookies.delete(name);
                    continue;
                }
                const defaultPath = requestUrl.pathname.slice(0, requestUrl.pathname.lastIndexOf('/') + 1) || '/';
                const cookiePath = attributes.get('path') || defaultPath;
                const expiresAt = Number.isFinite(maxAge)
                    ? Date.now() + maxAge * 1000
                    : Number.isFinite(expires) ? expires : null;
                cookies.set(name, { value, path: cookiePath, expiresAt });
            }
        }
    };
}

function readJwtClaims(token, user, authOrigin) {
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
    if (claims.sub !== user.id || claims.iss !== authOrigin || !audienceMatches ||
        claims.emailVerified !== true || claims.banned !== false ||
        typeof claims.email !== 'string' || claims.email.toLowerCase() !== user.email.toLowerCase() ||
        !Number.isFinite(claims.exp) || claims.exp * 1000 <= Date.now()) {
        throw new Error('Neon Auth did not return a current verified token for the synthetic staging account.');
    }
    return token;
}

export async function withStagingAuth(callback, environment = process.env, account = 'A') {
    if (typeof callback !== 'function') throw new TypeError('A staging Auth callback is required.');
    if (environment.STAGING_BASE_URL !== 'https://phishlens-staging.onrender.com') {
        throw new Error('Authenticated staging sign-in is limited to the approved staging origin.');
    }
    const { url, email, password } = validateStagingAuthConfig(environment, account);
    const { createAuthClient, BetterAuthVanillaAdapter } =
        await import('../extension/vendor/neon/sdk.mjs');
    const sdk = createAuthClient(url.href, {
        adapter: BetterAuthVanillaAdapter({ fetchOptions: {
            credentials: 'include', redirect: 'error', timeout: 10000, retry: 0
        } })
    });
    const authOrigin = url.origin;
    const authPath = url.pathname;
    const jar = createCookieJar();
    const originalFetch = globalThis.fetch;
    const nativeFetch = originalFetch.bind(globalThis);
    const authFetch = async (input, init = {}) => {
        const requestUrl = input instanceof Request
            ? new URL(input.url)
            : input instanceof URL ? input : new URL(String(input));
        if (requestUrl.origin !== authOrigin || !requestUrl.pathname.startsWith(authPath + '/')) {
            throw new Error('Staging Auth request escaped the configured Neon Auth endpoint.');
        }
        const headers = new Headers(init.headers || (input instanceof Request ? input.headers : undefined));
        const cookie = jar.header(requestUrl.pathname);
        if (cookie && !headers.has('cookie')) headers.set('cookie', cookie);
        if (!headers.has('origin')) headers.set('origin', environment.STAGING_BASE_URL);
        const response = await nativeFetch(input, { ...init, headers, redirect: 'error' });
        jar.absorb(response.headers, requestUrl);
        return response;
    };
    const withAuthFetch = async action => {
        globalThis.fetch = authFetch;
        try {
            return await action();
        } finally {
            globalThis.fetch = originalFetch;
        }
    };

    let signedIn = false;
    let primaryError;
    let signOutError;
    let result;
    try {
        const signIn = await withAuthFetch(() => sdk.signIn.email({ email, password, rememberMe: false }));
        if (signIn?.error || !signIn?.data?.user) {
            const error = new Error(`Neon Auth sign-in failed for synthetic staging account ${account}.`);
            if (Number.isInteger(signIn?.error?.status)) error.status = signIn.error.status;
            throw error;
        }
        signedIn = true;
        const current = await withAuthFetch(() => sdk.getSession({
            fetchOptions: { headers: { 'X-Force-Fetch': 'true' } }
        }));
        const session = current?.data;
        if (current?.error || !session?.user || !session?.session) {
            const error = new Error('Neon Auth could not confirm the synthetic staging session.');
            if (Number.isInteger(current?.error?.status)) error.status = current.error.status;
            throw error;
        }
        if (session.user.id !== signIn.data.user.id ||
            session.user.email?.toLowerCase() !== email.toLowerCase() ||
            session.user.emailVerified !== true) {
            throw new Error('Neon Auth returned a different or unverified staging account.');
        }
        const expiresAt = Date.parse(session.session.expiresAt);
        if (!Number.isFinite(expiresAt) || expiresAt <= Date.now()) {
            throw new Error('Neon Auth returned an expired staging session.');
        }
        const token = readJwtClaims(session.session.token, session.user, authOrigin);
        result = await callback(async () => token);
    } catch (error) {
        primaryError = error;
    }

    if (signedIn) {
        try {
            const signedOut = await withAuthFetch(() => sdk.signOut());
            if (signedOut?.error) throw new Error('Auth sign-out was rejected.');
        } catch {
            signOutError = new Error('The synthetic staging Auth session could not be closed safely.');
        }
    }
    if (primaryError && signOutError) {
        throw new AggregateError([primaryError, signOutError],
            'Authenticated staging verification and Auth session cleanup both failed.');
    }
    if (primaryError) throw primaryError;
    if (signOutError) throw signOutError;
    return result;
}

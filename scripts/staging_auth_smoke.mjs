import { pathToFileURL } from 'node:url';
import { verifyCrud } from './verify_crud.mjs';

function required(name) {
    const value = process.env[name]?.trim();
    if (!value) throw new Error(`Required staging setting is missing: ${name}`);
    return value;
}

function validatedAuthUrl(value, productionValue) {
    let url;
    try { url = new URL(value); }
    catch { throw new Error('Staging Neon Auth URL is invalid'); }
    if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash ||
        url.pathname !== '/neondb/auth' || !url.hostname.includes('.neonauth.')) {
        throw new Error('Staging Neon Auth URL is not a canonical Neon Auth endpoint');
    }
    let production;
    try { production = new URL(productionValue); }
    catch { throw new Error('Production Neon Auth URL is invalid'); }
    if (url.origin === production.origin) {
        throw new Error('Hosted staging must use a Neon Auth endpoint distinct from production');
    }
    return url.href.replace(/\/$/, '');
}

function jwtClaims(token) {
    if (typeof token !== 'string' || !/^[\w-]+\.[\w-]+\.[\w-]+$/.test(token)) {
        throw new Error('Neon Auth did not return an access token');
    }
    try {
        const payload = JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString('utf8'));
        if (typeof payload.sub !== 'string' || !Number.isFinite(payload.exp) ||
            payload.exp * 1000 <= Date.now()) {
            throw new Error();
        }
        return payload;
    } catch {
        throw new Error('Neon Auth returned an invalid or expired access token');
    }
}

function validatedStagingOrigin(value) {
    let url;
    try { url = new URL(value); }
    catch { throw new Error('Staging Auth origin is invalid'); }
    if (url.origin !== 'https://phishlens-staging.onrender.com' ||
        url.username || url.password || url.pathname !== '/' || url.search || url.hash) {
        throw new Error('Staging Auth smoke must use the approved staging origin');
    }
    return url.origin;
}

async function signIn(authUrl, origin, email, password) {
    const response = await fetch(`${authUrl}/sign-in/email`, {
        method: 'POST',
        headers: { 'content-type': 'application/json', accept: 'application/json', origin },
        body: JSON.stringify({ email, password }),
        redirect: 'error',
        signal: AbortSignal.timeout(15000)
    });
    if (!response.ok) {
        throw new Error(`Staging Neon Auth sign-in failed (HTTP ${response.status})`);
    }
    const token = response.headers.get('set-auth-jwt');
    jwtClaims(token);
    return token;
}

async function main() {
    const args = process.argv.slice(2);
    const value = flag => {
        const index = args.indexOf(flag);
        return index === -1 ? undefined : args[index + 1];
    };
    const authUrl = validatedAuthUrl(
        required('STAGING_NEON_AUTH_URL'), required('PRODUCTION_NEON_AUTH_URL')
    );
    const origin = validatedStagingOrigin(required('STAGING_BASE_URL'));
    const token = await signIn(
        authUrl,
        origin,
        required('STAGING_AUTH_TEST_EMAIL'),
        required('STAGING_AUTH_TEST_PASSWORD')
    );
    const result = await verifyCrud(value('--base-url'), {
        environment: value('--environment'),
        expectedSha: value('--expected-sha'),
        allowWrites: args.includes('--allow-writes'),
        getAccessToken: async () => token
    });
    console.log(JSON.stringify(result, null, 2));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
    try { await main(); }
    catch (error) {
        console.error(error.message);
        process.exitCode = 1;
    }
}

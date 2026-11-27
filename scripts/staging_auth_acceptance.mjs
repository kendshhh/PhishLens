import { pathToFileURL } from 'node:url';
import { withStagingAuth } from './staging_auth.mjs';
import { verifyCrud, verifyTarget } from './verify_crud.mjs';

function required(name) {
    const value = process.env[name];
    if (typeof value !== 'string' || !value.trim()) {
        throw new Error(`Missing required staging setting: ${name}`);
    }
    return value.trim();
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
    const email = process.env.STAGING_AUTH_USER_A_EMAIL ?? process.env.STAGING_AUTH_EMAIL;
    const password = process.env.STAGING_AUTH_USER_A_PASSWORD ?? process.env.STAGING_AUTH_PASSWORD;
    const authEnvironment = {
        ...process.env,
        STAGING_AUTH_USER_A_EMAIL: email,
        STAGING_AUTH_USER_A_PASSWORD: password
    };

    await verifyTarget(baseUrl, {
        environment: 'staging',
        expectedSha,
        allowWrites: true
    });
    const result = await withStagingAuth(
        getAccessToken => verifyCrud(baseUrl, {
            environment: 'staging',
            expectedSha,
            allowWrites: true,
            getAccessToken
        }),
        authEnvironment,
        'A'
    );
    console.log(JSON.stringify(result, null, 2));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
    main().catch(error => {
        const values = [
            process.env.STAGING_AUTH_USER_A_EMAIL,
            process.env.STAGING_AUTH_EMAIL,
            process.env.STAGING_AUTH_USER_A_PASSWORD,
            process.env.STAGING_AUTH_PASSWORD
        ];
        console.error(redact(error instanceof Error ? error.message : 'Authenticated staging acceptance failed', values));
        process.exitCode = 1;
    });
}
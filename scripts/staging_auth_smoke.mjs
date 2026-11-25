import { pathToFileURL } from 'node:url';
import { withStagingAuth } from './staging_auth.mjs';
import { verifyCrud } from './verify_crud.mjs';

function argument(flag) {
    const index = process.argv.indexOf(flag);
    return index === -1 ? undefined : process.argv[index + 1];
}

async function main() {
    const baseUrl = argument('--base-url');
    if (!baseUrl) throw new Error('A staging API base URL is required');
    const result = await withStagingAuth(
        getAccessToken => verifyCrud(baseUrl, {
            environment: argument('--environment'),
            expectedSha: argument('--expected-sha'),
            allowWrites: process.argv.includes('--allow-writes'),
            getAccessToken
        }),
        process.env,
        'A'
    );
    console.log(JSON.stringify(result, null, 2));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
    try { await main(); }
    catch (error) {
        console.error(error instanceof Error ? error.message : String(error));
        process.exitCode = 1;
    }
}
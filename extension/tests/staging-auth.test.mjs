import assert from 'node:assert/strict';
import { test } from 'node:test';
import { verifyReportIsolation } from '../../scripts/verify_crud.mjs';
import { validateStagingAuthAccounts } from '../../scripts/staging_auth.mjs';

const authEnvironment = {
    STAGING_NEON_AUTH_URL:
        'https://ep-staging.neonauth.c-4.ap-southeast-1.aws.neon.tech/neondb/auth',
    PHISHLENS_STAGING_AUTH_DATABASE: 'neondb',
    STAGING_AUTH_USER_A_EMAIL: 'phishlens-a@example.test',
    STAGING_AUTH_USER_A_PASSWORD: 'synthetic-a-password',
    STAGING_AUTH_USER_B_EMAIL: 'phishlens-b@example.test',
    STAGING_AUTH_USER_B_PASSWORD: 'synthetic-b-password'
};

test('staging Auth requires two distinct accounts and matches the configured Auth database path', () => {
    const accounts = validateStagingAuthAccounts(authEnvironment);
    assert.equal(accounts.A.email, 'phishlens-a@example.test');
    assert.equal(accounts.B.email, 'phishlens-b@example.test');

    assert.throws(() => validateStagingAuthAccounts({
        ...authEnvironment,
        STAGING_AUTH_USER_B_EMAIL: 'PHISHLENS-A@example.test'
    }), /two distinct synthetic Auth accounts/);
    const alternateDatabase = {
        ...authEnvironment,
        PHISHLENS_STAGING_AUTH_DATABASE: 'phishlens_dev',
        STAGING_NEON_AUTH_URL: authEnvironment.STAGING_NEON_AUTH_URL
            .replace('/neondb/auth', '/phishlens_dev/auth')
    };
    assert.equal(validateStagingAuthAccounts(alternateDatabase).A.email, 'phishlens-a@example.test');

    assert.throws(() => validateStagingAuthAccounts({
        ...authEnvironment,
        STAGING_NEON_AUTH_URL: authEnvironment.STAGING_NEON_AUTH_URL
            .replace('/neondb/auth', '/phishlens_dev/auth')
    }), /HTTPS Neon Auth URL/);
    assert.throws(() => validateStagingAuthAccounts({
        ...authEnvironment,
        PHISHLENS_STAGING_AUTH_DATABASE: 'phishlens-dev'
    }), /HTTPS Neon Auth URL/);
});

test('second synthetic user cannot list, read, update, or delete another user report', async () => {
    const calls = [];
    const notFound = async operation => {
        calls.push(operation);
        throw Object.assign(new Error('Analysis not found'), { status: 404 });
    };
    const client = {
        listAnalyses: async () => { calls.push('list'); return []; },
        getAnalysis: () => notFound('read'),
        updateAnalysis: () => notFound('update'),
        deleteAnalysis: () => notFound('delete')
    };

    assert.equal(await verifyReportIsolation(client, 'report-a'), 'passed');
    assert.deepEqual(calls, ['list', 'read', 'update', 'delete']);
});

test('cross-user visibility fails closed when another user can list the report', async () => {
    const client = {
        listAnalyses: async () => [{ id: 'report-a' }],
        getAnalysis: async () => { throw Object.assign(new Error('not found'), { status: 404 }); },
        updateAnalysis: async () => { throw Object.assign(new Error('not found'), { status: 404 }); },
        deleteAnalysis: async () => { throw Object.assign(new Error('not found'), { status: 404 }); }
    };

    await assert.rejects(verifyReportIsolation(client, 'report-a'),
        /Another Auth user can list this saved report/);
});

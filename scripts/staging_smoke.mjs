import assert from 'node:assert/strict';
import { appendFile } from 'node:fs/promises';
import {
    isRetryableStagingHistoryError,
    readStagingHistory,
    writeHistoryAccessOutput,
} from './staging_history.mjs';

const baseUrl = (process.env.STAGING_BASE_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');
const timeoutMs = Number(process.env.STAGING_SMOKE_TIMEOUT_MS || 120000);
const maxAttempts = Number(process.env.STAGING_MAX_ATTEMPTS || 30);
const retryDelayMs = Number(process.env.STAGING_RETRY_DELAY_MS || 3000);
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
let currentStage = { name: 'startup readiness', endpoint: '/health', status: undefined };

function transient(error) {
    // Once an HTTP response exists, classify its status before reading any error text.
    if (Number.isInteger(error?.status)) return isRetryableStagingHistoryError(error);
    const messages = [];
    const seen = new Set();
    let current = error;
    while (current && !seen.has(current) && messages.length < 5) {
        seen.add(current);
        if (current instanceof Error) messages.push(current.message);
        else messages.push(String(current));
        current = current.cause;
    }
    const detail = messages.join(' ');
    if (/redirect|invalid url|unsupported protocol|certificate|self[- ]signed|ERR_TLS/i.test(detail)) {
        return false;
    }
    return isRetryableStagingHistoryError(new Error(detail));
}

function requestError(message, { endpoint, status, retryable = false, cause } = {}) {
    const error = new Error(message, cause ? { cause } : undefined);
    error.endpoint = endpoint;
    error.status = status;
    error.retryable = retryable;
    return error;
}

async function readJson(path, remainingMs) {
    const endpoint = `${baseUrl}${path}`;
    let response;
    try {
        response = await fetch(endpoint, {
            signal: AbortSignal.timeout(Math.max(1, Math.min(10000, remainingMs))),
            redirect: 'error',
        });
    } catch (cause) {
        const reason = cause instanceof Error ? cause.message : String(cause);
        throw requestError(`GET ${endpoint} failed: ${reason}`, {
            endpoint,
            retryable: transient(cause),
            cause,
        });
    }

    currentStage.status = response.status;
    if (!response.ok) {
        let detail = '';
        try {
            detail = (await response.text()).trim().slice(0, 500);
        } catch {}
        throw requestError(
            `GET ${endpoint} returned HTTP ${response.status}${detail ? `: ${detail}` : ''}`,
            {
                endpoint,
                status: response.status,
                retryable: isRetryableStagingHistoryError({ status: response.status }),
            },
        );
    }

    try {
        return await response.json();
    } catch (cause) {
        const reason = cause instanceof Error ? cause.message : String(cause);
        throw requestError(`GET ${endpoint} returned invalid JSON: ${reason}`, {
            endpoint,
            status: response.status,
            cause,
        });
    }
}

async function retryStage(name, path, operation, deadline) {
    currentStage = { name, endpoint: `${baseUrl}${path}`, status: undefined };
    let lastError;
    let attempts = 0;

    while (attempts < maxAttempts && Date.now() < deadline) {
        attempts += 1;
        try {
            return await operation(Math.max(1, deadline - Date.now()));
        } catch (error) {
            lastError = error;
            if (!transient(error) || attempts >= maxAttempts || Date.now() >= deadline) break;

            const remainingMs = deadline - Date.now();
            console.error(
                `Staging ${name} attempt ${attempts}/${maxAttempts} failed; retrying in ${Math.min(retryDelayMs, remainingMs)} ms: ${redact(error.message)}`,
            );
            await sleep(Math.min(retryDelayMs, remainingMs));
        }
    }

    if (lastError) {
        lastError.endpoint ||= currentStage.endpoint;
        lastError.attempts = attempts;
        lastError.maxAttempts = maxAttempts;
        throw lastError;
    }
    throw requestError(
        `Staging ${name} exceeded its overall ${timeoutMs} ms deadline after ${attempts} attempt(s)`,
        { endpoint: currentStage.endpoint, status: currentStage.status },
    );
}

function redact(value) {
    return String(value)
        .replace(/\bBearer\s+[^\s,;]+/gi, 'Bearer [redacted]')
        .replace(/((?:password|token|secret|api[_-]?key)=)[^&\s]+/gi, '$1[redacted]')
        .replace(/(["']?(?:password|token|secret|api[_-]?key|authorization)["']?\s*[:=]\s*["']?)[^"'&\s,;}]+/gi, '$1[redacted]');
}

function reportStagingFailure(error) {
    const endpoint = error?.url || error?.endpoint || currentStage.endpoint;
    const status = Number.isInteger(error?.status) ? error.status : 'unavailable';
    const origin = error?.origin || 'assertion';
    const category = error?.category || 'staging_contract';
    const code = error?.code || 'staging_assertion_failed';
    const attempts = Number.isInteger(error?.attempts) ? error.attempts : 1;
    const max = Number.isInteger(error?.maxAttempts) ? error.maxAttempts : maxAttempts;
    console.error(`Staging check failed: GET ${redact(endpoint)}`);
    console.error(`status=${status} origin=${origin} category=${category} code=${code} attempts=${attempts}/${max}`);
    if (error?.responseBody) {
        console.error(`Response body (bounded): ${redact(error.responseBody)}`);
    }
    console.error(redact(error instanceof Error ? error.message : String(error)));
}

async function writeFailureSummary(error) {
    const summaryPath = process.env.GITHUB_STEP_SUMMARY;
    if (!summaryPath) return;
    const endpoint = error?.endpoint || currentStage.endpoint;
    const status = Number.isInteger(error?.status)
        ? `HTTP ${error.status}`
        : Number.isInteger(currentStage.status)
            ? `HTTP ${currentStage.status}`
            : 'no HTTP response';
    const detail = redact(error instanceof Error ? error.message : String(error));
    const attempts = Number.isInteger(error?.attempts) ? ` (attempts: ${error.attempts})` : '';
    const entry = [
        '',
        '### Staging smoke failed',
        `- Stage: ${redact(currentStage.name)}`,
        `- Endpoint: \`${redact(endpoint)}\``,
        `- Final result: ${status}${attempts}`,
        `- Error: ${detail}`,
        `- Overall deadline: ${timeoutMs} ms`,
        '',
    ].join('\n');
    await appendFile(summaryPath, entry, 'utf8');
}

async function main() {
    if (!Number.isSafeInteger(timeoutMs) || timeoutMs < 1 ||
        !Number.isSafeInteger(maxAttempts) || maxAttempts < 1 ||
        !Number.isSafeInteger(retryDelayMs) || retryDelayMs < 0) {
        throw new Error('STAGING_SMOKE_TIMEOUT_MS, STAGING_MAX_ATTEMPTS, and STAGING_RETRY_DELAY_MS must be valid non-negative integers (timeout and attempts must be positive).');
    }
    const deadline = Date.now() + timeoutMs;

    const health = await retryStage('health', '/health', remainingMs => readJson('/health', remainingMs), deadline);
    assert.deepEqual(health, { status: 'ok', service: 'phishlens-api' }, '/health response contract changed');
    const readiness = await retryStage('database readiness', '/ready', remainingMs => readJson('/ready', remainingMs), deadline);
    assert.deepEqual(readiness, { status: 'ready', database: 'connected' }, '/ready response contract changed');

    const result = await retryStage('saved-report history', '/api/analyses', async remainingMs => {
        const items = await readStagingHistory(
            baseUrl,
            fetch,
            {
                attempts: 1,
                delayMs: 0,
                timeoutMs: Math.max(1, Math.min(10000, remainingMs)),
            },
        );
        currentStage.status = items === null ? 401 : 200;
        if (process.argv.includes('--github-output')) {
            await writeHistoryAccessOutput(items, process.env.GITHUB_OUTPUT);
        }
        return items === null ? { kind: 'authentication-required' } : { kind: 'history', items };
    }, deadline);

    if (result.kind === 'authentication-required') {
        console.log('Staging passed: health, database readiness, and anonymous saved-report authentication (HTTP 401 Bearer).');
        return;
    }

    const demo = result.items.find(item => item.id === '29d80c39-ec0d-4db8-a6e5-87444ba2600c');
    assert.ok(demo, 'Migrated and seeded demo analysis must be returned through the extension client');
    assert.equal(demo.subject, 'Synthetic account notice');
    assert.equal(demo.prediction, 'phishing');
    assert.equal(demo.risk_level, 'high');
    assert.equal(demo.confidence, 0.93);
    assert.ok(Array.isArray(demo.threat_indicators));
    assert.ok(Number.isFinite(Date.parse(demo.created_at)));
    console.log('Staging passed: health, database readiness, and seeded history through the staging history contract.');
}

main().catch(async error => {
    if (Number.isInteger(error?.status)) currentStage.status = error.status;
    try {
        await writeFailureSummary(error);
    } catch (summaryError) {
        console.error(`Could not write GitHub step summary: ${summaryError instanceof Error ? summaryError.message : String(summaryError)}`);
    }
    reportStagingFailure(error);
    console.error(`Staging ${currentStage.name} failed: ${redact(error instanceof Error ? error.message : String(error))}`);
    process.exitCode = 1;
});

import test from "node:test";
import assert from "node:assert/strict";

import { getAnalyses } from "../js/api.js";

const originalFetch = globalThis.fetch;

const validAnalysis = {
    id: "29d80c39-ec0d-4db8-a6e5-87444ba2600c",
    subject: "Synthetic account notice",
    prediction: "phishing",
    confidence: 0.93,
    risk_level: "high",
    threat_indicators: [
        {
            type: "link",
            detail: "Synthetic lookalike link"
        }
    ],
    explanation: "Synthetic test explanation",
    created_at: "2026-10-14T04:00:00Z"
};

test.afterEach(() => {
    globalThis.fetch = originalFetch;
});

function mockResponse(data) {
    globalThis.fetch = async () => ({
        ok: true,
        status: 200,
        clone: () => new Response(JSON.stringify(data)),
        json: async () => data
    });
}

test("returns records from items", async () => {
    mockResponse({ items: [validAnalysis] });

    const result = await getAnalyses("https://example.test");

    assert.deepEqual(result, [validAnalysis]);
});

test("returns empty history", async () => {
    mockResponse({ items: [] });

    const result = await getAnalyses("https://example.test");

    assert.deepEqual(result, []);
});

test("rejects an HTTP 503 response", async () => {
    globalThis.fetch = async () => ({
        ok: false,
        status: 503,
        text: async () => "database unavailable"
    });

    await assert.rejects(
        getAnalyses("https://example.test", { retries: 0 }),
        error => error.status === 503 &&
            error.url === "https://example.test/api/analyses" &&
            error.origin === "http" &&
            error.category === "staging_api_outage" &&
            error.code === "history_http_5xx" &&
            error.responseBody === "database unavailable" &&
            /HTTP 503/.test(error.message)
    );
});

test("classifies HTTP 4xx responses as authentication or authorization failures", async () => {
    globalThis.fetch = async () => new Response("sign in required", {
        status: 401,
        headers: { "WWW-Authenticate": "Bearer" }
    });

    await assert.rejects(
        getAnalyses("https://example.test", { retries: 0 }),
        error => error.status === 401 &&
            error.url === "https://example.test/api/analyses" &&
            error.origin === "http" &&
            error.category === "authentication_authorization" &&
            error.code === "history_http_4xx" &&
            error.wwwAuthenticate === "Bearer" &&
            error.responseBody === "sign in required"
    );
});

test("rejects an invalid response wrapper", async () => {
    mockResponse({ wrong_field: [] });

    await assert.rejects(
        getAnalyses("https://example.test", { retries: 0 }),
        error => error.category === "backend_contract_mismatch" &&
            error.code === "history_schema_mismatch" &&
            error.origin === "contract" &&
            error.status === 200 &&
            /Invalid history data/.test(error.message)
    );
});

test("rejects a null record", async () => {
    mockResponse({ items: [null] });

    await assert.rejects(
        getAnalyses("https://example.test"),
        /Invalid history data/
    );
});

test("rejects confidence stored as text", async () => {
    mockResponse({
        items: [{
            ...validAnalysis,
            confidence: "not-a-number"
        }]
    });

    await assert.rejects(
        getAnalyses("https://example.test"),
        /Invalid history data/
    );
});

test("rejects confidence outside the allowed range", async () => {
    mockResponse({
        items: [{
            ...validAnalysis,
            confidence: 9
        }]
    });

    await assert.rejects(
        getAnalyses("https://example.test"),
        /Invalid history data/
    );
});

test("accepts nullable result fields", async () => {
    const pendingAnalysis = {
        ...validAnalysis,
        prediction: null,
        confidence: null,
        risk_level: null,
        explanation: null
    };

    mockResponse({ items: [pendingAnalysis] });

    const result = await getAnalyses("https://example.test");

    assert.deepEqual(result, [pendingAnalysis]);
});

test("rejects invalid JSON", async () => {
    globalThis.fetch = async () => ({
        ok: true,
        status: 200,
        clone: () => new Response("{not-json"),
        json: async () => { throw new SyntaxError("Invalid JSON"); }
    });

    await assert.rejects(
        getAnalyses("https://example.test", { retries: 0 }),
        error => error.category === "backend_contract_mismatch" &&
            error.code === "history_invalid_json" &&
            error.origin === "contract" &&
            error.responseBody === "{not-json"
    );
});

test("handles a network failure", async () => {
    globalThis.fetch = async () => {
        throw new TypeError("Network unavailable");
    };

    await assert.rejects(
        getAnalyses("https://example.test", { retries: 0 }),
        error => error.category === "transport_failure" &&
            error.code === "history_network_error" &&
            error.origin === "network" &&
            error.url === "https://example.test/api/analyses" &&
            /Network unavailable/.test(error.message)
    );
});

test("handles a request timeout as a distinct transport failure", async () => {
    globalThis.fetch = async () => { throw new DOMException("The request timed out", "TimeoutError"); };

    await assert.rejects(
        getAnalyses("https://example.test", { retries: 0 }),
        error => error.category === "transport_failure" &&
            error.code === "history_timeout" &&
            error.origin === "timeout" &&
            error.status === null &&
            error.timeoutMs === 10000 &&
            /timed out/.test(error.message)
    );
});

test("bounds the captured HTTP response body", async () => {
    globalThis.fetch = async () => new Response("x".repeat(10000), { status: 503 });

    await assert.rejects(
        getAnalyses("https://example.test", { retries: 0 }),
        error => error.responseBody.length <= 2070 &&
            error.responseBody.endsWith("… [truncated]") &&
            error.message.length < 2300
    );
});

test("retries a transient history outage and returns the recovered response", async () => {
    let calls = 0;
    globalThis.fetch = async () => {
        calls++;
        if (calls === 1) return new Response("database starting", { status: 503 });
        return new Response(JSON.stringify({ items: [validAnalysis] }), {
            status: 200,
            headers: { "Content-Type": "application/json" }
        });
    };

    assert.deepEqual(
        await getAnalyses("https://example.test", { retries: 1, retryDelayMs: 0 }),
        [validAnalysis]
    );
    assert.equal(calls, 2);
});

for (const [failure, error] of [
    ["network failure", new TypeError("Network unavailable")],
    ["timeout", new DOMException("The request timed out", "TimeoutError")]
]) {
    test(`retries a transient ${failure} and returns the recovered response`, async () => {
        let calls = 0;
        globalThis.fetch = async () => {
            calls++;
            if (calls === 1) throw error;
            return new Response(JSON.stringify({ items: [validAnalysis] }), {
                status: 200,
                headers: { "Content-Type": "application/json" }
            });
        };

        assert.deepEqual(
            await getAnalyses("https://example.test", { retries: 1, retryDelayMs: 0 }),
            [validAnalysis]
        );
        assert.equal(calls, 2);
    });
}
test("rejects an ID that is not a UUID", async () => {
    mockResponse({
        items: [{ ...validAnalysis, id: "not-a-uuid" }]
    });

    await assert.rejects(
        getAnalyses("https://example.test"),
        /Invalid history data/
    );
});

for (const timestamp of [
    0,
    "0",
    "2026-10-14",
    "2026-10-14T04:00:00",
    "2026-10-14T04:00:00+08:00",
    "2026-02-30T04:00:00Z"
]) {
    test(`rejects invalid UTC timestamp ${JSON.stringify(timestamp)}`, async () => {
        mockResponse({
            items: [{ ...validAnalysis, created_at: timestamp }]
        });

        await assert.rejects(
            getAnalyses("https://example.test"),
            /Invalid history data/
        );
    });
}

for (const timestamp of [
    "2026-10-14T04:00:00Z",
    "2026-10-14T04:00:00+00:00",
    "2026-10-13T15:07:51.365605+00:00"
]) {
    test(`accepts UTC timestamp ${timestamp}`, async () => {
        const record = {
            ...validAnalysis,
            created_at: timestamp
        };

        mockResponse({ items: [record] });

        assert.deepEqual(
            await getAnalyses("https://example.test"),
            [record]
        );
    });
}

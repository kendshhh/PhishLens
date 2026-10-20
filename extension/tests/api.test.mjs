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
        status: 503
    });

    await assert.rejects(
        getAnalyses("https://example.test"),
        /Failed to load history/
    );
});

test("rejects an invalid response wrapper", async () => {
    mockResponse({ wrong_field: [] });

    await assert.rejects(
        getAnalyses("https://example.test"),
        /Invalid history data/
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
        json: async () => {
            throw new SyntaxError("Invalid JSON");
        }
    });

    await assert.rejects(
        getAnalyses("https://example.test"),
        SyntaxError
    );
});

test("handles a network failure", async () => {
    globalThis.fetch = async () => {
        throw new TypeError("Network unavailable");
    };

    await assert.rejects(
        getAnalyses("https://example.test"),
        /Network unavailable/
    );
});
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
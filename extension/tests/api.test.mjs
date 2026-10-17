
import test from "node:test";
import assert from "node:assert/strict";
import { getAnalyses } from "../js/api.js";


test("Gets saved analyses", async () => {
    globalThis.fetch = async () => ({
        ok: true,
        json: async () => ({
            items: [
                {
                    id: "demo-1",
                    subject: "Synthetic account notice",
                    prediction: "phishing"
                }
            ]
        })
    });

    const history = await getAnalyses("http://localhost:8000");

    assert.equal(history.length, 1);
    assert.equal(history[0].prediction, "phishing");
});

test("Returns empty history", async () => {
    globalThis.fetch = async () => ({
        ok: true,
        json: async () => ({ items: [] })
    });

    const history = await getAnalyses("http://localhost:8000");

    assert.deepEqual(history, []);
});

test("Handles failed requests", async () => {
    globalThis.fetch = async () => ({
        ok: false,
        status: 500
    });

    await assert.rejects(
        getAnalyses("http://localhost:8000"),
        /Failed to load history/
    );
});

test("Rejects invalid response format", async () => {
    globalThis.fetch = async () => ({
        ok: true,
        json: async () => ({ wrong_field: [] })
    });

    await assert.rejects(
        getAnalyses("http://localhost:8000"),
        /Invalid history data/
    );
});

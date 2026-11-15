import test from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";

// The manifest's public key fixes the extension ID, which is the origin Neon Auth trusts.
// See docs/extension-identity.md before changing either value.
const EXPECTED_EXTENSION_ID = "ceneonaedddlkdocdapimkfggbjcchlb";

test("the manifest public key produces the documented extension ID", async () => {
  const manifest = JSON.parse(await readFile(new URL("../manifest.json", import.meta.url), "utf8"));
  assert.equal(typeof manifest.key, "string");
  const publicKey = Buffer.from(manifest.key, "base64");
  assert.equal(publicKey.toString("base64"), manifest.key, "The key must be canonical base64");
  const extensionId = createHash("sha256").update(publicKey).digest("hex").slice(0, 32)
    .replace(/[0-9a-f]/g, digit => String.fromCharCode("a".charCodeAt(0) + parseInt(digit, 16)));
  assert.equal(extensionId, EXPECTED_EXTENSION_ID);
});

test("the manifest carries only a public key", async () => {
  const text = await readFile(new URL("../manifest.json", import.meta.url), "utf8");
  assert.doesNotMatch(text, /PRIVATE KEY/);
});

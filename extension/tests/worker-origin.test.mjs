import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const worker = await readFile(new URL('../background.js', import.meta.url), 'utf8');
const popup = await readFile(new URL('../js/popup.js', import.meta.url), 'utf8');
const sharedConfigImport = /import\s+\{\s*API_BASE_URL\s*\}\s+from\s+["']\.\/js\/config\.js["'];/;
const popupConfigImport = /import\s+\{\s*API_BASE_URL\s*\}\s+from\s+["']\.\/config\.js["'];/;
const localScannerImport = /from\s+["']\.\/ai\/(?:local-analyzer|live-workflow)\.mjs["']/;
const forbiddenOrigins = /127\.0\.0\.1|localhost|phishlens-api-ocvt\.onrender\.com/;

test('worker establishes a safe origin through shared config or the local scanner', () => {
  const usesLocalScanner = localScannerImport.test(worker);
  assert.ok(sharedConfigImport.test(worker) || usesLocalScanner,
    'worker must import API_BASE_URL or use a recognized local scanner');
  assert.doesNotMatch(worker, forbiddenOrigins);
  assert.doesNotMatch(popup, forbiddenOrigins);
  assert.match(popup, popupConfigImport);
});


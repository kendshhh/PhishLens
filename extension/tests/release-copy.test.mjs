import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const popup = await readFile(new URL('../popup.html', import.meta.url), 'utf8');
const controller = await readFile(new URL('../js/popup.js', import.meta.url), 'utf8');
const accountPopup = await readFile(new URL('../js/account-popup.js', import.meta.url), 'utf8');
const releasePopup = await readFile(new URL('../popup.js', import.meta.url), 'utf8');

test('saved-report copy describes the real authenticated server path without pending placeholders', () => {
  assert.match(popup, /Saving requires sign-in and uploads the <strong>original email text<\/strong> to the PhishLens API/);
  assert.match(popup, /saves the result to your signed-in account/);
  assert.doesNotMatch(popup, /Live account integration is pending|Account saving is not connected yet/);
});

test('synthetic demo notice is shown only for explicit preview mode', () => {
  assert.match(popup, /id="reports-preview-notice"[^>]*hidden/);
  assert.match(controller, /show\('reports-preview-notice', preview\)/);
  assert.match(accountPopup, /canAccessReports: \(\) => accounts\.state\.status === 'signed-in', preview/);
});

test('single release package defaults to production and selects staging only for the internal staging query', () => {
  assert.match(releasePopup, /requestedEnvironment === 'staging' \? 'staging' : 'production'/);
  assert.match(releasePopup, /API_BASE_URLS\[releaseEnvironment\]/);
  assert.match(releasePopup, /AUTH_CONFIGS\[releaseEnvironment\]/);
  assert.match(releasePopup, /initializeAccountPopup\(\{[\s\S]*apiOrigin/);
});

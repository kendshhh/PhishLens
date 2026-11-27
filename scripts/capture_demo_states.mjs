// Capture presenter screenshots of the release package's visible states in installed
// Chrome (Issue #151). The repository's extension files must match the package identity
// in output/extension/evidence.json. All network requests are blocked; only synthetic
// text is analyzed locally. Screenshots and a state record go to output/demo-states/.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const chromePath = process.env.PHISHLENS_CHROME;
const playwrightPath = process.env.PHISHLENS_PLAYWRIGHT;
if (!chromePath || !playwrightPath) throw Error('Set PHISHLENS_CHROME and PHISHLENS_PLAYWRIGHT to existing local runtimes.');
const { chromium } = await import(pathToFileURL(playwrightPath).href);

const out = path.join(root, 'output', 'demo-states');
const SYNTHETIC_EMAIL = 'Subject: Urgent account review\n\nYour account will be closed today. Review it at '
  + 'https://example.invalid and enter your password to keep access.';
const record = { scope: 'installed extension presenter states; synthetic text; all network blocked',
  recorded_at: new Date().toISOString(), states: [] };
const profile = await mkdtemp(path.join(os.tmpdir(), 'phishlens-demo-'));
let context;

try {
  const identity = JSON.parse(await readFile(path.join(root, 'output/extension/evidence.json'), 'utf8'));
  assert.equal(identity.runtime_or_packaging_changes, false, 'Use a package built from clean inputs');
  for (const [asset, expected] of Object.entries(identity.files_sha256)) {
    const actual = createHash('sha256').update(await readFile(path.join(root, 'extension', asset))).digest('hex');
    assert.equal(actual, expected, `Extension file differs from the package: ${asset}`);
  }
  Object.assign(record, { source_commit: identity.source_commit, package_sha256: identity.archive_sha256,
    extension_version: identity.extension_version });
  await mkdir(out, { recursive: true });

  context = await chromium.launchPersistentContext(profile, {
    executablePath: chromePath, headless: true, ignoreDefaultArgs: ['--disable-extensions'],
    viewport: { width: 420, height: 900 },
    args: ['--enable-unsafe-extension-debugging', '--disable-background-networking', '--no-first-run'],
  });
  let blockedRequests = 0;
  await context.route(/^https?:\/\//, route => { blockedRequests++; return route.abort(); });
  record.chrome = context.browser()?.version();
  const session = await context.browser().newBrowserCDPSession();
  const { id } = await session.send('Extensions.loadUnpacked', { path: path.join(root, 'extension') });
  record.extension_id = id;
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(`chrome-extension://${id}/popup.html`);

  const capture = async (file, state, observed) => {
    await page.evaluate(() => scrollTo(0, 0));
    await page.screenshot({ path: path.join(out, file), fullPage: true });
    const sha256 = createHash('sha256').update(await readFile(path.join(out, file))).digest('hex');
    record.states.push({ file, state, observed, sha256 });
  };
  const analyze = text => page.evaluate(value => {
    void chrome.runtime.sendMessage({ type: 'phishlens-analyze-text', text: value });
  }, text);

  await page.locator('#empty-state').waitFor({ state: 'visible' });
  await capture('01-ready.png', 'Ready before a check',
    (await page.locator('#empty-state').innerText()).trim());

  await analyze(SYNTHETIC_EMAIL);
  // The loading screenshot is required. Only a timeout means the state was missed, and that
  // fails the run; any other error (including a screenshot write) propagates unchanged.
  const loading = page.locator('#loading-state');
  const loadingShown = await loading.waitFor({ state: 'visible', timeout: 3000 }).then(
    () => true,
    error => { if (error?.name === 'TimeoutError') return false; throw error; },
  );
  assert.ok(loadingShown, 'The loading state finished before it could be captured; rerun the capture');
  const loadingHeading = (await page.locator('#loading-state h2').innerText()).trim();
  await capture('02-loading.png', 'Loading while the local check runs', loadingHeading);
  // A check only moves from loading to its outcome, so loading visible both before and after
  // the screenshot proves the image shows the loading state.
  assert.equal(await loading.isVisible(), true,
    'The check completed during the loading screenshot; rerun the capture');
  await page.locator('#result-state').waitFor({ state: 'visible', timeout: 120000 });
  const label = (await page.locator('#classification').innerText()).trim();
  assert.match(label, /Suspicious — review before acting|No strong warning signs|Uncertain — check before acting/);
  assert.doesNotMatch(label, /\b(safe|genuine|legitimate)\b/i);
  await capture('03-result.png', 'Local result with its stated limits', label);

  await page.evaluate(async () => {
    await chrome.storage.session.set({ phishlensDebugFailNext: true });
  });
  await analyze(SYNTHETIC_EMAIL);
  await page.locator('#error-state').waitFor({ state: 'visible', timeout: 60000 });
  assert.equal(await page.locator('#result-state').isVisible(), false, 'A failure must not show a verdict');
  await capture('04-controlled-failure.png', 'Controlled local-model failure (built-in one-shot debug flag)',
    (await page.locator('#error-state h2').innerText()).trim());

  await page.locator('#retry-scan').click();
  await page.locator('#result-state').waitFor({ state: 'visible', timeout: 120000 });
  await capture('05-recovery.png', 'Recovery after Try again',
    (await page.locator('#classification').innerText()).trim());

  await page.locator('#clear-button').click();
  await page.locator('#empty-state').waitFor({ state: 'visible' });
  record.states.push({ state: 'Clear returns to ready', observed: 'Ready state shown' });

  assert.deepEqual(errors, [], 'No page JavaScript errors');
  record.blocked_network_requests = blockedRequests;
  record.success = true;
} catch (error) {
  record.success = false;
  record.failure = error.message;
  process.exitCode = 1;
} finally {
  if (context) await context.close();
  const absolute = path.resolve(profile);
  if (path.dirname(absolute) === path.resolve(os.tmpdir()) && path.basename(absolute).startsWith('phishlens-demo-')) {
    await rm(absolute, { recursive: true, force: true });
    record.temporary_profile_removed = true;
  }
  await mkdir(out, { recursive: true });
  await writeFile(path.join(out, 'demo-states.json'), JSON.stringify(record, null, 2) + '\n');
  console.log(JSON.stringify(record, null, 2));
}

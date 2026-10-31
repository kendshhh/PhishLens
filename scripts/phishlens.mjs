#!/usr/bin/env node
// Small repository commands, not a separate application or a prerequisite for users.
import { readFile, stat } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import os from 'node:os';
import { createLocalAnalyzer, MODEL_SHA256 } from '../extension/ai/local-analyzer.mjs';
import { VERSION as OBSERVATIONS_VERSION } from '../extension/ai/observations.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const [command = 'help', ...args] = process.argv.slice(2);
const read = relative => readFile(path.join(root, relative));
const analyzer = createLocalAnalyzer({
  fetchImpl: async url => new Response(await readFile(fileURLToPath(url)))
});

async function modelCheck() {
  const model = await read('extension/ai/tfidf_v12a.json');
  if (hash(model) !== MODEL_SHA256) throw Error('Model hash differs from the frozen v12a artifact.');
  const expected = {
    'core.mjs': 'fbef6d86cc179c960b38307b6e9d72462c454ccdbdad688f7e353193f8b0b447',
    'observations.mjs': '97d25c61cc8975e89a5d3de9072374534d8b0a6b9099f07a537f440e6bead3c4'
  };
  for (const [file, sha] of Object.entries(expected)) {
    if (hash(await read('extension/ai/' + file)) !== sha) throw Error('Packaged AI module differs: ' + file);
  }
  const result = await analyzer('Please confirm the meeting agenda with your project team.');
  console.log(JSON.stringify({ check: 'model integrity and software smoke check',
    model_sha256: MODEL_SHA256, bytes: model.length, raw_alert_threshold: result.alert_threshold,
    observations_version: OBSERVATIONS_VERSION,
    displayed_threshold_percent: 100 * result.alert_threshold_score,
    evidence_spans_valid: result.verification.quote_spans_valid,
    accuracy_test: false }, null, 2));
}

async function recordsCheck() {
  const manifest = JSON.parse(await read('benchmark-records/manifest.json'));
  let bytes = 0;
  for (const item of manifest.files) {
    const resolved = path.resolve(root, 'benchmark-records', item.file);
    const base = path.resolve(root, 'benchmark-records') + path.sep;
    if (!resolved.startsWith(base) || /private|\.eml$/i.test(item.file)) throw Error('Invalid archive entry');
    const data = await readFile(resolved);
    if (data.length !== item.bytes || hash(data) !== item.sha256) throw Error('Evidence changed: ' + item.file);
    bytes += data.length;
  }
  console.log(JSON.stringify({ files_verified: manifest.files.length, bytes, originals_modified: false }, null, 2));
}

function run(program, arguments_) {
  const result = spawnSync(program, arguments_, { cwd: root, stdio: 'inherit', windowsHide: true });
  if (result.error) throw Error('Cannot start ' + program + '. See docs/TFIDF_DEBUGGING.md for setup.');
  if (result.status !== 0) process.exitCode = result.status || 1;
}

try {
  if (command === 'model-check') await modelCheck();
  else if (command === 'records-check') await recordsCheck();
  else if (command === 'doctor') {
    console.log(JSON.stringify({ node: process.version, os: os.platform(), os_release: os.release(),
      architecture: os.arch(), root, chrome_extension: path.join(root, 'extension'),
      backend: 'Optional for local scans; AI_MODE=tfidf required for matching saved reports.' }, null, 2));
    await modelCheck();
    await stat(path.join(root, 'extension/manifest.json'));
    console.log('Next: npm test; npm run lint; load extension/ at chrome://extensions.');
  } else if (command === 'test') run(process.execPath, ['--test', 'extension/tests/*.test.mjs']);
  else if (command === 'setup-models') run(process.execPath, ['scripts/setup_judge_assets.mjs', ...args]);
  else if (command === 'package') run(process.env.PHISHLENS_PYTHON || 'python', ['scripts/package_extension.py', ...args]);
  else if (command === 'scan') {
    if (args.length !== 2 || args[0] !== '--file') throw Error('Usage: npm run phishlens -- scan --file <plain-text-file>');
    const input = await readFile(path.resolve(args[1]), 'utf8');
    const r = await analyzer(input);
    console.log(JSON.stringify({ verdict: r.verdict, research_risk_score_percent: r.risk_percent,
      alert_threshold_percent: r.alert_threshold_score * 100, raw_margin: r.raw_margin,
      input_truncated: r.input_truncated, model_sha256: r.model_sha256,
      evidence_checked: r.verification.evidence_checked, matched_features: r.matched_features,
      model_ms: r.model_ms, workflow_ms: r.workflow_ms,
      assessment: r.assessment, actions: r.actions,
      full_review_executed: false,
      note: 'Primary TF-IDF diagnostic only. The full LLM/KRR/LightGBM workflow runs in Chrome. Source text and quotes omitted.' }, null, 2));
  } else if (command === 'help') console.log([
    'PhishLens developer commands (from the repository root):',
    'npm run phishlens -- doctor          Check runtime, model and folder paths',
    'npm run phishlens -- model-check     Check frozen model/core integrity',
    'npm run phishlens -- records-check   Verify archived benchmark evidence',
    'npm run phishlens -- scan --file message.txt   Debug primary TF-IDF only (full review runs in Chrome)',
    'npm run phishlens -- test            Run extension tests',
    'npm run phishlens -- setup-models --download   Install pinned public LLM weights locally',
    'npm run phishlens -- package --include-models  Build the full offline extension using Python',
    'Chrome service-worker and popup consoles remain the primary extension debuggers.',
    'See docs/TFIDF_DEBUGGING.md.'
  ].join('\n'));
  else throw Error('Unknown command. Run npm run phishlens -- help.');
} catch (error) {
  console.error(error.message); process.exitCode = 1;
}

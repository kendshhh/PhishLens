// Build the static PhishLens web app into web/dist for Vercel or local preview.
// The web app reuses the extension's UI, API client and local analysis modules,
// so they are copied rather than duplicated in the repository. Uses only Node
// built-ins, so the deployment needs no npm install.
import { cp, mkdir, readdir, readFile, rm, stat, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { webBuildConfig, deploymentConfig } from './web_build_config.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const out = path.join(root, 'web', 'dist');
// Validate before deleting the previous output. These settings are all public.
const config = webBuildConfig();
const routes = deploymentConfig(config);
const vercelOutput = path.join(root, '.vercel', 'output');

// [source relative to the repository, destination relative to web/dist]
const COPIES = [
  ['web/index.html', 'index.html'],
  ['web/app.js', 'app.js'],
  ['web/runtime.js', 'runtime.js'],
  ['web/account-storage.js', 'account-storage.js'],
  ['web/favicon.svg', 'favicon.svg'],
  ['web/css/web.css', 'css/web.css'],
  ['extension/css/popup.css', 'css/popup.css'],
  ['extension/js', 'js'],
  ['extension/ai', 'ai'],
  ['extension/vendor/neon', 'vendor/neon'],
];
// The LLM judge worker needs ~1 GB of weights and the 54 MB ML runtime, which a
// static site does not ship; the web app reports the judge as unavailable.
const EXCLUDED = new Set(['ai/judge-worker.mjs']);

async function* files(dir) {
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) yield* files(full);
    else yield full;
  }
}

await rm(out, { recursive: true, force: true });
for (const [from, to] of COPIES) {
  const source = path.join(root, from);
  const target = path.join(out, to);
  await mkdir(path.dirname(target), { recursive: true });
  await cp(source, target, { recursive: true,
    filter: src => !EXCLUDED.has(path.relative(out, path.join(target, path.relative(source, src))).split(path.sep).join('/')) });
}

await writeFile(path.join(out, 'js/config.js'), 'export const API_BASE_URL = globalThis.location.origin;\n');
const auth = config.authUrl ? `{ enabled: true, authUrl: ${JSON.stringify(config.authUrl)}, database: ${JSON.stringify(config.database)}, apiOrigin: globalThis.location.origin }` : 'null';
await writeFile(path.join(out, 'js/auth-config.js'), `export const AUTH_CONFIG = ${auth};\n`);
let html = await readFile(path.join(out, 'index.html'), 'utf8');
html = html.replace('Account saving is not connected yet; local scanning remains available.',
  config.authUrl ? 'Sign in to save to your personal account.' : 'Account saving is disabled in this build; local scanning remains available.')
  .replace('Live account integration is pending. The demo preview uses synthetic records only.',
    config.authUrl ? 'Only reports saved to your signed-in account appear here.' : 'Account integration is disabled in this build.')
  .replace('Live account integration is pending.', config.authUrl ? 'Sign-in is required.' : 'Account integration is disabled in this build.');
await writeFile(path.join(out, 'index.html'), html);

// Fail the build if any relative module import or packaged asset is missing.
const missing = [];
let modules = 0;
for await (const file of files(out)) {
  if (!/\.(m?js)$/.test(file) || file.includes(`${path.sep}vendor${path.sep}`)) continue;
  modules++;
  const source = await readFile(file, 'utf8');
  const specifiers = [
    ...source.matchAll(/(?:import|export)\s[^'"`]*?from\s*['"](\.{1,2}\/[^'"]+)['"]/g),
    ...source.matchAll(/import\(\s*['"](\.{1,2}\/[^'"]+)['"]\s*\)/g),
  ].map(match => match[1]);
  for (const specifier of specifiers) {
    try { await stat(path.resolve(path.dirname(file), specifier)); }
    catch { missing.push(`${path.relative(out, file)} -> ${specifier}`); }
  }
}
for (const asset of ['ai/tfidf_v12a.json', 'ai/contract.json', 'ai/reevaluators/manifest.json']) {
  try { await stat(path.join(out, asset)); } catch { missing.push(asset); }
}
if (missing.length) {
  console.error('Web build is missing files:\n  ' + missing.join('\n  '));
  process.exit(1);
}
const manifest = {};
for await (const file of files(out)) {
  manifest[path.relative(out, file).split(path.sep).join('/')] = createHash('sha256').update(await readFile(file)).digest('hex');
}
const git = args => execFileSync('git', args, { cwd: root, encoding: 'utf8', windowsHide: true }).trim();
const identity = { schema: 1, source_sha: git(['rev-parse', 'HEAD']),
  source_dirty: Boolean(git(['status', '--porcelain', '--untracked-files=normal'])),
  ...config, backend_sha_verified: false, files: Object.fromEntries(Object.entries(manifest).sort()) };
await writeFile(path.join(out, 'build-info.json'), JSON.stringify(identity, null, 2) + '\n');
await writeFile(path.join(root, 'web/.build-routing.json'), JSON.stringify(routes, null, 2) + '\n');
await rm(vercelOutput, { recursive: true, force: true });
if (config.environment !== 'development') {
  await mkdir(vercelOutput, { recursive: true });
  await cp(out, path.join(vercelOutput, 'static'), { recursive: true });
  await writeFile(path.join(vercelOutput, 'config.json'), JSON.stringify(routes, null, 2) + '\n');
}
console.log(`Built the PhishLens web app in ${path.relative(root, out)} (${modules} modules checked).`);
console.log(`Environment: ${config.environment}; accounts: ${config.authUrl ? 'configured (hosted acceptance still required)' : 'disabled'}.`);

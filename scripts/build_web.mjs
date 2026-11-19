// Build the static PhishLens web app into web/dist for Vercel or local preview.
// The web app reuses the extension's UI, API client and local analysis modules,
// so they are copied rather than duplicated in the repository. Uses only Node
// built-ins, so the deployment needs no npm install.
import { cp, mkdir, readdir, readFile, rm, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const out = path.join(root, 'web', 'dist');

// [source relative to the repository, destination relative to web/dist]
const COPIES = [
  ['web/index.html', 'index.html'],
  ['web/app.js', 'app.js'],
  ['web/runtime.js', 'runtime.js'],
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
console.log(`Built the PhishLens web app in ${path.relative(root, out)} (${modules} modules checked).`);

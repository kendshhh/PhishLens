import { build } from 'esbuild';
import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
await mkdir('extension/vendor/neon', { recursive: true });
  const result = await build({ stdin: { contents: `import { createAuthClient as create } from '@neon/auth';
import { getGlobalBroadcastChannel } from 'better-auth/client';
// The pinned SDK broadcasts raw session data through localStorage by default.
// This extension revalidates cookies instead; never persist that broadcast.
export function createAuthClient(...args) {
  getGlobalBroadcastChannel().post = () => {};
  return create(...args);
}
export { BetterAuthVanillaAdapter } from '@neon/auth/vanilla';`, resolveDir: process.cwd() },
    outfile: 'extension/vendor/neon/sdk.mjs', bundle: true, platform: 'browser',
    format: 'esm', target: 'chrome127', minify: true, legalComments: 'inline', metafile: true });
const packages = new Map();
for (const output of Object.values(result.metafile.outputs)) for (const input of Object.keys(output.inputs)) {
  if (!input.includes('node_modules/')) continue;
  let folder = path.dirname(path.resolve(input));
  while (folder !== path.dirname(folder)) {
    try {
      const pkg = JSON.parse(await readFile(path.join(folder, 'package.json'), 'utf8'));
      if (!packages.has(pkg.name)) {
        const files = (await readdir(folder)).filter(name => /^(license|licence|copying)(\.|$)/i.test(name));
        const licenses = await Promise.all(files.map(name => readFile(path.join(folder, name), 'utf8')));
        packages.set(pkg.name, `${pkg.name}@${pkg.version} (${pkg.license || 'see upstream'})\n${licenses.join('\n')}`);
      }
      break;
    } catch { folder = path.dirname(folder); }
  }
}
await writeFile('extension/vendor/neon/THIRD_PARTY_NOTICES.txt', [...packages.values()].sort().join('\n\n---\n\n') + '\n');

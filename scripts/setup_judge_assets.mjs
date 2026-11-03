// Provision pinned public weights into ignored local storage. Never sends email.
import { readFile, writeFile, mkdir, stat } from 'node:fs/promises';
import { createReadStream } from 'node:fs';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const download = process.argv.slice(2).includes('--download');
const manifest = JSON.parse(await readFile(path.join(root, 'extension/ai/judge-assets.json')));
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
let checked = 0;
for (const entry of manifest.files) {
  const pieces = entry.chunks || [entry];
  let allPresent = true;
  for (const piece of pieces) {
    const relative = piece.path || entry.path;
    if (!relative.startsWith('llama/') || relative.split('/').includes('..')) throw Error('Invalid pinned model path');
    const dest = path.join(root, 'extension/model-assets', relative);
    try {
      const info = await stat(dest); if (info.size !== piece.bytes) throw Error('Wrong size');
      const h = createHash('sha256'); for await (const bytes of createReadStream(dest)) h.update(bytes);
      if (h.digest('hex') !== piece.sha256) throw Error('Wrong hash');
    } catch { allPresent = false; break; }
  }
  if (!allPresent) {
    if (!download) throw Error('Local LLM weights are missing or altered. Run npm run phishlens -- setup-models --download.');
    const remote = entry.path.slice('llama/'.length).split('/').map(encodeURIComponent).join('/');
    const url = 'https://huggingface.co/' + manifest.model_id + '/resolve/' + manifest.revision + '/' + remote;
    console.log('Downloading pinned public model asset: ' + remote);
    const response = await fetch(url, { signal: AbortSignal.timeout(10 * 60 * 1000) });
    if (!response.ok || !response.body) throw Error('Model download failed: HTTP ' + response.status);
    const reader = response.body.getReader(); let pending = new Uint8Array(0), total = 0;
    const full = createHash('sha256');
    for (const piece of pieces) {
      const bytes = new Uint8Array(piece.bytes); let filled = 0;
      while (filled < bytes.length) {
        if (!pending.length) { const next = await reader.read(); if (next.done) throw Error('Incomplete model download'); pending = next.value; }
        const take = Math.min(bytes.length - filled, pending.length);
        bytes.set(pending.subarray(0, take), filled); pending = pending.subarray(take); filled += take;
      }
      if (hash(bytes) !== piece.sha256) throw Error('Downloaded model failed its pinned hash');
      full.update(bytes); total += bytes.length;
      const dest = path.join(root, 'extension/model-assets', piece.path || entry.path);
      await mkdir(path.dirname(dest), { recursive: true }); await writeFile(dest, bytes);
    }
    const extra = await reader.read();
    if (pending.length || !extra.done || total !== entry.bytes || full.digest('hex') !== entry.sha256) throw Error('Downloaded model identity differs');
  }
  checked += entry.bytes;
}
console.log(JSON.stringify({ checked_model_files: manifest.files.length, checked_bytes: checked,
  model_id: manifest.model_id, revision: manifest.revision, uploaded_email: false }));

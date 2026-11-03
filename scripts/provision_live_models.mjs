// Reuse verified local model/runtime caches. No email or credential is uploaded.
import { readFile, mkdir, copyFile, writeFile, access, unlink } from 'node:fs/promises';
import { createReadStream } from 'node:fs';
import { createHash } from 'node:crypto';
import { patchTransformers } from './vendor_runtime_patch.mjs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const args = process.argv.slice(2);
if (args.length !== 2 || args[0] !== '--source-pilot') throw Error('Use --source-pilot <existing academic_pilot_v2 directory>');
const source = path.resolve(args[1]);
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const blockBytes = 4 * 1024 * 1024;
async function identity(file, chunked = false) {
  const full = createHash('sha256'), chunks = []; let bytes = 0;
  for await (const chunk of createReadStream(file, { highWaterMark: blockBytes })) {
    full.update(chunk); bytes += chunk.length;
    if (chunked) chunks.push({ bytes: chunk.length, sha256: digest(chunk) });
  }
  return { bytes, sha256: full.digest('hex'), ...(chunked ? { chunks } : {}) };
}
const prior = JSON.parse(await readFile(path.join(source, 'models/asset_manifest.json'), 'utf8'));
const files = [];
for (const entry of prior.files.filter(x => x.model === 'llm')) {
  const relative = entry.path.replaceAll('\\', '/');
  if (!relative.startsWith('models/llama/')) throw Error('Unexpected LLM source path');
  const src = path.resolve(source, relative);
  if (!src.startsWith(source + path.sep)) throw Error('Source path escapes the cache');
  const info = await identity(src, entry.bytes > blockBytes);
  if (info.sha256 !== entry.sha256 || info.bytes !== entry.bytes) throw Error('Existing model cache failed integrity: ' + relative);
  const modelPath = relative.slice('models/'.length);
  const dest = path.join(root, 'extension/model-assets', modelPath);
  await mkdir(path.dirname(dest), { recursive: true });
  let exists = false; try { await access(dest); exists = true; } catch { /* first provision */ }
  if (exists) {
    if ((await identity(dest)).sha256 !== info.sha256) throw Error('Provisioned model differs: ' + modelPath);
  } else await copyFile(src, dest);
  // Chrome's extension resource loader can allocate the entire resource in the
  // browser process. Serve large model data as independently verified 4 MB files.
  if (info.chunks) {
    let index = 0;
    for await (const chunk of createReadStream(src, { highWaterMark: blockBytes })) {
      const part = modelPath + '.part' + String(index).padStart(4, '0');
      await writeFile(path.join(root, 'extension/model-assets', part), chunk);
      info.chunks[index].path = part; index++;
    }
    // Remove only the verified generated duplicate; original cache stays intact.
    const expectedRoot = path.resolve(root, 'extension/model-assets') + path.sep;
    if (!path.resolve(dest).startsWith(expectedRoot)) throw Error('Unsafe generated-model cleanup path');
    await unlink(dest);
  }
  files.push({ path: modelPath, ...info });
}
const nodeModules = path.join(source, 'runtime/node_modules');
const vendor = path.join(root, 'extension/vendor/ml'); await mkdir(vendor, { recursive: true });
const vendorEntries = [
  ['@huggingface/transformers/dist/transformers.min.js', 'transformers.min.js'],
  ['onnxruntime-web/dist/ort-wasm-simd-threaded.jsep.mjs', 'ort-wasm-simd-threaded.jsep.mjs'],
  ['onnxruntime-web/dist/ort-wasm-simd-threaded.jsep.wasm', 'ort-wasm-simd-threaded.jsep.wasm'],
  ['onnxruntime-web/dist/ort-wasm-simd-threaded.asyncify.mjs', 'ort-wasm-simd-threaded.asyncify.mjs'],
  ['onnxruntime-web/dist/ort-wasm-simd-threaded.asyncify.wasm', 'ort-wasm-simd-threaded.asyncify.wasm'],
  ['@huggingface/transformers/LICENSE', 'LICENSE-transformers.txt'],
  ['@huggingface/transformers-structured-output/LICENSE', 'LICENSE-structured-output.txt']
];
const vendored = [];
for (const [src, dest] of vendorEntries) {
  let bytes = await readFile(path.join(nodeModules, src));
  if (dest === 'transformers.min.js') bytes = patchTransformers(bytes);
  await writeFile(path.join(vendor, dest), bytes);
  vendored.push({ path: 'vendor/ml/' + dest, bytes: bytes.length, sha256: digest(bytes) });
}
let structured = await readFile(path.join(nodeModules, '@huggingface/transformers-structured-output/dist/index.js'), 'utf8');
structured = structured.replaceAll('from "@huggingface/transformers"', 'from "./transformers.min.js"');
if (structured.includes('from "@huggingface/')) throw Error('Unresolved runtime package import');
await writeFile(path.join(vendor, 'structured-output.js'), structured);
vendored.push({ path: 'vendor/ml/structured-output.js', bytes: Buffer.byteLength(structured), sha256: digest(Buffer.from(structured)) });
const runtimeVersion = JSON.parse(await readFile(path.join(nodeModules, '@huggingface/transformers/package.json'))).version;
const structuredVersion = JSON.parse(await readFile(path.join(nodeModules, '@huggingface/transformers-structured-output/package.json'))).version;
const onnxVersion = JSON.parse(await readFile(path.join(nodeModules, 'onnxruntime-web/package.json'))).version;
// This npm distribution omits its MIT license file. Reuse Microsoft's license
// included with the locally installed ONNX Runtime distribution, unchanged.
const onnxLicense = await readFile(path.join(source, '../local_email/vendor/onnxruntime/LICENSE'));
await writeFile(path.join(vendor, 'LICENSE-onnxruntime.txt'), onnxLicense);
vendored.push({ path: 'vendor/ml/LICENSE-onnxruntime.txt', bytes: onnxLicense.length, sha256: digest(onnxLicense) });
const llamaLicense = await readFile(path.join(source, 'models/llama/LICENSE.txt'));
await writeFile(path.join(vendor, 'LICENSE-Llama3.2.txt'), llamaLicense);
vendored.push({ path: 'vendor/ml/LICENSE-Llama3.2.txt', bytes: llamaLicense.length, sha256: digest(llamaLicense) });
const manifest = { schema_version: 1, model_id: 'onnx-community/Llama-3.2-1B-Instruct-ONNX',
  revision: '14007543b6dc92de88daf96a9aa85d2f95ace6ef', dtype: 'q4f16', device: 'webgpu',
  files, runtime: { transformers: runtimeVersion, structured_output: structuredVersion, onnx: onnxVersion },
  vendored, total_model_bytes: files.reduce((n, x) => n + x.bytes, 0),
  note: 'Runtime code is packaged locally; provisioned weights are ignored by Git. Hashes are integrity checks, not signed publisher identity.' };
await writeFile(path.join(root, 'extension/ai/judge-assets.json'), JSON.stringify(manifest, null, 2) + '\n');
console.log(JSON.stringify({ model: manifest.model_id, model_bytes: manifest.total_model_bytes,
  model_files: files.length, runtime: manifest.runtime, executable_assets: vendored.length,
  provisioned: true, uploaded_email: false }, null, 2));

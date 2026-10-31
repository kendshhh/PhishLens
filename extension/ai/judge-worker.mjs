import { env, AutoTokenizer, AutoModelForCausalLM, random } from '../vendor/ml/transformers.min.js';
import { StructuredOutputProcessor } from '../vendor/ml/structured-output.js';
import { JUDGE_PROMPT, JUDGE_MODEL_ID, JUDGE_REVISION, judgeSchema, quoteOptions } from './judge-contract.mjs';

env.allowRemoteModels = false; env.allowLocalModels = true;
env.localModelPath = new URL('../model-assets/', import.meta.url).href;
env.useBrowserCache = false; env.useFSCache = false;
env.backends.onnx.wasm.wasmPaths = new URL('../vendor/ml/', import.meta.url).href;
env.backends.onnx.wasm.numThreads = 1; env.backends.onnx.wasm.proxy = false;
let loading, model, tokenizer, phase = 'initialization';
const chunkedEntries = new Map();
let lastProgress = 0;
function progress(jobId, stage, value) {
  if (performance.now() - lastProgress < 500 && value !== 1) return;
  lastProgress = performance.now(); self.postMessage({ type: 'progress', jobId, stage, value });
}
const sha = async bytes => [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(x => x.toString(16).padStart(2, '0')).join('');

async function verifyFiles(jobId) {
  const manifestResponse = await fetch(new URL('./judge-assets.json', import.meta.url));
  if (!manifestResponse.ok) throw Error('model_assets_missing');
  const manifest = await manifestResponse.json();
  if (manifest.model_id !== JUDGE_MODEL_ID || manifest.revision !== JUDGE_REVISION || manifest.files.length > 16) throw Error('model_identity_mismatch');
  let checked = 0;
  for (const entry of manifest.files) {
    if (typeof entry.path !== 'string' || !entry.path.startsWith('llama/') || entry.path.split('/').includes('..') ||
        !Number.isSafeInteger(entry.bytes) || entry.bytes <= 0) throw Error('invalid_model_manifest');
    const response = entry.chunks ? null : await fetch(new URL(entry.path, env.localModelPath));
    if (!entry.chunks && (!response.ok || !response.body)) throw Error('model_assets_missing');
    let bytesRead = 0;
    if (entry.chunks) {
      for (const part of entry.chunks) {
        const res = await fetch(new URL(part.path, env.localModelPath));
        if (!res.ok) throw Error('model_assets_missing');
        const block = await res.arrayBuffer();
        if (block.byteLength !== part.bytes || await sha(block) !== part.sha256) throw Error('model_integrity_failed');
        bytesRead += block.byteLength;
        progress(jobId, 'Verifying local LLM weights', (checked + bytesRead) / manifest.total_model_bytes);
      }
      chunkedEntries.set(new URL(entry.path, env.localModelPath).href, entry);
    } else {
      const bytes = await response.arrayBuffer(); bytesRead = bytes.byteLength;
      if (await sha(bytes) !== entry.sha256) throw Error('model_integrity_failed');
    }
    if (bytesRead !== entry.bytes) throw Error('model_integrity_failed');
    checked += bytesRead;
  }
  progress(jobId, 'Verified local LLM weights', 1);
  env.fetch = async (input, init) => {
    const entry = chunkedEntries.get(String(input));
    if (!entry) return fetch(input, init);
    let index = 0;
    const stream = new ReadableStream({
      async pull(controller) {
        if (index === entry.chunks.length) { controller.close(); return; }
        const part = entry.chunks[index++];
        const res = await fetch(new URL(part.path, env.localModelPath));
        if (!res.ok) throw Error('model_assets_missing');
        const bytes = await res.arrayBuffer();
        if (bytes.byteLength !== part.bytes || await sha(bytes) !== part.sha256) throw Error('model_integrity_failed');
        controller.enqueue(new Uint8Array(bytes));
      }
    });
    return new Response(stream, { headers: { 'Content-Length': String(entry.bytes) } });
  };
}

async function ready(jobId) {
  if (!loading) loading = (async () => {
    if (!navigator.gpu) throw Error('webgpu_unavailable');
    const adapter = await navigator.gpu.requestAdapter();
    if (!adapter || !adapter.features.has('shader-f16')) throw Error('webgpu_fp16_unavailable');
    await verifyFiles(jobId);
    phase = 'tokenizer_load';
    tokenizer = await AutoTokenizer.from_pretrained('llama', { local_files_only: true });
    phase = 'model_load';
    model = await AutoModelForCausalLM.from_pretrained('llama', {
      device: 'webgpu', dtype: 'q4f16', local_files_only: true,
      progress_callback: () => progress(jobId, 'Preparing the local LLM', null)
    });
    phase = 'decoder_warmup'; StructuredOutputProcessor.warmup(tokenizer);
    self.postMessage({ type: 'ready', jobId });
  })().catch(error => { loading = undefined; throw error; });
  await loading;
}

self.onmessage = async ({ data }) => {
  const { jobId, primary } = data; let inputs, output;
  try {
    await ready(jobId);
    phase = 'prompt_tokenization';
    const options = quoteOptions(primary);
    if (!options.length) throw Error('no_judge_evidence');
    const payload = { preliminary: primary.alert ? 'suspicious' : 'below_threshold',
      text: primary.analysis_text, quotes: options };
    inputs = tokenizer.apply_chat_template([
      { role: 'system', content: JUDGE_PROMPT }, { role: 'user', content: JSON.stringify(payload) }
    ], { add_generation_prompt: true, return_dict: true });
    const inputTokens = inputs.input_ids.dims.at(-1);
    if (inputTokens > 1536) throw Error('judge_input_too_long_without_truncation');
    const seedPassed = typeof random?.seed === 'function';
    if (seedPassed) random.seed(42);
    phase = 'structured_decoder';
    const processor = new StructuredOutputProcessor(tokenizer, { type: 'json_schema', json_schema: judgeSchema(options, primary.alert) });
    phase = 'generation';
    output = await model.generate({ ...inputs, max_new_tokens: 64, do_sample: false, temperature: 0,
      eos_token_id: tokenizer.eos_token_id, logits_processor: processor });
    const generated = output.tolist()[0].slice(inputTokens);
    self.postMessage({ type: 'result', jobId, raw: tokenizer.decode(generated, { skip_special_tokens: true }),
      inputTokens, generatedTokens: generated.length, seedPassed });
  } catch (error) {
    const known = new Set(['webgpu_unavailable', 'webgpu_fp16_unavailable', 'model_assets_missing', 'model_identity_mismatch',
      'invalid_model_manifest', 'model_integrity_failed', 'no_judge_evidence', 'judge_input_too_long_without_truncation']);
    self.postMessage({ type: 'failure', jobId, code: known.has(error?.message) ? error.message : 'local_judge_failed',
      diagnostic: { phase, name: error?.name, message: String(error?.message).slice(0, 300) } });
  } finally {
    for (const tensor of Object.values(inputs || {})) tensor?.dispose?.();
    output?.dispose?.();
  }
};

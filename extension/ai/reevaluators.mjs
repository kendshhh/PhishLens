import { featureCounts, mapScore } from './core.mjs';
import { analyzeLocal } from './local-analyzer.mjs';

export function vectorizePrepared(text, artifact) {
  const size = artifact.blocks.reduce((n, b) => n + b.idf.length, 0);
  const vector = new Float64Array(size); let offset = 0;
  for (const block of artifact.blocks) {
    const counts = featureCounts(text, block); let norm = 0;
    for (const [index, count] of counts) {
      const value = (1 + Math.log(count)) * block.idf[index];
      vector[offset + index] = value; norm += value * value;
    }
    norm = Math.sqrt(norm);
    if (norm) for (const index of counts.keys()) vector[offset + index] /= norm;
    offset += block.idf.length;
  }
  return vector;
}

export function scoreAuxiliary(vector, model) {
  if (model.feature_count !== vector.length || model.classes?.join(',') !== '0,1' || model.positive_label !== 'phishing') {
    throw Error('Invalid reevaluator feature or label mapping.');
  }
  let raw = 0;
  if (model.kind === 'krr') {
    if (model.kernel !== 'linear' || model.coefficients?.length !== vector.length || model.intercept !== 0) {
      throw Error('Invalid linear-kernel KRR artifact.');
    }
    for (let i = 0; i < vector.length; i++) raw += vector[i] * model.coefficients[i];
  } else if (model.kind === 'lightgbm') {
    if (model.objective !== 'binary_sigmoid_1' || !Array.isArray(model.trees)) throw Error('Unsupported LightGBM convention.');
    for (const tree of model.trees) {
      let node = tree, steps = 0;
      while (node.split_index !== undefined) {
        if (++steps > 16 || node.decision_type !== '<=' || !Number.isInteger(node.split_feature) ||
            node.split_feature < 0 || node.split_feature >= vector.length || !Number.isFinite(node.threshold)) {
          throw Error('Invalid or unsupported LightGBM tree.');
        }
        node = vector[node.split_feature] <= node.threshold ? node.left_child : node.right_child;
      }
      if (!Number.isFinite(node.leaf_value)) throw Error('Invalid LightGBM leaf.');
      raw += node.leaf_value;
    }
  } else throw Error('Unknown reevaluator.');
  const score = mapScore(raw, model.mapping);
  if (!Number.isFinite(raw) || !Number.isFinite(score) || !Number.isFinite(model.cutoff)) throw Error('Invalid reevaluator result.');
  return { model_id: model.model_id, kind: model.kind, raw_margin: raw, score,
    alert: raw >= model.cutoff, cutoff: model.cutoff, threshold_score: mapScore(model.cutoff, model.mapping), valid: true };
}

export function createReevaluator({ getBasis = () => analyzeLocal.getAssets(), fetchImpl = fetch } = {}) {
  let pending;
  async function load() {
    const base = new URL('./reevaluators/', import.meta.url);
    const response = await fetchImpl(new URL('manifest.json', base), { signal: AbortSignal.timeout(10000) });
    if (!response.ok) throw Error('Reevaluator manifest is unavailable.');
    const manifest = await response.json();
    const { artifact, contract } = await getBasis();
    if (manifest.basis_sha256 !== contract.model_sha256) throw Error('Reevaluators use a different TF-IDF basis.');
    const models = [];
    for (const kind of ['krr', 'lightgbm']) {
      const entry = manifest.models[kind];
      if (entry.file !== kind + '.json') throw Error('Invalid reevaluator asset path.');
      const file = await fetchImpl(new URL(entry.file, base), { signal: AbortSignal.timeout(10000) });
      if (!file.ok) throw Error('Reevaluator model is unavailable.');
      const bytes = await file.arrayBuffer();
      const sha = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(x => x.toString(16).padStart(2, '0')).join('');
      if (sha !== entry.sha256 || bytes.byteLength !== entry.bytes) throw Error('Reevaluator integrity check failed.');
      const model = JSON.parse(new TextDecoder().decode(bytes));
      if (model.kind !== kind || model.basis_sha256 !== contract.model_sha256) throw Error('Reevaluator identity mismatch.');
      models.push({ model, sha256: sha });
    }
    return { artifact, models };
  }
  return async primary => {
    if (!pending) pending = load().catch(error => { pending = undefined; throw error; });
    const { artifact, models } = await pending;
    const vector = vectorizePrepared(primary.analysis_text, artifact);
    return [{ kind: 'tfidf', model_id: primary.model_id, sha256: primary.model_sha256,
      raw_margin: primary.raw_margin, score: primary.score, threshold_score: primary.alert_threshold_score,
      cutoff: 0, alert: primary.alert, valid: true }, ...models.map(({ model, sha256 }) => ({ ...scoreAuxiliary(vector, model), sha256 }))];
  };
}

export const reevaluate = createReevaluator();

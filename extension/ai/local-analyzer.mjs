import { analyze } from './core.mjs';

export const MODEL_SHA256 = 'a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c';

function validArtifact(artifact) {
  if (!Number.isFinite(artifact.intercept) || artifact.blocks?.length !== 2) return false;
  return artifact.blocks.every(block => {
    const size = block.idf?.length;
    const ids = Object.values(block.vocabulary ?? {});
    return ['word', 'char_wb'].includes(block.analyzer) && size > 0 &&
      block.coefficient?.length === size && ids.length === size &&
      new Set(ids).size === size && ids.every(i => Number.isInteger(i) && i >= 0 && i < size) &&
      block.idf.every(x => Number.isFinite(x) && x > 0) && block.coefficient.every(Number.isFinite);
  });
}

// Static packaged assets only. There is no network inference or fallback provider.
export function createLocalAnalyzer({ fetchImpl = fetch, cryptoImpl = globalThis.crypto,
  baseUrl = new URL('./', import.meta.url) } = {}) {
  let pending;
  async function load() {
    const get = async name => {
      const response = await fetchImpl(new URL(name, baseUrl).href, { signal: AbortSignal.timeout(10000) });
      if (!response.ok) throw Error('Packaged model files could not be read. Reload the extension.');
      return response;
    };
    const [modelResponse, contractResponse] = await Promise.all([get('tfidf_v12a.json'), get('contract.json')]);
    const bytes = await modelResponse.arrayBuffer();
    const digest = [...new Uint8Array(await cryptoImpl.subtle.digest('SHA-256', bytes))]
      .map(x => x.toString(16).padStart(2, '0')).join('');
    const contract = await contractResponse.json();
    if (digest !== MODEL_SHA256 || contract.model_sha256 !== MODEL_SHA256 ||
        contract.model_id !== 'word_plus_char_wb_C1p0' || contract.system !== 'tfidf_v12a' ||
        contract.alert_mode !== 'raw_margin' || contract.alert_threshold !== 0 ||
        contract.mapping?.kind !== 'margin_sigmoid' ||
        contract.mapping?.slope !== 1.6158795082744162 ||
        contract.mapping?.intercept !== 2.0617153419475205) {
      throw Error('Model integrity check failed. Reload a verified PhishLens package.');
    }
    const artifact = JSON.parse(new TextDecoder().decode(bytes));
    if (!validArtifact(artifact)) throw Error('Invalid packaged model. Reload the extension.');
    return { artifact, contract };
  }
  async function getAssets() {
    if (!pending) pending = load().catch(error => { pending = undefined; throw error; });
    return pending;
  }
  const evaluate = async text => {
    const { artifact, contract } = await getAssets();
    const result = analyze({ text }, artifact, contract);
    if (!result.valid || !result.verification.quote_spans_valid || !result.matched_features) {
      throw Error('Unable to assess: the selection has no usable model features. Select the complete visible email text.');
    }
    // Lowercasing can expand Unicode characters and shift frozen attribution
    // offsets. Keep only drivers whose quoted word tokens still match the feature.
    const before = result.model_drivers.length;
    result.model_drivers = result.model_drivers.filter(driver =>
      (driver.quote.toLowerCase().match(/[\p{L}\p{N}_]{2,}/gu) || []).join(' ') === driver.feature);
    result.verification.model_feature_quotes_checked = result.model_drivers.length;
    result.verification.model_feature_quotes_dropped = before - result.model_drivers.length;
    return result;
  };
  evaluate.getAssets = getAssets;
  return evaluate;
}

export const analyzeLocal = createLocalAnalyzer();

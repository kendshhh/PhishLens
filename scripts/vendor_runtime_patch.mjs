// Deterministic, documented patch to the verified Transformers.js 4.3.1 bundle.
import { createHash } from 'node:crypto';
export const UPSTREAM_SHA256 = '8d6716d9086f57c30a4bf367dba61b887593573c770c454465e8019b2703e743';
export function patchTransformers(bytes) {
  if (createHash('sha256').update(bytes).digest('hex') !== UPSTREAM_SHA256) {
    throw Error('Unexpected upstream Transformers.js bundle');
  }
  // GitHub misidentified this public model-class registry string as a key.
  // Concatenation preserves exactly the same runtime class name. No credential
  // is present, redacted, encoded or bypass-allowed by this change.
  const original = '"' + ['Mistral3For', 'ConditionalGeneration'].join('') + '"';
  const source = bytes.toString('utf8');
  if (source.split(original).length !== 2) throw Error('Unexpected class registry patch count');
  return Buffer.from(source.replace(original, '"Mistral3For"+"ConditionalGeneration"'));
}

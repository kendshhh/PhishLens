import { analyzeLocal } from './local-analyzer.mjs';
import { requestJudge } from './judge-client.mjs';
import { reevaluate } from './reevaluators.mjs';
import { releaseWorkflow, validateJudge } from './judge-contract.mjs';

export function createWorkflow({ analyze = analyzeLocal, judge = requestJudge, evaluateAgain = reevaluate } = {}) {
  return async (text, { jobId, onProgress = async () => {}, isCurrent = () => true } = {}) => {
    const start = performance.now();
    const requireCurrent = () => { if (!isCurrent()) throw Error('Scan cancelled or superseded.'); };
    const primary = await analyze(text); requireCurrent();
    await onProgress('Local LLM judge', primary); requireCurrent();
    let audit;
    try {
      const response = await judge(primary, jobId); requireCurrent();
      if (!response?.ok) audit = { valid: false, code: response?.code || 'judge_unavailable' };
      else audit = { ...validateJudge(response.raw, primary, {
        inputTokens: response.inputTokens, generatedTokens: response.generatedTokens
      }), seed_passed_to_runtime: response.seedPassed === true };
    } catch {
      audit = { valid: false, code: 'invalid_judge_output' };
    }
    requireCurrent();
    await onProgress('TF-IDF + KRR + LightGBM reevaluation', primary); requireCurrent();
    let checks = [], reevaluatorError;
    try { checks = await evaluateAgain(primary); }
    catch { reevaluatorError = 'The reevaluator models could not be loaded or validated.'; }
    requireCurrent();
    const result = releaseWorkflow(primary, audit, checks);
    result.workflow.elapsed_ms = performance.now() - start;
    if (reevaluatorError) result.workflow.reevaluator_error = reevaluatorError;
    return result;
  };
}

export const analyzeWithReview = createWorkflow();

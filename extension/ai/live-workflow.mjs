import { analyzeLocal } from './local-analyzer.mjs';
import { requestJudge } from './judge-client.mjs';
import { reevaluate } from './reevaluators.mjs';
import { releaseWorkflow, validateJudge } from './judge-contract.mjs';
import { retrieveGuidance } from './retrieval.mjs';

export function createWorkflow({ analyze = analyzeLocal, judge = requestJudge, evaluateAgain = reevaluate } = {}) {
  return async (text, { jobId, onProgress = async () => {}, isCurrent = () => true } = {}) => {
    const start = performance.now();
    const requireCurrent = () => { if (!isCurrent()) throw Error('Scan cancelled or superseded.'); };
    const primary = await analyze(text); requireCurrent();
    await onProgress('Retrieving local guidance', primary); requireCurrent();
    let retrieval;
    try {
      retrieval = retrieveGuidance(primary.analysis_text);
    } catch {
      // Retrieval is advisory context only; an index problem must not prevent
      // the established TF-IDF/judge/reevaluator flow from completing.
      retrieval = { version: 'phishlens-email-guidance-1', query_terms: 0, documents: [], error: 'retrieval_unavailable' };
    }
    await onProgress('Local LLM judge', primary); requireCurrent();
    let audit, usedRetrievalSources = [];
    try {
      const judgeInput = { ...primary, local_guidance: retrieval };
      const response = await judge(judgeInput, jobId); requireCurrent();
      if (!response?.ok) audit = { valid: false, code: response?.code || 'judge_unavailable' };
      else {
        audit = { ...validateJudge(response.raw, primary, {
          inputTokens: response.inputTokens, generatedTokens: response.generatedTokens
        }), seed_passed_to_runtime: response.seedPassed === true };
        usedRetrievalSources = Array.isArray(response.retrievalSources)
          ? response.retrievalSources.filter(source => retrieval.documents.some(doc => doc.id === source.id))
          : retrieval.documents.map(({ id, title }) => ({ id, title }));
      }
    } catch {
      audit = { valid: false, code: 'invalid_judge_output' };
    }
    audit.retrieval = {
      status: retrieval.error ? 'unavailable' : audit.valid !== true ? 'judge_unavailable' :
        usedRetrievalSources.length ? 'retrieved' : retrieval.documents.length ? 'omitted_for_context_budget' : 'no_match',
      corpus_version: retrieval.version,
      sources: usedRetrievalSources.map(({ id, title }) => {
        const matched = retrieval.documents.find(doc => doc.id === id);
        return { id, title: title || matched?.title || id, score: matched ? Number(matched.score.toFixed(4)) : 0 };
      }),
    };
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

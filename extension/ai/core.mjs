import {observations} from './observations.mjs';

const PYSPACE=/[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+/u;
const PYSPACES=/[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+/gu;
const sigmoid=x=>x>=0?1/(1+Math.exp(-x)):Math.exp(x)/(1+Math.exp(x));
export function preparePlain(text){
 if(typeof text!=='string'||text.length>30_000)throw Error('Text must be a string of at most 30,000 characters.');
 let cleaned=text.replace(/\b[A-Z0-9._%+\-]+@([A-Z0-9.\-]+\.[A-Z]{2,})\b/gi,'[EMAIL]@$1')
  .replace(/(?<![\p{L}\p{N}_/])(?:\+?\p{Nd}[ ()\-.]*){9,15}(?![\p{L}\p{N}_])/gu,'[PHONE]')
  .replace(/(?<![\p{L}\p{N}_])\p{Nd}{6,}(?![\p{L}\p{N}_])/gu,'[NUMBER]').replace(PYSPACES,' ');
 cleaned=cleaned.replace(/^ +| +$/g,'');const chars=Array.from(cleaned);
 return {text:chars.length>2300?chars.slice(0,2000).join('')+chars.slice(-300).join(''):cleaned,truncated:chars.length>2300};
}
export function featureCounts(text,block){
 const lower=text.toLowerCase(),counts=new Map();
 const add=feature=>{if(Object.hasOwn(block.vocabulary,feature)){const id=block.vocabulary[feature];counts.set(id,(counts.get(id)||0)+1);}};
 if(block.analyzer==='word'){
  const words=lower.match(/[\p{L}\p{N}_]{2,}/gu)||[];
  for(let i=0;i<words.length;i++){add(words[i]);if(i)add(words[i-1]+' '+words[i]);}
 }else if(block.analyzer==='char_wb'){
  for(const word of lower.split(PYSPACE).filter(Boolean)){
   const padded=Array.from(' '+word+' '),len=padded.length;
   for(let n=block.ngram_range[0];n<=block.ngram_range[1];n++){
    let offset=0;add(padded.slice(0,n).join(''));
    while(offset+n<len){offset++;add(padded.slice(offset,offset+n).join(''));}
    if(offset===0)break;
   }
  }
 }else throw Error('Unsupported feature analyzer.');
 return counts;
}
export function rawScore(text,artifact){
 const blocks=artifact.blocks||[{...artifact,analyzer:'word',ngram_range:[1,2]}];
 let margin=artifact.intercept;const parts=[];let nonzero=0;
 for(let b=0;b<blocks.length;b++){
  const block=blocks[b],counts=featureCounts(text,block);let norm=0;const values=[];
  for(const [i,count] of counts){const value=(1+Math.log(count))*block.idf[i];norm+=value*value;values.push([i,value]);}
  norm=Math.sqrt(norm);
  for(const [i,value] of values){const contribution=value/norm*block.coefficient[i];margin+=contribution;parts.push({block:b,index:i,contribution});nonzero++;}
 }
 if(!Number.isFinite(margin))throw Error('Nonfinite classifier output.');
 return {margin,parts,nonzero};
}
export function mapScore(margin,mapping){
 let x=margin;
 if(mapping.kind==='frozen_probability_sigmoid'){const p=Math.max(mapping.epsilon,Math.min(1-mapping.epsilon,sigmoid(margin)));x=Math.log(p/(1-p));}
 return sigmoid(mapping.slope*x+mapping.intercept);
}
const featureNames=new WeakMap();
function modelDrivers(text,artifact,parts){
 const blocks=artifact.blocks||[{...artifact,analyzer:'word'}];
 if(!featureNames.has(artifact))featureNames.set(artifact,blocks.map(b=>{const a=[];for(const [name,i] of Object.entries(b.vocabulary))a[i]=name;return a;}));
 const names=featureNames.get(artifact);
 const words=[...text.toLowerCase().matchAll(/[\p{L}\p{N}_]{2,}/gu)];const output=[];
 for(const p of [...parts].sort((a,b)=>Math.abs(b.contribution)-Math.abs(a.contribution))){
  if(blocks[p.block].analyzer!=='word')continue;
  const feature=names[p.block][p.index];let match;
  for(let i=0;i<words.length;i++){
   if(words[i][0]===feature){match=[words[i].index,words[i].index+words[i][0].length];break;}
   if(i&&words[i-1][0]+' '+words[i][0]===feature){match=[words[i-1].index,words[i].index+words[i][0].length];break;}
  }
  if(match)output.push({feature,contribution:p.contribution,direction:p.contribution>=0?'toward_phishing':'away_from_phishing',quote:text.slice(...match),start:match[0],end:match[1],offset_unit:'UTF-16_code_units',basis:'exact_linear_margin_contribution_not_proof_of_deception'});
  if(output.length===3)break;
 }
 return output;
}
export function analyzePrepared(text,artifact,system){
 const started=performance.now();if(typeof text!=='string'||!text.trim())throw Error('No usable selected text.');
 const inferenceStart=performance.now(),raw=rawScore(text,artifact),score=mapScore(raw.margin,system.mapping);
 if(!Number.isFinite(score)||score<0||score>1||!Number.isFinite(system.alert_threshold))throw Error('Invalid score or decision contract.');
 const alert=system.alert_mode==='raw_margin'?raw.margin>=system.alert_threshold:score>=system.alert_threshold;
 const modelMs=performance.now()-inferenceStart;
 const evidence=observations(text),drivers=modelDrivers(text,artifact,raw.parts),actions=[...new Set(evidence.map(e=>e.action))].slice(0,3);
 if(!actions.length)actions.push('Verify an unexpected sensitive request using a website or contact method you already know.');
 const limitations=['This assessment covers the supplied text, not authenticated sender identity or unseen attachments.','The percentage is a research-calibrated model score; it is not a guarantee of your inbox probability.'];
 let assessment=alert?'The classifier flags this text for review.':'The classifier does not cross its alert threshold. This does not establish that the email is genuine.';
 assessment+=evidence.length?' Review the observations and their context before acting.':' A specific deceptive request was not independently established from the available text.';
 for(const item of [...evidence,...drivers])if(text.slice(item.start,item.end)!==item.quote)throw Error('Unsupported evidence span.');
 const result={schema_version:'phishlens-tfidf-v12a-1',system:system.system,model_id:system.model_id,model_sha256:system.model_sha256,valid:true,alert,verdict:alert?'suspicious':'no_strong_indicators',raw_margin:raw.margin,attribution_sum:artifact.intercept+raw.parts.reduce((sum,p)=>sum+p.contribution,0),score,risk_percent:score*100,alert_threshold:system.alert_threshold,alert_threshold_space:system.alert_mode,assessment,evidence,model_drivers:drivers,actions,limitations,explanation_origin:'deterministic_local_software_observations_and_exact_linear_contributions',analysis_text:text,verification:{schema_valid:true,quote_spans_valid:true,evidence_checked:evidence.length,model_feature_quotes_checked:drivers.length,sender_authenticated:false},matched_features:raw.nonzero,model_ms:modelMs};
 result.alert_threshold_score=system.alert_mode==='raw_margin'?mapScore(system.alert_threshold,system.mapping):system.alert_threshold;
 result.workflow_ms=performance.now()-started;return result;
}
export function analyze(input,artifact,system){
 if(!input||typeof input.text!=='string')throw Error('A text field is required.');
 // User-facing input is already visible plain selected text. MIME/HTML parsing
 // remains dataset preparation or a separately verified extension capture step.
 if(/<(?:html|body|div|p|a|table|span|br|head|style|script|h[1-6]|img)\b/i.test(input.text))throw Error('Provide visible plain text; raw HTML is not supported by this interface.');
 const prepared=preparePlain(input.text);const result=analyzePrepared(prepared.text,artifact,system);result.input_truncated=prepared.truncated;return result;
}

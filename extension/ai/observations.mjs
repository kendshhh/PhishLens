// Deterministic software observations. Never presented as hidden model reasoning.
export const VERSION='evidence-advice-v1';
const RULES={
 sensitive:{priority:10,observation:'The text directs the reader to provide or enter sensitive information.',why:'Passwords, payment details and verification codes can grant access or authorise an action. A request to disclose them needs independent verification.',action:'Do not send passwords or verification codes in a reply or to an unsolicited requester. Open the service through your usual app or a known address instead.'},
 pressure:{priority:9,observation:'The text connects an account-access consequence with a requested action.',why:'A threat of lost access can push a reader to act before checking the request. Legitimate services can also send urgent notices, so urgency does not establish phishing by itself.',action:'Check the account status through the app or website you normally use before following the requested action.'},
 funds:{priority:8,observation:'The text offers access to funds in exchange for the reader\'s assistance or personal details.',why:'An unexpected financial opportunity can lead to disclosure of identity details or later payment demands. The text alone does not establish that the money or the claimed sender exists.',action:'Verify the person and the financial claim independently. Do not pay an advance fee or send identity documents based only on this message.'},
 payment:{priority:7,observation:'The text requests a payment or transfer of funds.',why:'An incorrect recipient or a fabricated payment request could cause financial loss. A payment request alone is not proof of fraud.',action:'Confirm the invoice, recipient and amount through a contact method or payment workflow you already trust before sending money.'},
 link:{priority:5,observation:'The text includes a link alongside a sign-in, identity or account-update request.',why:'Following a supplied link for a sensitive action can take the reader outside their usual trusted workflow. The destination has not been opened or authenticated here.',action:'Navigate to the service independently and check whether the same request appears there. Do not use the message link as proof of identity.'},
 code:{priority:3,observation:'The text describes delivery or use of a security code.',why:'Code delivery and a short expiry can be normal parts of a user-initiated action. They do not alone establish phishing or prove that the sender is authentic.',action:'Check whether you initiated the action. Use any code only in the legitimate workflow you opened; if unexpected, review the account independently without approving the request.'},
 protective:{priority:2,observation:'The text contains an instruction not to disclose sensitive information.',why:'This is a protective instruction rather than a request to send the information. A warning can still appear inside a deceptive message, so it is not an authenticity guarantee.',action:'Keep the information private and check any separate request in the message through a known channel.'},
 attachment:{priority:1,observation:'The text refers to an attachment or attached document.',why:'Only the selected text was analysed. The contents, file type and safety of any attachment have not been checked.',action:'Confirm that you expected the document and verify an unexpected request with the sender through an established contact method before opening it.'},
 work:{priority:1,observation:'The text discusses a work event, scheduling or a submission deadline.',why:'An organisational deadline is different from a threat that requires credentials or payment. This topic does not itself authenticate the sender or any separate request.',action:'Check whether the notice fits a workshop, meeting or project you recognise. Verify any unexpected sensitive action through the organiser or your existing work channel.'}
};
const NEG=/(?:\bdo\s+not|\bdon['’]t|\bnever|\bshould\s+not|\bmust\s+not|\bnot\s+to)\s+(?:[a-z]+\s+){0,3}$/i;
const REPORTED=/\b(?:beware|example of (?:a )?(?:scam|phishing)|phishing (?:example|training)|quoted (?:scam|message)|scammer (?:asks|requested)|report(?:ed|ing) (?:a |the )?(?:scam|phishing))\b/i;
const PRIVATE=/\b\d{4,}\b|\b(?=[A-Z0-9]{6}\b)(?=[A-Z0-9]*[0-9])(?=[A-Z0-9]*[A-Z])[A-Z0-9]{6}\b/;
function segments(text){
 const out=[];let start=0;
 // A boundary at sentence punctuation is conservative; URL dots do not end a clause.
 const re=/[.!?;](?=\s|$)|\n+/gu;let m;
 while((m=re.exec(text))){const end=m.index+m[0].length;if(end>start)out.push({start,end,text:text.slice(start,end)});start=end;}
 if(start<text.length)out.push({start,end:text.length,text:text.slice(start)});
 return out;
}
function safeExcerpt(text,start,end){
 let value=text.slice(start,end);const left=value.search(/\S/u);if(left<0)return null;start+=left;end=start+value.trim().length;value=text.slice(start,end);
 // Do not unnecessarily echo codes/long numbers. Retain only a meaningful exact prefix.
 const secret=PRIVATE.exec(value);if(secret){end=start+secret.index;value=text.slice(start,end).trimEnd();end=start+value.length;}
 if(value.length<8||!/[A-Za-z]/.test(value))return null;
 return {start,end,quote:value,offset_unit:'UTF-16_code_units'};
}
export function observations(text){
 if(typeof text!=='string')throw Error('Text string required.');
 const found=new Map();
 function add(type,segment,match=null){
  if(found.has(type))return;
  const start=segment.start+(match?.index??0),end=match?start+match[0].length:segment.end;
  const excerpt=safeExcerpt(text,start,end);if(!excerpt)return;
  found.set(type,{type,...excerpt,...RULES[type],basis:'software_text_observation_not_model_attribution'});
 }
 for(const s of segments(text)){
  const reported=REPORTED.test(s.text);
  const protect=/\b(?:do\s+not|don['’]t|never|should\s+not|must\s+not|not\s+to)\s+(?:[a-z]+\s+){0,3}(?:share|disclose|send|tell|reveal|forward|give)\b[^.!?;]{0,65}\b(?:password|pin|code|passcode|credentials?|card details|account details)\b/i.exec(s.text);
  if(protect)add('protective',s,protect);
  const request=/\b(?:send|share|reply\s+with|provid(?:e|ing)|disclos(?:e|ing)|tell|reveal|forward|enter(?:ing)?|submit|give)\b[^.!?;]{0,70}\b(?:password|pin|verification\s+code|security\s+code|one[- ]time\s+(?:code|passcode)|passcode|credentials?|card\s+(?:number|details)|account\s+(?:number|details))\b/ig;
  let m;
  while((m=request.exec(s.text))){
   const before=s.text.slice(0,m.index);
   const established=/\b(?:already[- ]open|already opened|existing\s+(?:banking\s+)?app|app\s+(?:flow|screen|session)\s+you\s+(?:opened|initiated)|screen\s+you\s+already\s+opened)\b/i.test(s.text);
   if(!NEG.test(before)&&!reported&&!protect?.[0].includes(m[0])&&!established)add('sensitive',s,m);
  }
  const code=/\b(?:verification code|security (?:code|passcode)|one[- ]time (?:code|passcode)|confirmation code|authorisation token|authorization token)\b/i.exec(s.text);
  if(code)add('code',s,code);
  const pressure=/\b(?:account|access|profile|service|membership)\b[^.!?;]{0,100}\b(?:suspend(?:ed)?|disable[ds]?|closed?|terminat(?:ed|ion)|restrict(?:ed)?|locked?)\b/i.exec(s.text);
  if(pressure&&!reported&&!/\b(?:not|never)\s+(?:be\s+)?(?:suspended|disabled|closed|locked)\b/i.test(s.text)&&/\b(?:unless|must|within|immediate|verify|confirm|update|prevent)\b/i.test(text))add('pressure',s,pressure);
  const payment=/\b(?:pay|wire|transfer|remit|send)\s+(?:(?:the|this|a|an|your|these)\s+)?(?:invoice|payment|money|funds|[$£€¥])|\b(?:make|process|complete)\s+(?:(?:the|this|a|an|your)\s+)?payment\b/i.exec(s.text);
  if(payment&&!reported&&!NEG.test(s.text.slice(0,payment.index)))add('payment',s,payment);
  const attachment=/\b(?:attached|attachment|enclosed (?:file|document)|PDF attachment)\b/i.exec(s.text);
  if(attachment)add('attachment',s,attachment);
  const work=/\b(?:workshop|conference|presentation|meeting|submission deadline|agenda|schedule)\b/i.exec(s.text);
  if(work)add('work',s);
 }
 const url=/https?:\/\/[^\s<>"']+/i.exec(text);
 if(url&&/\b(?:verify (?:your )?(?:identity|account|login)|confirm (?:your )?(?:credentials|identity|account)|(?:log|sign)[ -]?in|update (?:your )?(?:account|payment|billing)|enter.{0,20}(?:password|pin))\b/i.test(text)){
  let host;try{host=new URL(url[0]).hostname;}catch{}
  if(host){const at=text.indexOf(host,url.index);if(at>=0)add('link',{start:at,end:at+host.length,text:host});}
 }
 if(/\b(?:million|inheritance|beneficiary|concealed.{0,20}fund|claim.{0,30}(?:money|fund))\b/i.test(text)&&/\b(?:assist|assistance|share the|commission|full name|private telephone|passport|beneficiary)\b/i.test(text)){
  const s=segments(text).find(s=>/\b(?:million|inheritance|beneficiary|fund)\b/i.test(s.text));if(s)add('funds',s);
 }
 let selected=[...found.values()].sort((a,b)=>b.priority-a.priority||a.start-b.start).slice(0,3);
 if(found.has('protective')&&selected.some(x=>x.type==='sensitive')&&!selected.some(x=>x.type==='protective'))selected=[...selected.slice(0,2),found.get('protective')];
 return selected.map(({priority,...x})=>x);
}
export function explain(text,prediction){
 if(typeof text!=='string'||!prediction||typeof prediction.valid!=='boolean')throw Error('Text and observed prediction required.');
 const evidence=observations(text),adverse=evidence.filter(x=>['sensitive','pressure','funds','payment','link'].includes(x.type));
 const valid=prediction.valid===true;
 if(!Number.isFinite(prediction.score)||prediction.score<0||prediction.score>1||!Number.isFinite(prediction.threshold))throw Error('Finite frozen probability and threshold required.');
 const alert=valid&&prediction.score>=prediction.threshold;
 const degenerate=prediction.calibration_degenerate===true;
 const percentage=valid&&!degenerate?prediction.score*100:null;
 const display=percentage===null?'Not informative':percentage>0&&percentage<.1?'<0.1%':percentage>99.9&&percentage<100?'>99.9%':(Math.round(percentage*10)/10)+'%';
 let assessment;
 if(!valid)assessment='The model could not produce a usable classification. No reliable model risk estimate is available for this selection.';
 else if(degenerate)assessment='The model returned a classification, but its frozen calibration maps every usable answer to the same score. That score cannot distinguish messages reliably; use the text observations below without treating this model result as a safety assurance.';
 else if(alert&&adverse.length)assessment=`The model assigns a text risk score of ${display} and flags this selection for caution. ${adverse[0].observation}`;
 else if(alert)assessment=`The model assigns a text risk score of ${display} and flags this selection for caution. A specific deceptive request could not be confirmed from the available text, so the model alert needs context rather than an invented justification.`;
 else if(adverse.length)assessment=`The model assigns a text risk score of ${display}, below its alert threshold. The text nevertheless contains a request that deserves review: ${adverse[0].observation.charAt(0).toLowerCase()+adverse[0].observation.slice(1)}`;
 else if(evidence.some(x=>x.type==='code'))assessment=`The model assigns a text risk score of ${display}, below its alert threshold. The text describes code delivery, which can be part of a legitimate action; check whether you initiated that action and keep the code private.`;
 else if(evidence.some(x=>x.type==='work'))assessment=`The model assigns a text risk score of ${display}, below its alert threshold. The selection concerns a work event or scheduling; the visible deadline alone does not establish a deceptive request for credentials or payment.`;
 else assessment=`The model assigns a text risk score of ${display}, below its alert threshold. No clear directed request for sensitive information or payment was identified in this selection; that does not prove that the full message or its sender is safe.`;
 const actions=[...new Set(evidence.map(e=>e.action))].slice(0,3);
 if(!actions.length)actions.push('Read the full message and verify an unexpected sensitive request through a contact method you already know before acting.');
 const result={version:VERSION,explanation_origin:'deterministic_local_software_observations',
  classifier:{valid,score:prediction.score,threshold:prediction.threshold,alert:Number(alert),benchmark_verdict:alert?'phishing':'safe'},
  presentation:{status:!valid?'analysis_unavailable':degenerate?'uninformative_model_score':'available',verdict:!valid?'Analysis unavailable':degenerate?'Model score uninformative':alert?'Likely phishing':'No alert from this model',risk_percent:percentage,risk_display:display},
  assessment,evidence,actions,
  limitations:['Only the selected text was analysed; surrounding conversation and whether you initiated an action may be missing.',
   'Sender authentication, link destinations and attachments were not verified by this explanation layer.',
   'The risk score is a model score calibrated on research validation data, not a guarantee of real-inbox probability or sender authenticity.'],
  model_reason_status:prediction.reason?'Original model reason retained separately; these observations do not rewrite it.':'No usable original model reason supplied.'};
 validateExplanation(text,result,prediction);return result;
}
export function validateExplanation(text,result,prediction){
 if(result.evidence.length>3||result.actions.length<1||result.actions.length>3)throw Error('Explanation item limit.');
 for(const e of result.evidence){
  if(e.start<0||e.end>text.length||text.slice(e.start,e.end)!==e.quote||!e.quote)throw Error('Evidence offset mismatch.');
  if(PRIVATE.test(e.quote))throw Error('Unnecessary code/long-number echo.');
  for(const field of ['observation','why','action'])if(!/[.!?]$/.test(e[field]))throw Error('Incomplete software sentence.');
 }
 for(const v of [result.assessment,...result.actions,...result.limitations])if(!v||!/[.!?]$/.test(v))throw Error('Incomplete explanation output.');
 if(result.classifier.score!==prediction.score||result.classifier.valid!==prediction.valid||result.classifier.threshold!==prediction.threshold)throw Error('Classifier output changed.');
 if(!prediction.valid&&result.presentation.risk_percent!==null)throw Error('Invalid result presented as known risk.');
 return true;
}

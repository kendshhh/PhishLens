// Small, transparent, offline retrieval index for the local review step.
// The cards below are PhishLens-authored safety guidance, not an external
// authority or a source of sender authentication.
export const RETRIEVAL_CORPUS_VERSION = 'phishlens-email-guidance-1';

const CARDS = Object.freeze([
  {
    id: 'verify-out-of-band',
    title: 'Verify unexpected requests independently',
    text: 'For an unexpected request involving an account, payment, or sensitive action, verify it using a website or contact method already known to you. Do not rely on contact details or links supplied in the message. Message text alone cannot confirm who sent it.',
  },
  {
    id: 'credentials-and-codes',
    title: 'Passwords and one-time codes',
    text: 'Do not disclose a password, recovery phrase, or one-time sign-in code in response to an unsolicited message. A code notification by itself does not prove the message is phishing or legitimate; consider whether you initiated the sign-in and verify unexpected requests independently.',
  },
  {
    id: 'payment-change',
    title: 'Payment and beneficiary changes',
    text: 'Treat an unexpected request to transfer money, pay an invoice, buy gift cards, or change bank details as needing independent verification. Confirm the request and recipient through a previously known channel before acting.',
  },
  {
    id: 'links-and-attachments',
    title: 'Visible links and unseen content',
    text: 'The visible text of an email does not establish the destination of a hidden link or the safety of an attachment. This text-only review cannot inspect hidden destinations, message headers, or attachments. Use a known site address for unexpected account actions.',
  },
  {
    id: 'routine-security-notices',
    title: 'Routine account and security notices',
    text: 'A protective warning not to share a code is different from a request to disclose that code. An account notification can be routine when it reports an event without asking for a suspicious action, but the sender is still not authenticated by wording alone.',
  },
  {
    id: 'urgency-and-branding',
    title: 'Urgency and familiar branding',
    text: 'Urgent wording, a familiar company name, a logo, a link, or a one-time code alone does not establish whether a message is phishing. Assess the specific requested action, the supporting text, and whether the event was expected.',
  },
]);

const STOP = new Set(('a an and are as at be been before by can could did do does for from had has have if in into is it its of on or our please should that the their them then this to was were what when where which who will with you your').split(/\s+/));
const tokenize = value => (String(value || '').toLowerCase().match(/[\p{L}\p{N}]{2,}/gu) || [])
  .filter(term => !STOP.has(term)).slice(0, 600);
const INDEX = CARDS.map(card => ({ ...card, terms: tokenize(`${card.title} ${card.text}`) }));
const AVERAGE_LENGTH = INDEX.reduce((sum, card) => sum + card.terms.length, 0) / INDEX.length;
const DOCUMENT_FREQUENCY = new Map();
for (const card of INDEX) {
  for (const term of new Set(card.terms)) DOCUMENT_FREQUENCY.set(term, (DOCUMENT_FREQUENCY.get(term) || 0) + 1);
}

function bm25(queryTerms, document) {
  const counts = new Map();
  for (const term of document.terms) counts.set(term, (counts.get(term) || 0) + 1);
  const k1 = 1.2, b = 0.75, n = INDEX.length, length = document.terms.length;
  let score = 0;
  for (const term of new Set(queryTerms)) {
    const tf = counts.get(term) || 0;
    if (!tf) continue;
    const df = DOCUMENT_FREQUENCY.get(term) || 0;
    const idf = Math.log(1 + (n - df + 0.5) / (df + 0.5));
    score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * length / AVERAGE_LENGTH));
  }
  return score;
}

/** Deterministic BM25 retrieval over the bundled, non-user-specific guidance cards. */
export function retrieveGuidance(text, { limit = 3, minScore = 0.35 } = {}) {
  if (!Number.isInteger(limit) || limit < 1 || limit > 5 || !Number.isFinite(minScore) || minScore < 0) {
    throw new RangeError('Invalid local retrieval limits.');
  }
  const queryTerms = tokenize(text);
  if (!queryTerms.length) return { version: RETRIEVAL_CORPUS_VERSION, query_terms: 0, documents: [] };
  const documents = INDEX.map(card => ({
    id: card.id,
    title: card.title,
    text: card.text,
    score: bm25(queryTerms, card),
  })).filter(card => card.score >= minScore)
    .sort((a, b) => b.score - a.score || a.id.localeCompare(b.id))
    .slice(0, limit);
  return { version: RETRIEVAL_CORPUS_VERSION, query_terms: queryTerms.length, documents };
}

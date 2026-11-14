import { initializeAccountPopup } from '../extension/js/account-popup.js';
import { createInMemoryAnalysisClient } from '../extension/tests/in-memory-analysis-client.mjs';
import { createMockAccounts } from './mock-accounts.mjs';
import { MODEL_SHA256 } from '../extension/ai/local-analyzer.mjs';

const clients = new Map();
const sessionStorageAdapter = {
  async get(key) { return { [key]: JSON.parse(sessionStorage.getItem(key) || 'null') }; },
  async set(data) { for (const [key, value] of Object.entries(data)) sessionStorage.setItem(key, JSON.stringify(value)); },
  async remove(key) { sessionStorage.removeItem(key); }
};
initializeAccountPopup({
  preview: true, adapter: createMockAccounts(sessionStorage),
  createClient({ user }) {
    if (!clients.has(user.id)) {
      clients.set(user.id, createInMemoryAnalysisClient([{
        id: `${user.id}-demo-report`, subject: `${user.name}'s synthetic report`, body: 'Synthetic meeting reminder.',
        prediction: 'legitimate', confidence: null, risk_level: 'low', threat_indicators: [],
        explanation: 'Synthetic preview data only.', notes: null, feedback: null, analysis_mode: 'mock',
        created_at: '2026-11-08T04:00:00Z'
      }]));
    }
    return clients.get(user.id);
  },
  fetchImpl: async url => {
    if (!url.endsWith('/model-info')) throw new Error('Live network is disabled in the account preview.');
    return new Response(JSON.stringify({ provider_mode: 'tfidf', accepts_tfidf_reports: true,
      accepts_local_reviews: true, model_sha256: MODEL_SHA256 }));
  },
  chromeImpl: {
    storage: { session: sessionStorageAdapter, onChanged: { addListener() {} } },
    runtime: { async sendMessage() { return { ok: false }; } }
  }
});
document.getElementById('account-panel').classList.remove('hidden');
document.getElementById('account-email').placeholder = 'ada@example.test';
document.getElementById('account-preview-notice').append(' Try ada@example.test or bea@example.test with Demo-only-123!.');

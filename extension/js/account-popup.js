import { initializePopup } from './popup.js';
import { createAccountSession, unavailableAccounts } from './account-session.js';
import { initializeAccountUI } from './account-ui.js';

export function initializeAccountPopup({ documentImpl = document, chromeImpl = globalThis.chrome,
  adapter = unavailableAccounts, createClient = () => { throw new Error('Live account integration is not connected.'); },
  fetchImpl = globalThis.fetch, preview = false } = {}) {
  let popup;
  const accounts = createAccountSession({ adapter, createClient,
    async onChange(userId) {
      popup?.resetReports();
      const stored = await chromeImpl.storage.session.get('phishlensReportAccount');
      if (stored.phishlensReportAccount !== userId) {
        await chromeImpl.storage.session.remove('phishlensReportAttempt');
        await chromeImpl.storage.session.set({ phishlensReportAccount: userId });
      }
    }
  });
  popup = initializePopup({ documentImpl, chromeImpl, fetchImpl, clientImpl: accounts.client, reportAccessReady: accounts.ready, canAccessReports: () => accounts.state.status === 'signed-in' });
  accounts.subscribe(() => popup.updateAccountAccess());
  const ui = initializeAccountUI(accounts, documentImpl, { preview });
  return { accounts, popup, dispose() { accounts.dispose(); ui.dispose(); } };
}

// Persist only the sign-out block, never an email, password, session or JWT.
// If site storage is unavailable, restoring a provider cookie is disabled for
// the next page load until the user explicitly signs in again.
export function createWebAccountStorage(getStorage = () => globalThis.localStorage) {
  const allowed = new Set();
  let unavailable = false;
  try {
    const storage = getStorage();
    const probe = 'phishlens:account-storage-probe';
    storage.setItem(probe, '1');
    if (storage.getItem(probe) !== '1') throw new Error('Storage did not retain the probe');
    storage.removeItem(probe);
  } catch { unavailable = true; }
  return {
    async get(key) {
      if (!key.startsWith('phishlensSignedOut:')) throw new Error('Unsupported account storage key');
      if (unavailable) return { [key]: !allowed.has(key) };
      try { return { [key]: getStorage().getItem(key) === 'true' }; }
      catch { return { [key]: !allowed.has(key) }; }
    },
    async set(values) {
      for (const [key, value] of Object.entries(values)) {
        if (!key.startsWith('phishlensSignedOut:') || value !== true) throw new Error('Unsupported account storage value');
        allowed.delete(key);
        try { getStorage().setItem(key, 'true'); } catch { unavailable = true; }
      }
    },
    async remove(key) {
      if (!key.startsWith('phishlensSignedOut:')) throw new Error('Unsupported account storage key');
      allowed.add(key);
      try { getStorage().removeItem(key); } catch { unavailable = true; }
    }
  };
}

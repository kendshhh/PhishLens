import test from 'node:test';
import assert from 'node:assert/strict';
import { createWebAccountStorage } from '../account-storage.js';
import { createNeonIntegration } from '../../extension/js/neon-integration.js';

const authUrl = 'https://auth.example.test/test/auth', apiOrigin = 'https://web.example.test';
const key = 'phishlensSignedOut:' + authUrl;
const fakeSession = { session: { expiresAt: '2099-01-01T00:00:00Z' },
  user: { id: 'a', email: 'a@example.test', emailVerified: true } };
test('failed provider logout stays blocked after reload; explicit sign-in clears only the marker', async () => {
  const data = new Map();
  const local = { getItem: k => data.get(k) ?? null, setItem: (k, v) => data.set(k, v), removeItem: k => data.delete(k) };
  let reads = 0;
  const sdk = { getSession: async () => { reads++; return { data: fakeSession }; },
    signOut: async () => ({ error: { status: 503 } }), signIn: { email: async () => ({ data: {} }) } };
  const open = () => createNeonIntegration({ config: { enabled: true, authUrl, database: 'test', apiOrigin },
    apiOrigin, storage: createWebAccountStorage(() => local), hostPermissions: ['https://auth.example.test/*'],
    sdkFactory: () => sdk }).adapter;
  const first = open();
  assert.ok(await first.restore());
  await assert.rejects(first.signOut(), { status: 503 });
  assert.deepEqual([...data], [[key, 'true']]);
  const reloaded = open();
  assert.equal(await reloaded.restore(), null);
  assert.equal(reads, 1);
  assert.ok(await reloaded.signIn({ email: 'a@example.test', password: 'Synthetic-password' }));
  assert.equal(data.size, 0);
  assert.ok(await open().restore());
});

test('unavailable or read-only site storage blocks automatic restore but permits current-page explicit login', async () => {
  for (const getStorage of [() => { throw Error('blocked'); },
    () => ({ getItem: () => null, setItem: () => { throw Error('quota'); }, removeItem() {} })]) {
    const storage = createWebAccountStorage(getStorage);
    assert.equal((await storage.get(key))[key], true);
    await storage.remove(key);
    assert.equal((await storage.get(key))[key], false);
    await storage.set({ [key]: true });
    assert.equal((await storage.get(key))[key], true);
    assert.equal((await createWebAccountStorage(getStorage).get(key))[key], true);
    await assert.rejects(storage.set({ sessionToken: 'secret' }));
  }
});

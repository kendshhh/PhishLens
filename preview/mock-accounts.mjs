// Local UI fixture. Never import this adapter from the extension entry point.
export function createMockAccounts(storage) {
  const users = new Map(['ada', 'bea'].map(name => [`${name}@example.test`, {
    id: name, name: name === 'ada' ? 'Ada Demo' : 'Bea Demo', email: `${name}@example.test`,
    emailVerified: true, password: 'Demo-only-123!'
  }]));
  const emailOf = input => {
    const email = input.email.trim().toLowerCase();
    if (!/^[^@\s]+@example\.test$/.test(email)) throw new Error('Use a fictional @example.test address in this demo.');
    return email;
  };
  function establish(user) {
    const session = { user: { id: user.id, name: user.name, email: user.email, emailVerified: user.emailVerified === true }, expiresAt: Date.now() + 600000 };
    storage.setItem('phishlens-demo-session', JSON.stringify(session));
    return session;
  }
  return {
    async restore() {
      const value = storage.getItem('phishlens-demo-session');
      return value ? JSON.parse(value) : null;
    },
    async signIn(input) {
      const user = users.get(emailOf(input));
      if (!user || user.password !== input.password) throw new Error('Email or password is incorrect.');
      return establish(user);
    },
    async signUp(input) {
      const email = emailOf(input);
      if (!input.name.trim() || input.password.length < 8) throw new Error('Enter a name and a password with at least 8 characters.');
      if (users.has(email)) throw new Error('This demo account already exists. Sign in instead.');
      const user = { id: email, name: input.name.trim(), email, password: input.password, emailVerified: false };
      users.set(email, user);
      return establish(user);
    },
    async recover(input) { emailOf(input); },
    async resetPassword(input) {
      const email = emailOf(input);
      if (input.code !== '123456' || input.password.length < 8) throw new Error('Enter code 123456 and a password with at least 8 characters.');
      const user = users.get(email);
      if (!user) throw new Error('The recovery request could not be completed.');
      user.password = input.password;
    },
    async signOut() { storage.removeItem('phishlens-demo-session'); }
  };
}

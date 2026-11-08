export function initializeAccountUI(accounts, doc = document, { preview = false } = {}) {
  const $ = id => doc.getElementById(id);
  const screens = ['sign-in', 'sign-up', 'verify', 'recover', 'reset'];
  let busy = false;
  const visible = (id, value) => $(id).classList.toggle('hidden', !value);
  function message(value, error = false) {
    $('account-status').textContent = value;
    $('account-status').setAttribute('role', error ? 'alert' : 'status');
  }
  function screen(name, focus = true) {
    for (const item of screens) visible('account-' + item, item === name);
    if (focus && name) $('account-' + name + '-heading').focus();
  }
  for (const name of screens) $('open-' + name)?.addEventListener('click', () => { message(''); screen(name); });
  $('show-account').addEventListener('click', () => {
    visible('account-panel', true);
    screen(accounts.state.status === 'signed-in' ? null : 'sign-in');
  });
  $('close-account').addEventListener('click', () => { visible('account-panel', false); $('show-account').focus(); });
  $('reports-sign-in').addEventListener('click', () => { visible('account-panel', true); screen('sign-in'); });
  const controls = $('account-panel').querySelectorAll('button, input');
  async function run(action) {
    if (busy) return;
    busy = true;
    for (const control of controls) control.disabled = true;
    $('account-panel').setAttribute('aria-busy', 'true');
    message('Please wait…');
    try { await action(); }
    catch (error) { message(error.message || 'This request could not be completed. Try again.', true); }
    finally {
      for (const control of controls) control.disabled = false;
      for (const id of ['account-password', 'signup-password', 'reset-password', 'verify-code', 'reset-code']) $(id).value = '';
      $('account-panel').setAttribute('aria-busy', 'false');
      busy = false;
    }
  }
  function submit(id, action) { $(id).addEventListener('submit', event => { event.preventDefault(); return run(action); }); }
  submit('account-sign-in', async () => {
    if (await accounts.signIn({ email: $('account-email').value.trim(), password: $('account-password').value })) {
      message(preview ? 'Signed in to the demo account. No live account was used.' : 'Signed in.');
      screen(null);
    }
  });
  submit('account-sign-up', async () => {
    await accounts.signUp({ name: $('signup-name').value.trim(), email: $('signup-email').value.trim(), password: $('signup-password').value });
    $('verify-email').value = $('signup-email').value.trim();
    screen('verify'); message(preview ? 'Demo only: enter 123456. No email was sent.' : 'Check your email for the verification code.');
  });
  submit('account-verify', async () => {
    if (await accounts.verifyEmail({ email: $('verify-email').value.trim(), code: $('verify-code').value.trim() })) {
      screen(null); message('Email verified. You are signed in.');
    }
  });
  $('resend-code').addEventListener('click', () => run(async () => {
    await accounts.resend({ email: $('verify-email').value.trim() });
    message(preview ? 'Demo verification code: 123456. No email was sent.' : 'If eligible, a new verification code has been sent.');
  }));
  submit('account-recover', async () => {
    await accounts.recover({ email: $('recovery-email').value.trim() });
    $('reset-email').value = $('recovery-email').value.trim();
    screen('reset'); message(preview ? 'Demo reset code: 123456. No email was sent.' : 'If an account exists, check your email for recovery instructions.');
  });
  submit('account-reset', async () => {
    await accounts.resetPassword({ email: $('reset-email').value.trim(), code: $('reset-code').value.trim(), password: $('reset-password').value });
    screen('sign-in'); message('Password updated. Sign in with your new password.');
  });
  $('account-sign-out').addEventListener('click', () => run(async () => { await accounts.signOut(); screen('sign-in'); message(accounts.state.message || 'Signed out. Local scanning is still available.'); }));
  const unsubscribe = accounts.subscribe(state => {
    const signedIn = state.status === 'signed-in';
    $('account-identity').textContent = signedIn ? state.user.name || state.user.email : 'Keep scanning without an account';
    $('show-account').textContent = signedIn ? 'Account' : 'Sign in';
    visible('account-sign-out', signedIn);
    visible('reports-account-gate', !signedIn);
    visible('personal-reports', signedIn);
    message(state.message, state.status === 'expired');
    if (state.status === 'expired') { visible('account-panel', true); screen('sign-in'); }
    if (signedIn) screen(null, false);
  });
  visible('account-preview-notice', preview);
  return { dispose: unsubscribe };
}

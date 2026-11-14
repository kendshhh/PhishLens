const dialog = document.querySelector('#auth-dialog');
const title = document.querySelector('#auth-title');
const email = document.querySelector('#auth-email');
const password = document.querySelector('#auth-password');
const submit = document.querySelector('.auth-submit');
const switchPrompt = document.querySelector('#auth-switch-prompt');
const switchButton = document.querySelector('#auth-switch');
const status = document.querySelector('#auth-status');
const form = document.querySelector('#auth-form');
let mode = 'login';

function setMode(nextMode) {
  mode = nextMode;
  const signup = mode === 'signup';
  title.textContent = signup ? 'Create your account' : 'Welcome back';
  submit.textContent = signup ? 'Create account' : 'Continue';
  password.autocomplete = signup ? 'new-password' : 'current-password';
  switchPrompt.textContent = signup ? 'Already have an account?' : 'New to PhishLens?';
  switchButton.textContent = signup ? 'Log in' : 'Create an account';
  status.textContent = '';
}

document.querySelectorAll('[data-auth]').forEach(button => {
  button.addEventListener('click', () => {
    setMode(button.dataset.auth);
    dialog.showModal();
  });
});

document.querySelector('.dialog-close').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => {
  if (event.target === dialog) dialog.close();
});
dialog.addEventListener('close', () => {
  form.reset();
  status.textContent = '';
});
switchButton.addEventListener('click', () => setMode(mode === 'login' ? 'signup' : 'login'));
form.addEventListener('submit', event => {
  event.preventDefault();
  status.textContent = 'Account access is not connected yet. Your details were not sent or saved.';
  email.value = '';
  password.value = '';
});

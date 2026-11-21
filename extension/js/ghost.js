// The monocle ghost: a decorative companion that reacts to phishing wording.
// It is a light, instant hint while the user pastes or views text. The real
// assessment is still the local workflow's result shown in the panel.
import { observations } from '../ai/observations.mjs';

// Wording cues taken from the strongest phishing-weighted terms of the bundled
// TF-IDF v12a model (extension/ai/tfidf_v12a.json). Dataset artifacts such as
// names, years and image file names are left out; only reusable cues remain.
export const PHISH_CUES = [
  'kindly', 'dear customer', 'dear user', 'dear email', 'valued customer',
  'verify your', 'confirm your', 'validate your', 'update your', 'please update',
  'to verify', 'to validate', 'verification process', 'account information',
  'click here', 'click on', 'click below', 'button below', 'log in', 'sign in to',
  'your account', 'account will', 'your mailbox', 'mailbox', 'webmail', 'mail system',
  'help desk', 'helpdesk', 'administrator',
  'suspended', 'blocked', 'locked', 'deactivation', 'closure', 'on hold',
  'unusual activity', 'unusual', 'detected', 'will expire', 'password will',
  'be lost', 'data will', 'exceeded', 'action required', 'is required', 'immediately',
  'your package', 'your parcel', 'be delivered', 'shipping cost', 'tracking number',
  'payment details', 'your payment', 'invoice', 'wallet', 'online banking',
  'your card', 'bank account', 'wire transfer', 'gift card', 'prize', 'winner',
  'inheritance', 'beneficiary', 'urgent'
];

// Rule-based observations that describe a request rather than a neutral topic.
const ADVERSE = new Set(['sensitive', 'pressure', 'funds', 'payment', 'link']);
const escape = value => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const CUE_PATTERNS = PHISH_CUES.map(cue => [cue, new RegExp(`\\b${escape(cue).replace(/ /g, '\\s+')}\\b`, 'i')]);

export function inspectText(text) {
  if (typeof text !== 'string' || !text.trim()) return { cues: [], flags: [] };
  const cues = CUE_PATTERNS.filter(([, pattern]) => pattern.test(text)).map(([cue]) => cue);
  let flags = [];
  try { flags = observations(text).filter(item => ADVERSE.has(item.type)).map(item => item.type); } catch { /* decorative only */ }
  return { cues, flags };
}

// calm: nothing notable. curious: a single cue. shocked: several cues, a red-flag
// request, or a released result that raised an alert.
export function moodFor({ cues = [], flags = [] } = {}, { alert = false } = {}) {
  if (alert || flags.length || cues.length >= 2) return 'shocked';
  return cues.length === 1 ? 'curious' : 'calm';
}

const FLAG_LABELS = { sensitive: 'asks for secrets', pressure: 'account threats', funds: 'money offer',
  payment: 'payment request', link: 'sign-in link' };

function bubbleFor(mood, { cues = [], flags = [] }, alert) {
  if (mood === 'calm') return '';
  if (mood === 'curious') return `Hmm… “${cues[0]}”`;
  const spotted = [...flags.map(flag => FLAG_LABELS[flag]), ...cues.map(cue => `“${cue}”`)].slice(0, 2);
  return spotted.length ? `Whoa! ${spotted.join(', ')}` : alert ? 'Whoa! This looks phishy.' : 'Whoa!';
}

// Keeps a dragged ghost fully inside the panel, even after the panel is resized.
export function clampPosition({ left, top }, { width, height }, { innerWidth, innerHeight }, margin = 4) {
  return {
    left: Math.round(Math.min(Math.max(margin, left), Math.max(margin, innerWidth - width - margin))),
    top: Math.round(Math.min(Math.max(margin, top), Math.max(margin, innerHeight - height - margin)))
  };
}

const POSITION_KEY = 'phishlensGhostPosition';

// Drag the ghost by its body anywhere inside the panel. A page cannot draw outside
// its own window, so the side panel's edges are the limit. Double-click returns it
// to its corner. The position is a per-browser convenience kept in localStorage.
function enableDrag(ghost, win) {
  const handle = ghost.querySelector?.('.ghost-body');
  if (!handle || !win?.addEventListener) return;
  let drag = null;
  const read = () => ({ left: parseFloat(ghost.style.left), top: parseFloat(ghost.style.top) });
  function place(position) {
    const size = { width: ghost.offsetWidth || 64, height: ghost.offsetHeight || 84 };
    const next = clampPosition(position, size, win);
    Object.assign(ghost.style, { left: next.left + 'px', top: next.top + 'px', right: 'auto', bottom: 'auto' });
    // Keep the speech bubble on screen: beside the ghost on the roomier side, below it near the top.
    ghost.classList.toggle('bubble-right', next.left + size.width / 2 < win.innerWidth / 2);
    ghost.classList.toggle('bubble-below', next.top < 90);
  }
  function reset() {
    Object.assign(ghost.style, { left: '', top: '', right: '', bottom: '' });
    ghost.classList.remove('bubble-right', 'bubble-below');
    try { win.localStorage.removeItem(POSITION_KEY); } catch { /* convenience only */ }
  }
  try {
    const saved = JSON.parse(win.localStorage.getItem(POSITION_KEY));
    if (Number.isFinite(saved?.left) && Number.isFinite(saved?.top)) place(saved);
  } catch { /* convenience only */ }
  handle.addEventListener('pointerdown', event => {
    if (event.button !== 0) return;
    const box = ghost.getBoundingClientRect();
    drag = { id: event.pointerId, dx: event.clientX - box.left, dy: event.clientY - box.top };
    handle.setPointerCapture?.(event.pointerId);
    ghost.classList.add('is-dragging');
    event.preventDefault();
  });
  handle.addEventListener('pointermove', event => {
    if (drag?.id === event.pointerId) place({ left: event.clientX - drag.dx, top: event.clientY - drag.dy });
  });
  const finish = event => {
    if (drag?.id !== event.pointerId) return;
    drag = null;
    ghost.classList.remove('is-dragging');
    try { win.localStorage.setItem(POSITION_KEY, JSON.stringify(read())); } catch { /* convenience only */ }
  };
  handle.addEventListener('pointerup', finish);
  handle.addEventListener('pointercancel', finish);
  handle.addEventListener('dblclick', reset);
  win.addEventListener('resize', () => { if (ghost.style.left) place(read()); });
}

export function initializeGhost({ documentImpl = document, chromeImpl = globalThis.chrome, windowImpl = globalThis.window } = {}) {
  const ghost = documentImpl.getElementById('ghost');
  const bubble = documentImpl.getElementById('ghost-bubble');
  const textarea = documentImpl.getElementById('scan-body');
  if (!ghost || !bubble) return { update() {} };
  enableDrag(ghost, windowImpl);
  let analysis = null;
  let mood = 'calm';
  let bubbleTimer;
  const pastePanel = documentImpl.getElementById('paste-panel');
  // The ghost reacts to the user's most recent action, so clearing what it reacted
  // to calms it: 'pasted' = the paste box was opened or edited, 'viewed' = the
  // current check, 'none' = the check was just cleared (calm until the next action).
  let focus = 'pasted';
  // Text in a collapsed paste box is out of sight, so it never alarms the ghost.
  const pasteVisible = () => !pastePanel || pastePanel.open !== false;

  function update() {
    let found = { cues: [], flags: [] };
    let alert = false;
    if (focus === 'pasted' && pasteVisible()) found = inspectText(textarea?.value ?? '');
    else if (focus === 'viewed') {
      found = inspectText(typeof analysis?.selectedText === 'string' ? analysis.selectedText : '');
      const result = analysis?.status === 'success' ? analysis.result : null;
      alert = Boolean(result?.workflow?.released && result.alert);
    }
    const next = moodFor(found, { alert });
    const label = bubbleFor(next, found, alert);
    if (next !== mood) {
      // Restart the reaction animation each time the ghost becomes shocked.
      ghost.classList.remove('is-reacting');
      if (next === 'shocked') { void ghost.offsetWidth; ghost.classList.add('is-reacting'); }
    }
    mood = next;
    ghost.dataset.mood = next;
    // Show the bubble briefly when its message changes so it never sits over the text
    // being typed. The face and the "!" keep showing the mood.
    if (label !== bubble.textContent || !label) {
      clearTimeout(bubbleTimer);
      bubble.textContent = label;
      ghost.classList.toggle('has-bubble', Boolean(label));
      if (label) bubbleTimer = setTimeout(() => ghost.classList.remove('has-bubble'), 4500);
    }
    ghost.setAttribute('aria-label', next === 'shocked' ? 'PhishLens ghost: shocked by phishing wording'
      : next === 'curious' ? 'PhishLens ghost: curious' : 'PhishLens ghost: all calm');
  }

  let pending;
  let typed = false;
  textarea?.addEventListener('input', () => {
    focus = 'pasted'; typed = true;
    clearTimeout(pending); pending = setTimeout(update, 200);
  });
  // Opening the paste box shows its text again (a check keeps the draft), so the
  // ghost looks at it; closing it hides that text.
  pastePanel?.addEventListener('toggle', () => {
    if (pastePanel.open) { focus = 'pasted'; typed = true; }
    if (pastePanel.open || focus === 'pasted') { clearTimeout(pending); update(); }
  });
  chromeImpl?.storage?.onChanged?.addListener((changes, area) => {
    if (area !== 'session' || !('veriqoAnalysis' in changes)) return;
    analysis = changes.veriqoAnalysis.newValue ?? null;
    focus = analysis ? 'viewed' : 'none';
    clearTimeout(pending);
    update();
  });
  chromeImpl?.storage?.session?.get(['veriqoAnalysis', 'phishlensScanDraft']).then(data => {
    analysis = data?.veriqoAnalysis ?? null;
    if (analysis && !typed) focus = 'viewed';
    // popup.js restores the draft into the textarea; read it after that settles.
    setTimeout(() => {
      update();
      if (mood === 'calm') {
        bubble.textContent = 'Hi! I’ll keep an eye out.';
        ghost.classList.add('has-bubble');
        bubbleTimer = setTimeout(() => ghost.classList.remove('has-bubble'), 3500);
      }
    }, 0);
  }).catch(update);
  return { update };
}

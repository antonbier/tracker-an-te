/**
 * app/onboarding.js — Full-screen onboarding wizard
 *
 * A three-step full-screen experience shown on first launch (when no backend
 * URL is configured). Steps:
 *
 *   Step 1 — "Willkommen beim Abenteuer"
 *     Backend URL input + live /health check with visual feedback
 *     (spinner → green ✓ on success / red warning on failure).
 *     "Weiter" is only enabled after a successful connection.
 *
 *   Step 2 — "Deine Werkzeuge"
 *     Optional SerpAPI + Gemini key inputs with links to get them.
 *     Can be skipped — keys can always be added later in Settings.
 *
 *   Step 3 — "Alles bereit!"
 *     Confirmation screen. Final button "Lass das Abenteuer beginnen"
 *     saves URL + keys to localStorage and syncs to backend.
 *
 * On close: smooth fade-out animation via CSS class .ob-closing.
 * Completion flag: localStorage key 'ws-onboarding-done' = '1'.
 */

import { setApiUrl, setObStep, obStep } from '../core/state.js';
import { t } from '../ui/i18n.js';

// Track whether step 1 connection was verified
let connectionVerified = false;

/** Show onboarding if no backend URL is set and wizard hasn't been completed. */
export function checkOnboarding() {
  const hasUrl = localStorage.getItem('apiUrl');
  const seen   = localStorage.getItem('ws-onboarding-done');
  if (!hasUrl && !seen) {
    setObStep(1);
    updateObStep();
    document.getElementById('onboardingBackdrop').classList.add('open');
    document.body.style.overflow = 'hidden';
  }
}

/** Close the wizard with a fade-out animation, then save completion flag. */
export function closeOnboarding() {
  const el = document.getElementById('onboardingBackdrop');
  el.classList.add('ob-closing');
  setTimeout(() => {
    el.classList.remove('open', 'ob-closing');
    document.body.style.overflow = '';
    localStorage.setItem('ws-onboarding-done', '1');
  }, 400);
}

/**
 * Handle the "Weiter / Fertig" button click.
 * Step 1: validate URL (must have been verified via checkConnection()).
 * Step 2: optionally save API keys.
 * Step 3: save everything, sync to backend, close.
 */
export async function obNext() {
  if (obStep === 1) {
    // URL is optional — save it if provided but don't block on connection
    const url = document.getElementById('ob-url').value.trim().replace(/\/$/, '');
    if (url) {
      localStorage.setItem('apiUrl', url);
      const { setApiUrl } = await import('../core/state.js');
      setApiUrl(url);
      checkConnection(); // fire-and-forget visual feedback, don't block
    }
    // Always allow proceeding — app works without backend (frontend-only mode)
  }

  if (obStep >= 3) {
    await _finishOnboarding();
    return;
  }

  setObStep(obStep + 1);
  updateObStep();
}

export function obBack() {
  if (obStep <= 1) return;
  setObStep(obStep - 1);
  updateObStep();
}

/** Update visible panel, step indicators, button labels. */
export function updateObStep() {
  [1, 2, 3].forEach(i => {
    const panel  = document.getElementById('ob-panel-' + i);
    const stepEl = document.getElementById('ob-step-' + i);
    if (panel)  panel.style.display = i === obStep ? 'block' : 'none';
    if (stepEl) {
      stepEl.classList.remove('active', 'done');
      if (i < obStep)  stepEl.classList.add('done');
      if (i === obStep) stepEl.classList.add('active');
    }
  });

  const backBtn = document.getElementById('ob-back');
  const nextBtn = document.getElementById('ob-next');
  if (backBtn) backBtn.style.display = obStep > 1 ? 'inline-flex' : 'none';
  if (nextBtn) {
    if (obStep === 1) nextBtn.textContent = t('obNextStep') || 'Weiter →';
    if (obStep === 2) nextBtn.textContent = t('obNextStep') || 'Weiter →';
    if (obStep === 3) nextBtn.textContent = t('obFinish') || '🧳 Lass das Abenteuer beginnen';
  }

  // Reset connection state when returning to step 1
  if (obStep === 1) _resetConnectionStatus();
}

/**
 * Live /health check triggered by the "Verbinden" button in step 1.
 * Shows spinner → green check on success, red warning on failure.
 */
export async function checkConnection() {
  const url    = document.getElementById('ob-url').value.trim().replace(/\/$/, '');
  const status = document.getElementById('ob-conn-status');
  const nextBtn = document.getElementById('ob-next');

  if (!url) { _showUrlError(t('obUrlRequired') || 'Bitte URL eingeben.'); return; }

  // Show spinner
  status.innerHTML = '<span class="ob-spinner"></span> <span class="ob-status-text">' + (t('obConnecting') || 'Verbinde…') + '</span>';
  status.className = 'ob-conn-status ob-connecting';
  connectionVerified = false;
  if (nextBtn) nextBtn.disabled = true;

  try {
    const r = await fetch(url + '/health', { signal: AbortSignal.timeout(6000) });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    // Success
    connectionVerified = true;
    status.innerHTML = '✅ <span class="ob-status-text">' + (t('obConnected') || 'Verbunden!') + '</span>';
    status.className = 'ob-conn-status ob-success';
    if (nextBtn) nextBtn.disabled = false;
    // Save URL immediately
    const cleanUrl = url;
    localStorage.setItem('apiUrl', cleanUrl);
    setApiUrl(cleanUrl);
  } catch (e) {
    connectionVerified = false;
    status.innerHTML = '❌ <span class="ob-status-text">' + (t('obConnectFailed') || 'Keine Verbindung') + ': ' + e.message + '</span>';
    status.className = 'ob-conn-status ob-error';
    if (nextBtn) nextBtn.disabled = true;
  }
}

// ── Private helpers ───────────────────────────────────────────────────────────

function _resetConnectionStatus() {
  const status  = document.getElementById('ob-conn-status');
  const nextBtn = document.getElementById('ob-next');
  if (status) { status.innerHTML = ''; status.className = 'ob-conn-status'; }
  connectionVerified = false;
  // Re-enable next if URL already saved (revisiting)
  if (nextBtn) nextBtn.disabled = !localStorage.getItem('apiUrl');
}

function _showUrlError(msg) {
  const status = document.getElementById('ob-conn-status');
  if (status) {
    status.innerHTML = '⚠️ <span class="ob-status-text">' + msg + '</span>';
    status.className = 'ob-conn-status ob-error';
  }
  document.getElementById('ob-url')?.focus();
}

async function _finishOnboarding() {
  // Save optional API keys from step 2
  const serpKey   = document.getElementById('ob-serpapi')?.value.trim() || '';
  const geminiKey = document.getElementById('ob-gemini')?.value.trim()  || '';
  if (serpKey)   localStorage.setItem('s-serpApiKey', serpKey);
  if (geminiKey) localStorage.setItem('s-geminiKey', geminiKey);

  // Sync to backend if connected
  const apiUrl = localStorage.getItem('apiUrl') || '';
  if (apiUrl && (serpKey || geminiKey)) {
    try {
      await fetch(apiUrl + '/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          serpapi_key: serpKey  || null,
          gemini_key:  geminiKey || null,
        }),
      });
    } catch(e) { /* silent — keys are in localStorage as fallback */ }
  }

  // Update status dot
  const { checkApiStatus } = await import('../core/api.js');
  checkApiStatus();

  // Hide api-notice if visible
  const notice = document.querySelector('.api-notice');
  if (notice) notice.classList.add('hidden');

  closeOnboarding();

  // Load dashboard
  const { loadDashboard } = await import('./dashboard.js');
  loadDashboard();
}

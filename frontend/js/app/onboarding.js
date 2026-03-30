/**
 * app/onboarding.js — Full-screen onboarding wizard (shown only on first visit)
 *
 * Nuclear approach: backdrop is REMOVED from DOM when not needed.
 * This guarantees it can never block clicks regardless of CSS state.
 */

import { setApiUrl, setObStep, obStep } from '../core/state.js';
import { t } from '../ui/i18n.js';

let connectionVerified = false;

/** Show onboarding if no backend URL is set and wizard hasn't been completed. */
export function checkOnboarding() {
  const hasUrl = localStorage.getItem('apiUrl');
  const seen   = localStorage.getItem('ws-onboarding-done');

  // Any reason to skip → remove backdrop from DOM entirely
  if (seen || hasUrl) {
    if (hasUrl && !seen) localStorage.setItem('ws-onboarding-done', '1');
    _removeBd();
    return;
  }

  // Truly first visit: show wizard
  const bd = document.getElementById('onboardingBackdrop');
  if (!bd) return;
  setObStep(1);
  updateObStep();
  bd.classList.add('open');
  document.body.style.overflow = 'hidden';
}

/** Remove backdrop from DOM entirely — nuclear guarantee no click blocking. */
function _removeBd() {
  const bd = document.getElementById('onboardingBackdrop');
  if (bd) bd.remove();
}

/** Close the wizard and remove from DOM. */
export function closeOnboarding() {
  const el = document.getElementById('onboardingBackdrop');
  if (!el) return;
  el.style.pointerEvents = 'none';
  el.classList.add('ob-closing');
  setTimeout(() => {
    el.remove();
    document.body.style.overflow = '';
    localStorage.setItem('ws-onboarding-done', '1');
  }, 350);
}

/**
 * Handle the "Weiter / Fertig" button click.
 */
export async function obNext() {
  if (obStep === 1) {
    const url = document.getElementById('ob-url').value.trim().replace(/\/$/, '');
    if (url) {
      localStorage.setItem('apiUrl', url);
      const { setApiUrl } = await import('../core/state.js');
      setApiUrl(url);
      checkConnection();
    }
    // Always allow proceeding
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

export function updateObStep() {
  for (let i = 1; i <= 3; i++) {
    const panel = document.getElementById('ob-panel-' + i);
    const step  = document.getElementById('ob-step-' + i);
    const line  = document.getElementById('ob-line-' + (i - 1));
    if (panel) panel.style.display = i === obStep ? 'block' : 'none';
    if (step)  step.classList.toggle('active', i <= obStep);
    if (line)  line.classList.toggle('active', i <= obStep);
  }
  const backBtn = document.getElementById('ob-back');
  const nextBtn = document.getElementById('ob-next');
  if (backBtn) backBtn.style.display = obStep > 1 ? 'inline-flex' : 'none';
  if (nextBtn) {
    if (obStep === 3) {
      nextBtn.setAttribute('data-i18n', 'obFinish');
      nextBtn.textContent = t('obFinish') || 'Lass das Abenteuer beginnen →';
    } else {
      nextBtn.setAttribute('data-i18n', 'obNextStep');
      nextBtn.textContent = t('obNextStep') || 'Weiter →';
    }
  }
}

export async function checkConnection() {
  const url    = (document.getElementById('ob-url')?.value || '').trim().replace(/\/$/, '');
  const status = document.getElementById('ob-conn-status');
  if (!url) return;
  if (status) { status.textContent = '⏳ Verbinde…'; status.className = 'ob-conn-status pending'; }
  try {
    const r = await fetch(url + '/health', { signal: AbortSignal.timeout(5000) });
    if (r.ok) {
      connectionVerified = true;
      if (status) { status.textContent = '✅ Verbunden!'; status.className = 'ob-conn-status success'; }
    } else {
      if (status) { status.textContent = '⚠️ Server antwortet nicht korrekt'; status.className = 'ob-conn-status error'; }
    }
  } catch(e) {
    if (status) { status.textContent = '❌ Nicht erreichbar — trotzdem fortfahren möglich'; status.className = 'ob-conn-status error'; }
  }
}

function _showUrlError(msg) {
  const s = document.getElementById('ob-conn-status');
  if (s) { s.textContent = msg; s.className = 'ob-conn-status error'; }
}

async function _finishOnboarding() {
  const url     = localStorage.getItem('apiUrl') || '';
  const serpapi = document.getElementById('ob-serpapi')?.value || '';
  const gemini  = document.getElementById('ob-gemini')?.value  || '';
  if (serpapi) localStorage.setItem('s-serpApiKey', serpapi);
  if (gemini)  localStorage.setItem('s-geminiKey',  gemini);
  if (url && (serpapi || gemini)) {
    try {
      await fetch(url + '/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          serpapi_key: serpapi || null,
          gemini_key:  gemini  || null,
        }),
      });
    } catch(e) { /* silent */ }
  }
  closeOnboarding();
  const { checkApiStatus } = await import('../core/api.js');
  const { loadDashboard }  = await import('./dashboard.js');
  setTimeout(checkApiStatus, 300);
  loadDashboard();
}

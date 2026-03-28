/**
 * app/onboarding.js — First-run onboarding wizard + Field Guide modal
 *
 * Onboarding:
 *   - Shows a 3-step wizard on first load if no backend URL is set
 *   - Step 1: Enter backend URL
 *   - Step 2: Create first tracker (guided)
 *   - Step 3: Ready confirmation
 *   - Completion state stored in localStorage (ws-onboarding-done)
 *
 * Field Guide:
 *   - FAQ modal accessible from the header (📖 button)
 *   - Content is translated via data-i18n attributes
 *
 * Functions: checkOnboarding, closeOnboarding, obNext, obBack, updateObStep,
 *             openFieldGuide, closeFieldGuide
 */
// frontend/js/app/onboarding.js
import { t } from '../ui/i18n.js';
import { API_URL, obStep, setObStep, setApiUrl } from '../core/state.js';

export function checkOnboarding() {
  const hasUrl = localStorage.getItem('apiUrl');
  const seen   = localStorage.getItem('ws-onboarding-done');
  if (!hasUrl && !seen) {
    document.getElementById('onboardingBackdrop').classList.add('open');
    document.body.style.overflow = 'hidden';
  }
}

export function closeOnboarding() {
  localStorage.setItem('ws-onboarding-done', '1');
  document.getElementById('onboardingBackdrop').classList.remove('open');
  document.body.style.overflow = '';
}

export async function obNext() {
  if (obStep === 1) {
    const url = document.getElementById('ob-url').value.trim().replace(/\/$/, '');
    if (url) {
      setApiUrl(url);
      localStorage.setItem('apiUrl', url);
      const apiInput = document.getElementById('apiUrlInput');
      if (apiInput) apiInput.value = url;
      const { checkApiStatus } = await import('../core/api.js');
      checkApiStatus();
    }
  }
  if (obStep >= 3) { closeOnboarding(); const { loadDashboard } = await import('./dashboard.js'); loadDashboard(); return; }
  setObStep(obStep + 1);
  updateObStep();
}

export function obBack() {
  if (obStep <= 1) return;
  setObStep(obStep - 1);
  updateObStep();
}

export function updateObStep() {
  [1,2,3].forEach(i => {
    document.getElementById('ob-panel-'+i).style.display = i===obStep ? 'block' : 'none';
    const stepEl = document.getElementById('ob-step-'+i);
    stepEl.classList.remove('active','done');
    if (i < obStep)  stepEl.classList.add('done');
    if (i === obStep) stepEl.classList.add('active');
  });
  document.getElementById('ob-back').style.display   = obStep > 1 ? 'inline-flex' : 'none';
  document.getElementById('ob-next').textContent     = obStep >= 3 ? `🎒 ${t('startTracker')}` : `${t('refresh')} →`;
}

// openFieldGuide() and closeFieldGuide() live in ui/fieldguide.js

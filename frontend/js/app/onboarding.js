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

export function openFieldGuide() {
  document.querySelectorAll('.faq-answer[data-i18n]').forEach(el => { el.textContent = t(el.getAttribute('data-i18n')); });
  document.querySelectorAll('.faq-question[data-i18n]').forEach(el => { el.textContent = t(el.getAttribute('data-i18n')); });
  document.getElementById('fieldGuideBackdrop').classList.add('open');
  document.body.style.overflow = 'hidden';
  if (window.innerWidth < 900) { import('../ui/nav.js').then(m => m.closeSidebar()); }
}

export function closeFieldGuide(e) {
  if (e && e.target !== document.getElementById('fieldGuideBackdrop')) return;
  document.getElementById('fieldGuideBackdrop').classList.remove('open');
  document.body.style.overflow = '';
}

// frontend/js/ui/settings.js
import { setApiUrl } from '../core/state.js';
import { t } from './i18n.js';
import { toast } from './toast.js';

export function openSettings() {
  const tzSel = document.getElementById('s-timezone');
  if (!tzSel.options.length) {
    ['Europe/Rome','Europe/Berlin','Europe/London','Europe/Paris','Europe/Madrid','Europe/Zurich',
     'Europe/Vienna','America/New_York','America/Chicago','America/Los_Angeles',
     'Asia/Tokyo','Asia/Shanghai','Australia/Sydney','UTC'].forEach(z => {
      const o = document.createElement('option'); o.value = o.textContent = z; tzSel.appendChild(o);
    });
  }
  document.getElementById('s-backendUrl').value        = localStorage.getItem('apiUrl') || '';
  document.getElementById('s-timezone').value          = localStorage.getItem('s-timezone') || 'Europe/Rome';
  document.getElementById('s-lightMode').checked       = document.body.classList.contains('light-mode');
  document.getElementById('s-dawarichUrl').value       = localStorage.getItem('s-dawarichUrl') || '';
  document.getElementById('s-dawarichToken').value     = localStorage.getItem('s-dawarichToken') || '';
  document.getElementById('s-actualUrl').value         = localStorage.getItem('s-actualUrl') || '';
  document.getElementById('s-actualPassword').value    = localStorage.getItem('s-actualPassword') || '';
  document.getElementById('s-actualFile').value        = localStorage.getItem('s-actualFile') || '';
  document.getElementById('s-llmProvider').value       = localStorage.getItem('s-llmProvider') || '';
  document.getElementById('s-llmKey').value            = localStorage.getItem('s-llmKey') || '';
  document.getElementById('s-homeLat').value           = localStorage.getItem('s-homeLat') || '';
  document.getElementById('s-homeLon').value           = localStorage.getItem('s-homeLon') || '';
  document.getElementById('s-travelCategories').value  = localStorage.getItem('s-travelCategories') || '';
  document.getElementById('s-serpApiKey').value        = localStorage.getItem('s-serpApiKey') || '';
  document.getElementById('s-geminiKey').value         = localStorage.getItem('s-geminiKey') || '';
  document.getElementById('s-openaiKey').value         = localStorage.getItem('s-openaiKey') || '';
  switchTab('basic');
  document.getElementById('settingsBackdrop').classList.add('open');
  document.body.style.overflow = 'hidden';
  if (localStorage.getItem('s-serpApiKey')) loadSerpApiQuota();
}

export function closeSettings() {
  document.getElementById('settingsBackdrop').classList.remove('open');
  document.body.style.overflow = '';
}

export async function loadSerpApiQuota() {
  const apiUrl = localStorage.getItem('apiUrl');
  if (!apiUrl) return;
  const wrap = document.getElementById('serpapi-quota-wrap');
  const bar  = document.getElementById('serpapi-quota-bar');
  const txt  = document.getElementById('serpapi-quota-text');
  wrap.style.display = 'block';
  txt.textContent = '…';
  try {
    const r = await fetch(`${apiUrl}/api/settings/serpapi-quota`);
    const d = await r.json();
    if (d.error) { txt.textContent = d.error; bar.style.width = '0%'; return; }
    const used  = d.used  ?? 0;
    const limit = d.limit ?? 100;
    const pct   = Math.min(100, Math.round((used / limit) * 100));
    bar.style.width = pct + '%';
    bar.style.background = pct >= 90 ? '#e07b5a' : pct >= 70 ? '#d4a843' : 'var(--accent)';
    txt.textContent = `${used} / ${limit}`;
  } catch(e) { txt.textContent = 'Fehler'; }
}

export function backdropClick(e) {
  if (e.target === document.getElementById('settingsBackdrop')) closeSettings();
}

export function switchTab(tab) {
  ['basic','integrations','apis'].forEach(id => {
    const panel = document.getElementById('panel-'+id);
    const tabEl = document.getElementById('tab-'+id);
    if (panel) panel.style.display = id===tab ? 'block' : 'none';
    if (tabEl) tabEl.classList.toggle('active', id===tab);
  });
}

export function toggleTheme(isDark) {
  document.body.classList.toggle('dark-mode', isDark);
  localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

export async function saveSettings() {
  const newUrl = document.getElementById('s-backendUrl').value.trim().replace(/\/$/, '');
  localStorage.setItem('apiUrl', newUrl);
  setApiUrl(newUrl);
  ['s-timezone','s-dawarichUrl','s-dawarichToken','s-actualUrl','s-actualPassword',
   's-actualFile','s-llmProvider','s-llmKey','s-serpApiKey','s-geminiKey','s-openaiKey',
   's-homeLat','s-homeLon','s-travelCategories'].forEach(k => {
    localStorage.setItem(k, document.getElementById(k).value);
  });
  try {
    await fetch(newUrl + '/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        serpapi_key:       document.getElementById('s-serpApiKey').value || null,
        gemini_key:        document.getElementById('s-geminiKey').value  || null,
        openai_key:        document.getElementById('s-openaiKey').value  || null,
        dawarich_url:      document.getElementById('s-dawarichUrl').value   || null,
        dawarich_token:    document.getElementById('s-dawarichToken').value || null,
        actual_url:        document.getElementById('s-actualUrl').value     || null,
        actual_token:      document.getElementById('s-actualPassword').value || null,
        actual_file:       document.getElementById('s-actualFile').value    || null,
        llm_provider:      document.getElementById('s-llmProvider').value   || null,
        timezone:          document.getElementById('s-timezone').value      || null,
        home_lat:          document.getElementById('s-homeLat').value       || null,
        home_lon:          document.getElementById('s-homeLon').value       || null,
        travel_categories: document.getElementById('s-travelCategories').value || null,
      }),
    });
  } catch(e) { /* Server sync optional */ }

  toast(t('saved') + ' ✓', 'success');
  closeSettings();

  const { checkApiStatus } = await import('../core/api.js');
  const { loadTrackers }   = await import('../app/ryanair.js');
  const { loadDashboard }  = await import('../app/dashboard.js');
  const { checkOnboarding } = await import('../app/onboarding.js');
  setTimeout(checkApiStatus, 300);
  setTimeout(loadTrackers, 600);
  loadDashboard();
  checkOnboarding();

  if (newUrl) {
    const notice = document.querySelector('.api-notice');
    if (notice) notice.classList.add('hidden');
  }
}

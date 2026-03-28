// frontend/js/core/api.js
import { API_URL } from './state.js';
import { t } from '../ui/i18n.js';

export async function api(path, opts = {}) {
  const base = localStorage.getItem('apiUrl') || API_URL || '';
  if (!base) throw new Error(t('missingUrl'));
  const r = await fetch(base + path, { headers: { 'Content-Type': 'application/json' }, ...opts });
  if (!r.ok) { const err = await r.json().catch(() => ({ detail: r.statusText })); throw new Error(err.detail || `HTTP ${r.status}`); }
  return r.json();
}

export async function checkApiStatus() {
  const dot = document.getElementById('statusDot');
  const base = localStorage.getItem('apiUrl') || '';
  if (!base) {
    dot.style.background = 'var(--red)';
    dot.style.boxShadow  = '0 0 6px var(--red)';
    dot.title = 'Backend URL nicht konfiguriert';
    return;
  }
  try {
    const r2 = await fetch(base + '/health', { signal: AbortSignal.timeout(5000) });
    if (!r2.ok) throw new Error(`HTTP ${r2.status}`);
    dot.style.background = 'var(--green)';
    dot.style.boxShadow  = '0 0 6px var(--green)';
    dot.title = 'Backend online';
  } catch(e) {
    dot.style.background = 'var(--red)';
    dot.style.boxShadow  = '0 0 6px var(--red)';
    dot.title = 'Backend nicht erreichbar: ' + e.message;
  }
}

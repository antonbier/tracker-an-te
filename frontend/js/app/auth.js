/**
 * app/auth.js — Authentication flow
 *
 * On DOMContentLoaded, checks GET /api/status:
 *   - auth_enabled: false → skip auth entirely, show app normally
 *   - needs_setup: true   → show setup screen (create first admin)
 *   - logged in (JWT in localStorage) → validate + show app
 *   - not logged in → show login screen
 *
 * JWT is stored in localStorage under key 'ws-jwt'.
 * Injected into every fetch via the api() client in core/api.js.
 *
 * Exports:
 *   initAuth()          — called from main.js on DOMContentLoaded
 *   logout()            — clears JWT + reloads
 *   showAuthScreen()    — shows login/setup overlay
 *   hideAuthScreen()    — removes overlay after success
 *   submitSetup()       — handles setup form submission
 *   submitLogin()       — handles login form submission
 *   switchAuthTab(tab)  — toggles login/setup panels in auth overlay
 */

import { setApiUrl } from '../core/state.js';

const JWT_KEY = 'ws-jwt';

// ── Token helpers ──────────────────────────────────────────────────────────

export function getToken()         { return localStorage.getItem(JWT_KEY); }
export function setToken(t)        { localStorage.setItem(JWT_KEY, t); }
export function clearToken()       { localStorage.removeItem(JWT_KEY); }

/** Inject Authorization header into fetch options if token present. */
export function withAuth(opts = {}) {
  const token = getToken();
  if (!token) return opts;
  return {
    ...opts,
    headers: { 'Content-Type': 'application/json', ...(opts.headers || {}), Authorization: `Bearer ${token}` },
  };
}

// ── Main entry point ───────────────────────────────────────────────────────

/**
 * Called from DOMContentLoaded in main.js.
 * Returns true if app should start normally, false if auth screen takes over.
 */
export async function initAuth() {
  const apiUrl = localStorage.getItem('apiUrl') || '';
  if (!apiUrl) return true; // No backend configured → show onboarding, not auth

  try {
    const r = await fetch(`${apiUrl}/api/status`, { signal: AbortSignal.timeout(5000) });
    if (!r.ok) return true; // Backend unreachable → open access
    const status = await r.json();

    if (!status.auth_enabled) { _removeOverlayIfPresent(); return true; }

    if (status.needs_setup) {
      showAuthScreen('setup');
      return false;
    }

    // Check existing JWT
    const token = getToken();
    if (token && await _validateToken(apiUrl, token)) {
      _removeOverlayIfPresent();
      return true;
    }

    showAuthScreen('login');
    return false;

  } catch(e) {
    console.warn('[Auth] Status check failed:', e.message);
    _removeOverlayIfPresent();
    return true; // Can't reach backend → open access (fail-open)
  }
}

function _removeOverlayIfPresent() {
  const overlay = document.getElementById('auth-overlay');
  if (overlay) { overlay.remove(); document.body.style.overflow = ''; }
}

async function _validateToken(apiUrl, token) {
  try {
    const r = await fetch(`${apiUrl}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: AbortSignal.timeout(5000),
    });
    if (r.ok) {
      const user = await r.json();
      _setCurrentUser(user);
      return true;
    }
    return false;
  } catch(e) {
    return false;
  }
}

// ── Auth Screen ────────────────────────────────────────────────────────────

export function showAuthScreen(tab = 'login') {
  let overlay = document.getElementById('auth-overlay');
  if (!overlay) {
    overlay = _buildAuthOverlay();
    document.body.appendChild(overlay);
  }
  switchAuthTab(tab);
  overlay.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

export function hideAuthScreen() {
  const overlay = document.getElementById('auth-overlay');
  if (overlay) {
    overlay.classList.add('auth-fade-out');
    setTimeout(() => { overlay.remove(); document.body.style.overflow = ''; }, 350);
  }
}

export function switchAuthTab(tab) {
  ['login', 'setup'].forEach(id => {
    const panel = document.getElementById(`auth-panel-${id}`);
    const btn   = document.getElementById(`auth-tab-${id}`);
    if (panel) panel.style.display = id === tab ? 'block' : 'none';
    if (btn)   btn.classList.toggle('active', id === tab);
  });
}

// ── Form handlers ──────────────────────────────────────────────────────────

export async function submitLogin() {
  const email    = document.getElementById('auth-email')?.value.trim();
  const password = document.getElementById('auth-password')?.value;
  const errEl    = document.getElementById('auth-login-error');
  const btn      = document.getElementById('auth-login-btn');

  if (!email || !password) { _setError(errEl, 'Bitte E-Mail und Passwort eingeben.'); return; }

  btn.disabled = true; btn.textContent = '⏳ Einloggen…';
  _setError(errEl, '');

  try {
    const apiUrl = localStorage.getItem('apiUrl') || '';
    const r = await fetch(`${apiUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await r.json();
    if (!r.ok) { _setError(errEl, data.detail || 'Login fehlgeschlagen.'); return; }
    setToken(data.token);
    _setCurrentUser(data.user);
    _updateSecurityTab(data.user);
    hideAuthScreen();
    // Reload app content with auth
    const { loadDashboard } = await import('./dashboard.js');
    loadDashboard();
  } catch(e) {
    _setError(errEl, 'Verbindungsfehler: ' + e.message);
  } finally {
    btn.disabled = false; btn.textContent = '→ Einloggen';
  }
}

export async function submitSetup() {
  const email    = document.getElementById('setup-email')?.value.trim();
  const password = document.getElementById('setup-password')?.value;
  const confirm  = document.getElementById('setup-confirm')?.value;
  const errEl    = document.getElementById('auth-setup-error');
  const btn      = document.getElementById('auth-setup-btn');

  if (!email || !password) { _setError(errEl, 'Bitte alle Felder ausfüllen.'); return; }
  if (password !== confirm)  { _setError(errEl, 'Passwörter stimmen nicht überein.'); return; }
  if (password.length < 8)   { _setError(errEl, 'Passwort muss mindestens 8 Zeichen haben.'); return; }

  btn.disabled = true; btn.textContent = '⏳ Erstelle Admin…';
  _setError(errEl, '');

  try {
    const apiUrl = localStorage.getItem('apiUrl') || '';
    const r = await fetch(`${apiUrl}/api/auth/setup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await r.json();
    if (!r.ok) { _setError(errEl, data.detail || 'Setup fehlgeschlagen.'); return; }
    setToken(data.token);
    _setCurrentUser(data.user);
    _updateSecurityTab(data.user);
    hideAuthScreen();
    const { loadDashboard } = await import('./dashboard.js');
    loadDashboard();
  } catch(e) {
    _setError(errEl, 'Verbindungsfehler: ' + e.message);
  } finally {
    btn.disabled = false; btn.textContent = '✓ Admin erstellen';
  }
}

export function logout() {
  clearToken();
  localStorage.removeItem('ws-current-user');
  location.reload();
}

// ── Admin panel (user management) ─────────────────────────────────────────

export async function loadAdminUsers() {
  const container = document.getElementById('admin-users-list');
  if (!container) return;
  const apiUrl = localStorage.getItem('apiUrl') || '';
  try {
    const r = await fetch(`${apiUrl}/api/admin/users`, withAuth());
    if (!r.ok) { container.innerHTML = '<div class="auth-error">Zugriff verweigert.</div>'; return; }
    const users = await r.json();
    container.innerHTML = users.map(u => `
      <div class="admin-user-row">
        <div class="admin-user-info">
          <span class="admin-user-email">${u.email}</span>
          <span class="admin-user-badge ${u.role}">${u.role}</span>
        </div>
        <button class="admin-user-delete" onclick="deleteAdminUser(${u.id})" title="Löschen">🗑️</button>
      </div>`).join('') || '<div style="color:var(--sub);font-size:.8rem">Keine weiteren Nutzer.</div>';
  } catch(e) { container.innerHTML = `<div class="auth-error">${e.message}</div>`; }
}

export async function createAdminUser() {
  const email    = document.getElementById('admin-new-email')?.value.trim();
  const password = document.getElementById('admin-new-password')?.value;
  const role     = document.getElementById('admin-new-role')?.value || 'user';
  const errEl    = document.getElementById('admin-create-error');

  if (!email || !password) { _setError(errEl, 'E-Mail und Passwort eingeben.'); return; }
  const apiUrl = localStorage.getItem('apiUrl') || '';
  try {
    const r = await fetch(`${apiUrl}/api/admin/users`, {
      ...withAuth(), method: 'POST',
      body: JSON.stringify({ email, password, role }),
    });
    const data = await r.json();
    if (!r.ok) { _setError(errEl, data.detail || 'Fehler.'); return; }
    _setError(errEl, '');
    document.getElementById('admin-new-email').value    = '';
    document.getElementById('admin-new-password').value = '';
    loadAdminUsers();
  } catch(e) { _setError(errEl, e.message); }
}

export async function deleteAdminUser(userId) {
  if (!confirm('Nutzer wirklich löschen?')) return;
  const apiUrl = localStorage.getItem('apiUrl') || '';
  await fetch(`${apiUrl}/api/admin/users/${userId}`, { ...withAuth(), method: 'DELETE' });
  loadAdminUsers();
}

export async function changePassword() {
  const curr  = document.getElementById('sec-current-pw')?.value;
  const newPw = document.getElementById('sec-new-pw')?.value;
  const conf  = document.getElementById('sec-confirm-pw')?.value;
  const errEl = document.getElementById('sec-pw-error');

  if (newPw !== conf) { _setError(errEl, 'Passwörter stimmen nicht überein.'); return; }
  if (newPw.length < 8) { _setError(errEl, 'Mindestens 8 Zeichen.'); return; }

  const apiUrl = localStorage.getItem('apiUrl') || '';
  try {
    const r = await fetch(`${apiUrl}/api/auth/change-password`, {
      ...withAuth(), method: 'POST',
      body: JSON.stringify({ current_password: curr, new_password: newPw }),
    });
    const data = await r.json();
    if (!r.ok) { _setError(errEl, data.detail || 'Fehler.'); return; }
    _setError(errEl, '');
    errEl.textContent = '✅ ' + data.message;
    errEl.style.color = 'var(--green)';
    ['sec-current-pw','sec-new-pw','sec-confirm-pw'].forEach(id => {
      const el = document.getElementById(id); if (el) el.value = '';
    });
  } catch(e) { _setError(errEl, e.message); }
}

// ── Internal helpers ───────────────────────────────────────────────────────

function _setError(el, msg) {
  if (!el) return;
  el.textContent = msg;
  el.style.color = msg ? 'var(--red)' : '';
}

function _setCurrentUser(user) {
  localStorage.setItem('ws-current-user', JSON.stringify(user));
}

function _updateSecurityTab(user) {
  const emailEl = document.getElementById('sec-current-email');
  if (emailEl) emailEl.textContent = user.email;
  const roleEl  = document.getElementById('sec-current-role');
  if (roleEl)   roleEl.textContent = user.role;
  // Show/hide admin tab
  const adminTab = document.getElementById('tab-adminusers');
  if (adminTab) adminTab.style.display = user.role === 'admin' ? 'block' : 'none';
}

function _buildAuthOverlay() {
  const el = document.createElement('div');
  el.id = 'auth-overlay';
  el.innerHTML = `
    <div class="auth-card">
      <div class="auth-logo">🧭</div>
      <h1 class="auth-title">WanderSuite</h1>

      <div class="auth-tabs">
        <button class="auth-tab active" id="auth-tab-login" onclick="switchAuthTab('login')">Einloggen</button>
        <button class="auth-tab" id="auth-tab-setup" onclick="switchAuthTab('setup')">Ersteinrichtung</button>
      </div>

      <!-- Login Panel -->
      <div id="auth-panel-login">
        <div class="auth-field">
          <label>E-Mail</label>
          <input id="auth-email" type="email" placeholder="admin@example.com"
                 onkeydown="if(event.key==='Enter')document.getElementById('auth-password').focus()">
        </div>
        <div class="auth-field">
          <label>Passwort</label>
          <input id="auth-password" type="password" placeholder="••••••••"
                 onkeydown="if(event.key==='Enter')submitLogin()">
        </div>
        <div id="auth-login-error" class="auth-error"></div>
        <button class="auth-submit" id="auth-login-btn" onclick="submitLogin()">→ Einloggen</button>
      </div>

      <!-- Setup Panel -->
      <div id="auth-panel-setup" style="display:none">
        <div style="font-size:.8rem;color:var(--sub);margin-bottom:1rem;text-align:center;font-style:italic">
          Erstelle den ersten Admin-Account für WanderSuite.
        </div>
        <div class="auth-field">
          <label>E-Mail</label>
          <input id="setup-email" type="email" placeholder="admin@example.com">
        </div>
        <div class="auth-field">
          <label>Passwort <span style="color:var(--muted);font-size:.65rem">(mind. 8 Zeichen)</span></label>
          <input id="setup-password" type="password" placeholder="••••••••">
        </div>
        <div class="auth-field">
          <label>Passwort bestätigen</label>
          <input id="setup-confirm" type="password" placeholder="••••••••"
                 onkeydown="if(event.key==='Enter')submitSetup()">
        </div>
        <div id="auth-setup-error" class="auth-error"></div>
        <button class="auth-submit" id="auth-setup-btn" onclick="submitSetup()">✓ Admin erstellen</button>
      </div>
    </div>`;
  return el;
}

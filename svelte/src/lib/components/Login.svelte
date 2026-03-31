<script>
  import { apiUrl, jwtToken, currentUser } from '$lib/stores.js';
  import { api } from '$lib/api.js';
  import { toast } from '$lib/toast.js';
  import { t } from '$lib/i18n.js';
  import { get } from 'svelte/store';

  let { onDone } = $props();

  let email     = $state('');
  let password  = $state('');
  let loading   = $state(false);
  let pkLoading = $state(false);
  let error     = $state('');
  let showPassword = $state(false);

  // ── Passkey Login ───────────────────────────────────────────────────────────
  async function loginWithPasskey() {
    if (!window.PublicKeyCredential) {
      error = 'Passkeys werden von diesem Browser nicht unterstützt.';
      return;
    }
    pkLoading = true; error = '';
    try {
      // 1. Get challenge from backend
      const options = await api('/api/auth/passkeys/login/begin', { method: 'POST' });

      // 2. Ask browser for passkey
      const credential = await navigator.credentials.get({
        publicKey: {
          ...options,
          challenge: _base64urlToBuffer(options.challenge),
          allowCredentials: (options.allowCredentials || []).map(c => ({
            ...c,
            id: _base64urlToBuffer(c.id),
          })),
        },
      });

      if (!credential) { pkLoading = false; return; }

      // 3. Verify with backend
      const r = await api('/api/auth/passkeys/login/complete', {
        method: 'POST',
        body: JSON.stringify({ credential: _credentialToJSON(credential) }),
      });

      jwtToken.set(r.token);
      currentUser.set(r.user);
      toast('🔑 ' + r.user.email, 'success');
      onDone?.();
    } catch (e) {
      if (e.name === 'NotAllowedError') {
        error = 'Passkey abgebrochen.';
      } else {
        error = e.message || 'Passkey-Login fehlgeschlagen.';
      }
    }
    pkLoading = false;
  }

  // ── Password Login ──────────────────────────────────────────────────────────
  async function loginWithPassword() {
    if (!email || !password) { error = 'E-Mail und Passwort eingeben.'; return; }
    loading = true; error = '';
    try {
      const r = await api('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      jwtToken.set(r.token);
      currentUser.set(r.user);
      toast('👋 ' + r.user.email, 'success');
      onDone?.();
    } catch (e) {
      error = e.message.includes('401') ? 'E-Mail oder Passwort falsch.' : e.message;
    }
    loading = false;
  }

  function onKeydown(e) { if (e.key === 'Enter') loginWithPassword(); }

  // ── WebAuthn helpers ────────────────────────────────────────────────────────
  function _base64urlToBuffer(base64url) {
    const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
    const bin = atob(base64);
    return Uint8Array.from(bin, c => c.charCodeAt(0)).buffer;
  }

  function _bufferToBase64url(buffer) {
    const bytes = new Uint8Array(buffer);
    let bin = '';
    bytes.forEach(b => bin += String.fromCharCode(b));
    return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
  }

  function _credentialToJSON(cred) {
    return {
      id: cred.id,
      rawId: _bufferToBase64url(cred.rawId),
      type: cred.type,
      response: {
        clientDataJSON:    _bufferToBase64url(cred.response.clientDataJSON),
        authenticatorData: _bufferToBase64url(cred.response.authenticatorData),
        signature:         _bufferToBase64url(cred.response.signature),
        userHandle: cred.response.userHandle
          ? _bufferToBase64url(cred.response.userHandle)
          : null,
      },
    };
  }

  const passkeySupported = typeof window !== 'undefined' && !!window.PublicKeyCredential;
</script>

<div class="fixed inset-0 flex items-center justify-center p-4" style="background:var(--ws-bg)">
  <div class="w-full max-w-sm">

    <div class="text-center mb-8">
      <div class="text-5xl mb-3">🧭</div>
      <h1 class="text-2xl font-bold" style="color:var(--ws-accent)">WanderSuite</h1>
      <p class="text-sm mt-1" style="color:var(--ws-muted)">Anmelden</p>
    </div>

    <div class="rounded-2xl border overflow-hidden" style="background:var(--ws-surface);border-color:var(--ws-border)">

      <!-- Passkey Button (primary) -->
      {#if passkeySupported}
        <div class="p-6 pb-4">
          <button
            onclick={loginWithPasskey}
            disabled={pkLoading}
            class="w-full py-3 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 transition-opacity disabled:opacity-50"
            style="background:var(--ws-accent);color:#fff5ec"
          >
            {#if pkLoading}
              ⏳ Warte auf Passkey…
            {:else}
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/>
              </svg>
              Mit Passkey anmelden
            {/if}
          </button>
        </div>

        <!-- Divider -->
        <div class="flex items-center gap-3 px-6 pb-4">
          <div class="flex-1 h-px" style="background:var(--ws-border)"></div>
          <span class="text-xs" style="color:var(--ws-muted)">oder</span>
          <div class="flex-1 h-px" style="background:var(--ws-border)"></div>
        </div>
      {/if}

      <!-- Password fallback -->
      <div class="px-6 pb-6 space-y-3">
        {#if !showPassword && passkeySupported}
          <button
            onclick={() => showPassword = true}
            class="w-full py-2.5 rounded-xl text-sm font-medium border transition-opacity hover:opacity-70"
            style="border-color:var(--ws-border);color:var(--ws-muted);background:var(--ws-surface2)"
          >
            Mit Passwort anmelden
          </button>
        {:else}
          <div>
            <label class="text-xs font-bold uppercase tracking-wider block mb-1.5" style="color:var(--ws-muted)">
              E-Mail
            </label>
            <input type="email" bind:value={email} placeholder="admin@example.com"
              onkeydown={onKeydown}
              class="w-full px-3 py-2.5 rounded-xl border text-sm"
              style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          </div>
          <div>
            <label class="text-xs font-bold uppercase tracking-wider block mb-1.5" style="color:var(--ws-muted)">
              Passwort
            </label>
            <input type="password" bind:value={password} placeholder="••••••••"
              onkeydown={onKeydown}
              class="w-full px-3 py-2.5 rounded-xl border text-sm"
              style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          </div>
          <button onclick={loginWithPassword} disabled={loading}
            class="w-full py-2.5 rounded-xl text-sm font-semibold transition-opacity disabled:opacity-50"
            style="background:var(--ws-surface2);border:1px solid var(--ws-border);color:var(--ws-text)">
            {loading ? '⏳ Anmelden…' : '→ Anmelden'}
          </button>
        {/if}
      </div>
    </div>

    {#if error}
      <p class="text-xs text-center mt-4 px-3 py-2 rounded-xl"
        style="background:rgba(220,38,38,.1);color:#dc2626">{error}</p>
    {/if}

  </div>
</div>

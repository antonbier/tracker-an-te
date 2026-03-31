<script>
  import { api } from '$lib/api.js';
  import { toast } from '$lib/toast.js';

  let { userId } = $props();

  let passkeys    = $state([]);
  let loading     = $state(true);
  let registering = $state(false);
  let deviceName  = $state('');
  let error       = $state('');

  $effect(() => { loadPasskeys(); });

  async function loadPasskeys() {
    loading = true;
    try { passkeys = await api('/api/auth/passkeys'); }
    catch { passkeys = []; }
    loading = false;
  }

  async function addPasskey() {
    if (!window.PublicKeyCredential) {
      error = 'Passkeys werden von diesem Browser nicht unterstützt.';
      return;
    }
    registering = true; error = '';
    try {
      // 1. Get registration options
      const options = await api('/api/auth/passkeys/register/begin', {
        method: 'POST',
        body: JSON.stringify({ device_name: deviceName || 'Passkey' }),
      });

      // 2. Create passkey in browser
      const credential = await navigator.credentials.create({
        publicKey: {
          ...options,
          challenge: _base64urlToBuffer(options.challenge),
          user: {
            ...options.user,
            id: _base64urlToBuffer(options.user.id),
          },
          excludeCredentials: (options.excludeCredentials || []).map(c => ({
            ...c,
            id: _base64urlToBuffer(c.id),
          })),
        },
      });

      if (!credential) { registering = false; return; }

      // 3. Send to backend
      await api('/api/auth/passkeys/register/complete', {
        method: 'POST',
        body: JSON.stringify({
          credential: _credentialToJSON(credential),
          device_name: deviceName || 'Passkey',
        }),
      });

      toast('Passkey hinzugefügt ✓', 'success');
      deviceName = '';
      await loadPasskeys();
    } catch (e) {
      if (e.name === 'NotAllowedError') {
        error = 'Passkey-Erstellung abgebrochen.';
      } else {
        error = e.message || 'Passkey-Registrierung fehlgeschlagen.';
      }
    }
    registering = false;
  }

  async function removePasskey(id, name) {
    if (!confirm(`Passkey "${name}" löschen?`)) return;
    try {
      await api(`/api/auth/passkeys/${id}`, { method: 'DELETE' });
      toast('Passkey gelöscht', 'success');
      await loadPasskeys();
    } catch (e) { toast(e.message, 'error'); }
  }

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
        attestationObject: _bufferToBase64url(cred.response.attestationObject),
      },
    };
  }

  const supported = typeof window !== 'undefined' && !!window.PublicKeyCredential;
</script>

<div class="space-y-4">
  <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">
    🔑 Passkeys
  </div>

  {#if !supported}
    <p class="text-xs p-3 rounded-xl" style="background:var(--ws-surface2);color:var(--ws-muted)">
      Dein Browser unterstützt keine Passkeys.
    </p>
  {:else}
    <!-- Existing passkeys -->
    {#if loading}
      <p class="text-xs" style="color:var(--ws-muted)">Lade…</p>
    {:else if passkeys.length === 0}
      <p class="text-xs" style="color:var(--ws-muted)">Noch keine Passkeys registriert.</p>
    {:else}
      <div class="space-y-2">
        {#each passkeys as pk}
          <div class="flex items-center gap-2 px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border)">
            <span>🔑</span>
            <div class="flex-1 min-w-0">
              <div class="font-medium truncate" style="color:var(--ws-text)">{pk.device_name}</div>
              <div class="text-xs" style="color:var(--ws-muted)">{pk.created_at?.slice(0,10)}</div>
            </div>
            <button
              onclick={() => removePasskey(pk.id, pk.device_name)}
              class="text-xs px-2 py-0.5 rounded-lg border shrink-0"
              style="border-color:var(--ws-border);color:var(--ws-muted)">✕</button>
          </div>
        {/each}
      </div>
    {/if}

    <!-- Add new passkey -->
    <div class="space-y-2">
      <input
        bind:value={deviceName}
        placeholder="Gerätename (z.B. MacBook, iPhone)"
        class="w-full px-3 py-2 rounded-xl border text-sm"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"
      />
      {#if error}
        <p class="text-xs px-3 py-2 rounded-lg" style="background:rgba(220,38,38,.1);color:#dc2626">{error}</p>
      {/if}
      <button
        onclick={addPasskey}
        disabled={registering}
        class="w-full py-2 rounded-xl text-sm font-semibold border transition-opacity disabled:opacity-50"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"
      >
        {registering ? '⏳ Warte auf Browser…' : '+ Passkey hinzufügen'}
      </button>
      <p class="text-xs" style="color:var(--ws-muted)">
        Funktioniert nur über HTTPS oder localhost.
      </p>
    </div>
  {/if}
</div>

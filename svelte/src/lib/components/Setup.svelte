<script>
  import { jwtToken, currentUser } from '$lib/stores.js';
  import { api } from '$lib/api.js';
  import { toast } from '$lib/toast.js';

  let { onDone } = $props();

  let email     = $state('');
  let password  = $state('');
  let password2 = $state('');
  let loading   = $state(false);
  let error     = $state('');

  async function setup() {
    if (!email || !password) { error = 'Alle Felder ausfüllen.'; return; }
    if (password.length < 8)  { error = 'Passwort mind. 8 Zeichen.'; return; }
    if (password !== password2){ error = 'Passwörter stimmen nicht überein.'; return; }
    loading = true; error = '';
    try {
      const r = await api('/api/auth/setup', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      jwtToken.set(r.token);
      currentUser.set(r.user);
      toast('Admin-Account erstellt ✓', 'success');
      onDone?.();
    } catch (e) {
      error = e.message;
    }
    loading = false;
  }
</script>

<div class="fixed inset-0 flex items-center justify-center p-4" style="background:var(--ws-bg)">
  <div class="w-full max-w-sm">

    <div class="text-center mb-8">
      <div class="text-5xl mb-3">🔐</div>
      <h1 class="text-2xl font-bold" style="color:var(--ws-accent)">WanderSuite Setup</h1>
      <p class="text-sm mt-1" style="color:var(--ws-muted)">Ersten Admin-Account erstellen</p>
    </div>

    <div class="rounded-2xl p-6 border space-y-4" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <div>
        <label class="text-xs font-bold uppercase tracking-wider block mb-1.5" style="color:var(--ws-muted)">E-Mail</label>
        <input type="email" bind:value={email} placeholder="admin@example.com"
          class="w-full px-3 py-2.5 rounded-xl border text-sm"
          style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      </div>
      <div>
        <label class="text-xs font-bold uppercase tracking-wider block mb-1.5" style="color:var(--ws-muted)">Passwort</label>
        <input type="password" bind:value={password} placeholder="mind. 8 Zeichen"
          class="w-full px-3 py-2.5 rounded-xl border text-sm"
          style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      </div>
      <div>
        <label class="text-xs font-bold uppercase tracking-wider block mb-1.5" style="color:var(--ws-muted)">Passwort bestätigen</label>
        <input type="password" bind:value={password2} placeholder="••••••••"
          class="w-full px-3 py-2.5 rounded-xl border text-sm"
          style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      </div>

      {#if error}
        <p class="text-xs px-3 py-2 rounded-lg" style="background:rgba(220,38,38,.1);color:#dc2626">{error}</p>
      {/if}

      <button onclick={setup} disabled={loading}
        class="w-full py-2.5 rounded-xl text-sm font-semibold transition-opacity disabled:opacity-50"
        style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
        {loading ? '⏳ Erstelle Account…' : '🔐 Account erstellen'}
      </button>
    </div>

    <p class="text-xs text-center mt-4" style="color:var(--ws-muted)">
      AUTH_ENABLED=true — dieser Account ist der einzige Admin.
    </p>
  </div>
</div>

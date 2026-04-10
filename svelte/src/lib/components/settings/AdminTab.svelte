<script>
  import { t } from '$lib/i18n.js';
  import { api } from '$lib/api.js';
  import { toast } from '$lib/toast.js';

  let { currentUserId } = $props();

  let adminUsers   = $state([]);
  let adminLoading = $state(false);
  let newEmail     = $state('');
  let newPassword  = $state('');
  let newRole      = $state('user');
  let adminError   = $state('');

  async function loadAdminUsers() {
    adminLoading = true;
    try { adminUsers = await api('/api/admin/users'); }
    catch { adminUsers = []; }
    adminLoading = false;
  }

  async function createUser() {
    if (!newEmail || !newPassword) { adminError = 'E-Mail und Passwort eingeben.'; return; }
    adminError = '';
    try {
      await api('/api/admin/users', {
        method: 'POST',
        body: JSON.stringify({ email: newEmail, password: newPassword, role: newRole }),
      });
      newEmail = newPassword = ''; newRole = 'user';
      toast('User erstellt ✓', 'success');
      await loadAdminUsers();
    } catch (e) { adminError = e.message; }
  }

  async function deleteUser(id, email) {
    if (!confirm(`User ${email} löschen?`)) return;
    try {
      await api(`/api/admin/users/${id}`, { method: 'DELETE' });
      toast('User gelöscht', 'success');
      await loadAdminUsers();
    } catch (e) { toast(e.message, 'error'); }
  }

  // Load on mount
  $effect(() => { loadAdminUsers(); });
</script>

<!-- User list -->
<div class="space-y-2">
  <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('settingsUsers')}</div>
  {#if adminLoading}
    <p class="text-xs" style="color:var(--ws-muted)">Lade…</p>
  {:else}
    {#each adminUsers as u}
      <div class="flex items-center gap-2 px-3 py-2 rounded-xl border text-sm"
        style="background:var(--ws-surface2);border-color:var(--ws-border)">
        <span class="flex-1 truncate" style="color:var(--ws-text)">{u.email}</span>
        <span class="text-xs px-2 py-0.5 rounded-full"
          style="background:{u.role==='admin'?'rgba(196,98,45,.15)':'rgba(42,92,69,.1)'};color:{u.role==='admin'?'var(--ws-accent)':'var(--ws-green)'}">
          {u.role}
        </span>
        {#if u.id !== currentUserId}
          <button onclick={() => deleteUser(u.id, u.email)}
            class="text-xs px-2 py-0.5 rounded-lg border"
            style="border-color:var(--ws-border);color:var(--ws-muted)">✕</button>
        {/if}
      </div>
    {/each}
  {/if}
</div>

<hr style="border-color:var(--ws-border)"/>

<!-- Create user -->
<div class="space-y-2">
  <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('settingsCreateUser')}</div>
  <input bind:value={newEmail} type="email" placeholder="E-Mail"
    class="w-full px-3 py-2 rounded-xl border text-sm"
    style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
  <input bind:value={newPassword} type="password" placeholder="Passwort (mind. 8)"
    class="w-full px-3 py-2 rounded-xl border text-sm"
    style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
  <div class="flex gap-2">
    {#each ['user','admin'] as r}
      <button onclick={() => newRole = r}
        class="flex-1 py-1.5 rounded-xl text-xs border font-medium transition-all"
        style={newRole === r
          ? 'background:var(--ws-accent);color:#fff;border-color:var(--ws-accent)'
          : 'background:var(--ws-surface2);color:var(--ws-muted);border-color:var(--ws-border)'}>
        {r}
      </button>
    {/each}
  </div>
  {#if adminError}
    <p class="text-xs px-3 py-2 rounded-lg" style="background:rgba(220,38,38,.1);color:#dc2626">{adminError}</p>
  {/if}
  <button onclick={createUser}
    class="w-full py-2.5 rounded-xl text-sm font-semibold transition-opacity hover:opacity-80"
    style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
    {$t('settingsCreateUserBtn')}
  </button>
</div>

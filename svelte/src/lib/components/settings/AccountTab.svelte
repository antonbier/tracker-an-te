<script>
  import { t } from '$lib/i18n.js';
  import { api } from '$lib/api.js';
  import { toast } from '$lib/toast.js';
  import PasskeyManager from '../PasskeyManager.svelte';

  let { userId, userEmail, userRole } = $props();

  let pwCurrent = $state('');
  let pwNew     = $state('');
  let pwNew2    = $state('');
  let pwLoading = $state(false);
  let pwError   = $state('');
  let pwOk      = $state(false);

  async function changePassword() {
    if (!pwCurrent || !pwNew) { pwError = 'Alle Felder ausfüllen.'; return; }
    if (pwNew.length < 8)     { pwError = 'Neues Passwort mind. 8 Zeichen.'; return; }
    if (pwNew !== pwNew2)     { pwError = 'Passwörter stimmen nicht überein.'; return; }
    pwLoading = true; pwError = ''; pwOk = false;
    try {
      await api('/api/auth/change-password', {
        method: 'POST',
        body: JSON.stringify({ current_password: pwCurrent, new_password: pwNew }),
      });
      pwOk = true;
      pwCurrent = pwNew = pwNew2 = '';
      toast('Passwort geändert ✓', 'success');
    } catch (e) {
      pwError = e.message.includes('401') ? 'Aktuelles Passwort falsch.' : e.message;
    }
    pwLoading = false;
  }
</script>

<div class="space-y-1 mb-4">
  <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('settingsLoggedInAs')}</div>
  <div class="px-3 py-2 rounded-xl text-sm font-medium" style="background:var(--ws-surface2);color:var(--ws-text)">
    {userEmail} <span class="text-xs ml-1" style="color:var(--ws-muted)">({userRole})</span>
  </div>
</div>

<hr style="border-color:var(--ws-border)"/>

<form onsubmit={(e) => { e.preventDefault(); changePassword(); }} autocomplete="on">
<div class="space-y-3">
  <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('settingsChangePassword')}</div>
  <input type="password" bind:value={pwCurrent} placeholder="Aktuelles Passwort"
    autocomplete="current-password"
    class="w-full px-3 py-2 rounded-xl border text-sm"
    style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
  <input type="password" bind:value={pwNew} placeholder="Neues Passwort (mind. 8)"
    autocomplete="new-password"
    class="w-full px-3 py-2 rounded-xl border text-sm"
    style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
  <input type="password" bind:value={pwNew2} placeholder="Bestätigen"
    autocomplete="new-password"
    class="w-full px-3 py-2 rounded-xl border text-sm"
    style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
  {#if pwError}
    <p class="text-xs px-3 py-2 rounded-lg" style="background:rgba(220,38,38,.1);color:#dc2626">{pwError}</p>
  {/if}
  {#if pwOk}
    <p class="text-xs px-3 py-2 rounded-lg" style="background:rgba(42,92,69,.1);color:var(--ws-green)">✓ Passwort geändert</p>
  {/if}
  <button type="submit" disabled={pwLoading}
    class="w-full py-2.5 rounded-xl text-sm font-semibold border transition-opacity disabled:opacity-50"
    style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)">
    {pwLoading ? '⏳…' : $t('settingsChangePasswordBtn')}
  </button>
</div>
</form>

<hr style="border-color:var(--ws-border)"/>
<PasskeyManager {userId} />

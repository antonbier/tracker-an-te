<script>
  import { t } from '$lib/i18n.js';
  import { api } from '$lib/api.js';
  import { apiUrl } from '$lib/stores.js';
  import { toast } from '$lib/toast.js';
  import { onMount } from 'svelte';

  let contacts = $state([]);
  let notes    = $state('');
  let loading  = $state(true);
  let saving   = $state(false);

  // ── Notfall-Karte (druckbare/teilbare öffentliche Ansicht) ────────────────
  let cardToken   = $state('');
  let cardLoading = $state(false);
  let cardCopied  = $state(false);
  const cardUrl = $derived(cardToken ? `${$apiUrl}/api/emergency/card/${cardToken}` : '');

  async function loadCardToken() {
    if (!$apiUrl || cardToken) return;
    cardLoading = true;
    try {
      const res = await api('/api/emergency/token');
      cardToken = res?.token || '';
    } catch {}
    cardLoading = false;
  }

  async function copyCardUrl() {
    if (!cardUrl) return;
    try {
      await navigator.clipboard.writeText(cardUrl);
      cardCopied = true;
      setTimeout(() => cardCopied = false, 2000);
    } catch {}
  }

  async function load() {
    loading = true;
    try {
      const res = await api('/api/emergency');
      contacts = res?.contacts || [];
      notes    = res?.notes    || '';
    } catch {
      contacts = []; notes = '';
    }
    loading = false;
  }

  onMount(load);

  function addContact() {
    contacts = [...contacts, { name: '', phone: '', relation: '' }];
  }

  function removeContact(i) {
    contacts = contacts.filter((_, idx) => idx !== i);
  }

  async function save() {
    saving = true;
    try {
      const cleanContacts = contacts.filter(c => c.name.trim() && c.phone.trim());
      await api('/api/emergency', {
        method: 'PUT',
        body: JSON.stringify({ contacts: cleanContacts, notes }),
      });
      contacts = cleanContacts;
      toast($t('toastSaved'), 'success');
    } catch (e) {
      toast(e.message || 'Fehler', 'error');
    }
    saving = false;
  }
</script>

<div class="space-y-4">
  <p class="text-xs" style="color:var(--ws-muted)">{$t('emergencyHint')}</p>

  {#if loading}
    <p class="text-xs" style="color:var(--ws-muted)">⏳…</p>
  {:else}
    <!-- Kontakte -->
    <div class="space-y-2">
      <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('emergencyContacts')}</div>
      {#each contacts as contact, i}
        <div class="flex gap-2 items-center rounded-xl border p-2" style="background:var(--ws-surface2);border-color:var(--ws-border)">
          <div class="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-2">
            <input bind:value={contact.name} placeholder={$t('emergencyName')}
              class="px-2.5 py-1.5 rounded-lg border text-xs"
              style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)"/>
            <input bind:value={contact.phone} placeholder={$t('emergencyPhone')} type="tel"
              class="px-2.5 py-1.5 rounded-lg border text-xs"
              style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)"/>
            <input bind:value={contact.relation} placeholder={$t('emergencyRelation')}
              class="px-2.5 py-1.5 rounded-lg border text-xs"
              style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)"/>
          </div>
          <button onclick={() => removeContact(i)} class="text-xs px-1.5 py-0.5 rounded hover:opacity-70 shrink-0" style="color:var(--ws-muted)">✕</button>
        </div>
      {/each}
      <button onclick={addContact}
        class="w-full py-2 rounded-xl text-xs font-semibold border hover:opacity-80"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-accent)">
        ➕ {$t('emergencyAddContact')}
      </button>
    </div>

    <!-- Notizen -->
    <div class="space-y-1">
      <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('emergencyNotes')}</div>
      <textarea bind:value={notes} rows="4" placeholder={$t('emergencyNotesPlaceholder')}
        class="w-full px-3 py-2 rounded-xl border text-sm resize-none"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"></textarea>
    </div>

    <button onclick={save} disabled={saving}
      class="w-full py-2.5 rounded-xl text-sm font-semibold disabled:opacity-40 hover:opacity-90"
      style="background:var(--ws-accent);color:#fff">
      {saving ? '⏳…' : ('💾 ' + $t('settingsSave'))}
    </button>

    <!-- Notfall-Karte -->
    <div class="rounded-xl border p-3 space-y-2" style="background:var(--ws-surface2);border-color:var(--ws-border)">
      <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">🖨️ {$t('emergencyCardTitle')}</div>
      <p class="text-xs" style="color:var(--ws-muted)">{$t('emergencyCardHint')}</p>
      {#if !cardToken}
        <button onclick={loadCardToken} disabled={cardLoading || !$apiUrl}
          class="px-4 py-2 rounded-xl text-xs border font-semibold transition-opacity hover:opacity-70 disabled:opacity-40"
          style="border-color:var(--ws-border);color:var(--ws-accent);background:var(--ws-surface)">
          {cardLoading ? '⏳…' : $t('emergencyCardGenerate')}
        </button>
      {:else}
        <div class="flex gap-2">
          <input readonly value={cardUrl}
            class="flex-1 px-3 py-2 rounded-xl border text-xs font-mono"
            style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)"/>
          <button onclick={copyCardUrl}
            class="px-3 py-2 rounded-xl text-xs border font-semibold transition-opacity hover:opacity-70"
            style="border-color:var(--ws-border);color:var(--ws-accent);background:var(--ws-surface)">
            {cardCopied ? '✓' : '📋'}
          </button>
          <a href={cardUrl} target="_blank" rel="noopener noreferrer"
            class="px-3 py-2 rounded-xl text-xs border font-semibold transition-opacity hover:opacity-70 flex items-center"
            style="border-color:var(--ws-border);color:var(--ws-accent);background:var(--ws-surface)">
            ↗
          </a>
        </div>
      {/if}
    </div>
  {/if}
</div>

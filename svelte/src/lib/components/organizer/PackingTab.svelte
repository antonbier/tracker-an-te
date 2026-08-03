<script>
  import { t } from '$lib/i18n.js';
  import { api } from '$lib/api.js';
  import { toast } from '$lib/toast.js';
  import { onMount } from 'svelte';

  let templates      = $state([]);
  let loading        = $state(true);
  let expandedId     = $state(null);
  let newName        = $state('');
  let creating       = $state(false);
  let newItemText    = $state('');
  let addingItem     = $state(false);
  let catalogs       = $state([]);
  let catalogLoading = $state(null); // key des gerade übernommenen Katalogs, sonst null

  async function loadTemplates() {
    loading = true;
    try {
      templates = await api('/api/packing-templates');
    } catch {
      templates = [];
    }
    loading = false;
  }

  async function loadCatalogs() {
    try {
      catalogs = await api('/api/packing-templates/catalog');
    } catch {
      catalogs = [];
    }
  }

  onMount(() => { loadTemplates(); loadCatalogs(); });

  async function adoptCatalog(cat) {
    catalogLoading = cat.key;
    try {
      const res = await api('/api/packing-templates/from-catalog', {
        method: 'POST',
        body: JSON.stringify({ catalog_key: cat.key }),
      });
      await loadTemplates();
      if (res?.id) expandedId = res.id;
      toast($t('packingCatalogAdopted'), 'success');
    } catch (e) {
      toast(e.message || 'Fehler', 'error');
    }
    catalogLoading = null;
  }

  function progress(tpl) {
    const total = tpl.items.length;
    const done  = tpl.items.filter(i => i.is_done).length;
    return { total, done };
  }

  async function createTemplate() {
    if (!newName.trim()) return;
    creating = true;
    try {
      const res = await api('/api/packing-templates', {
        method: 'POST',
        body: JSON.stringify({ name: newName.trim() }),
      });
      newName = '';
      await loadTemplates();
      if (res?.id) expandedId = res.id;
    } catch (e) {
      toast(e.message || 'Fehler', 'error');
    }
    creating = false;
  }

  async function removeTemplate(tpl) {
    if (!confirm($t('packingDeleteConfirm'))) return;
    try {
      await api(`/api/packing-templates/${tpl.id}`, { method: 'DELETE' });
      templates = templates.filter(t => t.id !== tpl.id);
      if (expandedId === tpl.id) expandedId = null;
    } catch (e) {
      toast(e.message || 'Fehler', 'error');
    }
  }

  async function addItem(tpl) {
    if (!newItemText.trim()) return;
    addingItem = true;
    try {
      await api(`/api/packing-templates/${tpl.id}/items`, {
        method: 'POST',
        body: JSON.stringify({ text: newItemText.trim() }),
      });
      newItemText = '';
      await loadTemplates();
    } catch (e) {
      toast(e.message || 'Fehler', 'error');
    }
    addingItem = false;
  }

  async function toggleItem(item) {
    // Optimistisch umschalten, damit Checkboxen sofort reagieren.
    templates = templates.map(t => ({
      ...t,
      items: t.items.map(i => i.id === item.id ? { ...i, is_done: i.is_done ? 0 : 1 } : i),
    }));
    try {
      await api(`/api/packing-templates/items/${item.id}/toggle`, { method: 'PATCH' });
    } catch (e) {
      toast(e.message || 'Fehler', 'error');
      await loadTemplates();
    }
  }

  async function removeItem(item) {
    try {
      await api(`/api/packing-templates/items/${item.id}`, { method: 'DELETE' });
      templates = templates.map(t => ({ ...t, items: t.items.filter(i => i.id !== item.id) }));
    } catch (e) {
      toast(e.message || 'Fehler', 'error');
    }
  }

  async function resetTemplate(tpl) {
    if (!confirm($t('packingResetConfirm'))) return;
    try {
      await api(`/api/packing-templates/${tpl.id}/reset`, { method: 'POST' });
      await loadTemplates();
    } catch (e) {
      toast(e.message || 'Fehler', 'error');
    }
  }
</script>

<div class="space-y-4">
  <p class="text-xs" style="color:var(--ws-muted)">{$t('packingHint')}</p>

  <!-- Kataloge: Ein-Klick-Übernahme -->
  {#if catalogs.length > 0}
    <div class="space-y-1.5">
      <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('packingCatalogTitle')}</div>
      <div class="flex gap-2 overflow-x-auto pb-1">
        {#each catalogs as cat}
          <button onclick={() => adoptCatalog(cat)} disabled={catalogLoading === cat.key}
            title={cat.items.join(', ')}
            class="shrink-0 px-3 py-2 rounded-xl border text-xs font-semibold whitespace-nowrap transition-opacity hover:opacity-80 disabled:opacity-40"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)">
            {catalogLoading === cat.key ? '⏳' : cat.label}
          </button>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Neue Liste -->
  <div class="flex gap-2">
    <input bind:value={newName} placeholder={$t('packingNewPlaceholder')}
      onkeydown={(e) => e.key === 'Enter' && createTemplate()}
      class="flex-1 px-3 py-2 rounded-xl border text-sm"
      style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
    <button onclick={createTemplate} disabled={creating || !newName.trim()}
      class="px-4 py-2 rounded-xl text-sm font-semibold disabled:opacity-40"
      style="background:var(--ws-accent);color:#fff">
      {creating ? '⏳' : ('➕ ' + $t('packingNewBtn'))}
    </button>
  </div>

  {#if loading}
    <p class="text-xs" style="color:var(--ws-muted)">⏳…</p>
  {:else if templates.length === 0}
    <p class="text-xs text-center py-4" style="color:var(--ws-muted)">{$t('packingEmpty')}</p>
  {:else}
    <div class="space-y-2">
      {#each templates as tpl (tpl.id)}
        {@const p = progress(tpl)}
        <div class="rounded-xl border overflow-hidden" style="border-color:var(--ws-border)">
          <button onclick={() => expandedId = expandedId === tpl.id ? null : tpl.id}
            class="w-full flex items-center gap-2 px-3 py-2.5 text-left"
            style="background:var(--ws-surface2)">
            <span class="text-lg shrink-0">🧳</span>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium truncate" style="color:var(--ws-text)">{tpl.name}</div>
              {#if p.total > 0}
                <div class="text-[10px]" style="color:var(--ws-muted)">{p.done}/{p.total}</div>
              {/if}
            </div>
            <span style="color:var(--ws-muted)">{expandedId === tpl.id ? '▲' : '▼'}</span>
          </button>

          {#if expandedId === tpl.id}
            <div class="p-3 space-y-2 border-t" style="border-color:var(--ws-border)">
              {#each tpl.items as item (item.id)}
                <div class="flex items-center gap-2">
                  <button onclick={() => toggleItem(item)}
                    class="shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center transition-all"
                    style="border-color:{item.is_done ? 'var(--ws-accent)' : 'var(--ws-border)'};background:{item.is_done ? 'var(--ws-accent)' : 'transparent'}">
                    {#if item.is_done}<span class="text-[10px] text-white font-bold">✓</span>{/if}
                  </button>
                  <span class="flex-1 text-sm {item.is_done ? 'line-through' : ''}"
                    style="color:{item.is_done ? 'var(--ws-muted)' : 'var(--ws-text)'}">{item.text}</span>
                  <button onclick={() => removeItem(item)} class="text-xs px-1.5 py-0.5 rounded hover:opacity-70" style="color:var(--ws-muted)">✕</button>
                </div>
              {/each}

              <div class="flex gap-2 pt-1">
                <input bind:value={newItemText} placeholder={$t('packingItemPlaceholder')}
                  onkeydown={(e) => e.key === 'Enter' && addItem(tpl)}
                  class="flex-1 px-3 py-1.5 rounded-lg border text-xs"
                  style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)"/>
                <button onclick={() => addItem(tpl)} disabled={addingItem || !newItemText.trim()}
                  class="px-3 py-1.5 rounded-lg text-xs font-semibold disabled:opacity-40"
                  style="background:var(--ws-surface);border:1px solid var(--ws-border);color:var(--ws-accent)">
                  +
                </button>
              </div>

              <div class="flex gap-2 pt-2 border-t" style="border-color:var(--ws-border)">
                <button onclick={() => resetTemplate(tpl)}
                  class="flex-1 py-1.5 rounded-lg text-xs font-semibold hover:opacity-80"
                  style="background:var(--ws-surface);border:1px solid var(--ws-border);color:var(--ws-muted)">
                  🔄 {$t('packingReset')}
                </button>
                <button onclick={() => removeTemplate(tpl)}
                  class="flex-1 py-1.5 rounded-lg text-xs font-semibold hover:opacity-80"
                  style="background:rgba(220,38,38,.08);border:1px solid rgba(220,38,38,.25);color:#dc2626">
                  🗑️ {$t('packingDeleteList')}
                </button>
              </div>
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>

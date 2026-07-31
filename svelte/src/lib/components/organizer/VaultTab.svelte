<script>
  import { t } from '$lib/i18n.js';
  import { api, apiUpload, apiDownloadBlob } from '$lib/api.js';
  import { toast } from '$lib/toast.js';
  import { fmtDate } from '$lib/utils.js';
  import { onMount } from 'svelte';

  let documents = $state([]);
  let loading   = $state(true);
  let uploading = $state(false);

  let file       = $state(null);
  let title      = $state('');
  let docType    = $state('other');
  let expiryDate = $state('');

  const DOC_TYPES = ['passport', 'visa', 'vaccination', 'insurance', 'booking', 'other'];

  function typeIcon(type) {
    return { passport: '📕', visa: '🛂', vaccination: '💉', insurance: '🛡️', booking: '🎫', other: '📄' }[type] || '📄';
  }
  function typeLabel(type) {
    return $t('vaultType_' + type) || type;
  }

  async function loadDocuments() {
    loading = true;
    try {
      documents = await api('/api/documents');
    } catch {
      documents = [];
    }
    loading = false;
  }

  onMount(loadDocuments);

  function onFileChange(e) {
    file = e.target.files?.[0] || null;
    if (file && !title.trim()) title = file.name.replace(/\.[^.]+$/, '');
  }

  async function upload() {
    if (!file || !title.trim()) {
      toast($t('vaultUploadMissing'), 'warning');
      return;
    }
    uploading = true;
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('title', title.trim());
      fd.append('doc_type', docType);
      if (expiryDate) fd.append('expiry_date', expiryDate);
      await apiUpload('/api/documents', fd);
      toast($t('toastSaved'), 'success');
      file = null; title = ''; docType = 'other'; expiryDate = '';
      const input = document.getElementById('vault-file-input');
      if (input) input.value = '';
      await loadDocuments();
    } catch (e) {
      toast(e.message || 'Fehler', 'error');
    }
    uploading = false;
  }

  async function download(doc) {
    try {
      const blob = await apiDownloadBlob(`/api/documents/${doc.id}/download`);
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement('a');
      a.href = url;
      a.download = doc.orig_filename || doc.title;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      toast(e.message || 'Download fehlgeschlagen', 'error');
    }
  }

  async function remove(doc) {
    if (!confirm($t('vaultDeleteConfirm'))) return;
    try {
      await api(`/api/documents/${doc.id}`, { method: 'DELETE' });
      documents = documents.filter(d => d.id !== doc.id);
    } catch (e) {
      toast(e.message || 'Fehler', 'error');
    }
  }

  /** null | 'expired' | 'soon' (<=90 Tage) — rein clientseitig aus expiry_date abgeleitet. */
  function expiryState(doc) {
    if (!doc.expiry_date) return null;
    const days = Math.floor((new Date(doc.expiry_date) - new Date()) / 86400000);
    if (days < 0)  return 'expired';
    if (days <= 90) return 'soon';
    return null;
  }
</script>

<div class="space-y-4">
  <p class="text-xs" style="color:var(--ws-muted)">{$t('vaultHint')}</p>

  <!-- Upload -->
  <div class="rounded-xl border p-3 space-y-2" style="background:var(--ws-surface2);border-color:var(--ws-border)">
    <input id="vault-file-input" type="file" onchange={onFileChange} class="w-full text-xs" style="color:var(--ws-text)"/>
    <input bind:value={title} placeholder={$t('vaultUploadTitlePlaceholder')}
      class="w-full px-3 py-2 rounded-xl border text-sm"
      style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)"/>
    <div class="grid grid-cols-2 gap-2">
      <select bind:value={docType}
        class="px-3 py-2 rounded-xl border text-sm"
        style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">
        {#each DOC_TYPES as dt}
          <option value={dt}>{typeIcon(dt)} {typeLabel(dt)}</option>
        {/each}
      </select>
      <input type="date" bind:value={expiryDate} title={$t('vaultUploadExpiry')}
        class="px-3 py-2 rounded-xl border text-sm"
        style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)"/>
    </div>
    <button onclick={upload} disabled={uploading || !file || !title.trim()}
      class="w-full py-2 rounded-xl text-sm font-semibold transition-opacity disabled:opacity-40 hover:opacity-90"
      style="background:var(--ws-accent);color:#fff">
      {uploading ? '⏳…' : ('⬆️ ' + $t('vaultUploadBtn'))}
    </button>
  </div>

  <!-- List -->
  {#if loading}
    <p class="text-xs" style="color:var(--ws-muted)">⏳…</p>
  {:else if documents.length === 0}
    <p class="text-xs text-center py-4" style="color:var(--ws-muted)">{$t('vaultEmpty')}</p>
  {:else}
    <div class="space-y-2">
      {#each documents as doc (doc.id)}
        {@const state = expiryState(doc)}
        <div class="flex items-center gap-2 rounded-xl border px-3 py-2"
          style="background:var(--ws-surface2);border-color:{state === 'expired' ? '#dc2626' : state === 'soon' ? '#ca8a04' : 'var(--ws-border)'}">
          <span class="text-lg shrink-0">{typeIcon(doc.doc_type)}</span>
          <div class="flex-1 min-w-0">
            <div class="text-sm font-medium truncate" style="color:var(--ws-text)">{doc.title}</div>
            {#if doc.expiry_date}
              <div class="text-[10px]" style="color:{state === 'expired' ? '#dc2626' : state === 'soon' ? '#ca8a04' : 'var(--ws-muted)'}">
                {#if state === 'expired'}⚠️ {$t('vaultExpired')} — {/if}{fmtDate(doc.expiry_date)}
              </div>
            {/if}
          </div>
          <button onclick={() => download(doc)} title={$t('vaultDownload')}
            class="text-sm px-2 py-1 rounded-lg hover:opacity-70 shrink-0">⬇️</button>
          <button onclick={() => remove(doc)} title={$t('vaultDelete')}
            class="text-sm px-2 py-1 rounded-lg hover:opacity-70 shrink-0">🗑️</button>
        </div>
      {/each}
    </div>
  {/if}
</div>

<script>
  import { t } from '$lib/i18n.js';
  import { api, apiUpload, apiDownloadBlob } from '$lib/api.js';
  import { toast } from '$lib/toast.js';
  import { fmtDate } from '$lib/utils.js';
  import { onMount } from 'svelte';

  let documents = $state([]);
  let trips     = $state([]);
  let loading   = $state(true);
  let uploading = $state(false);
  let dragOver  = $state(false);

  let file       = $state(null);
  let title      = $state('');
  let docType    = $state('other');
  let expiryDate = $state('');
  let tripId     = $state('');

  const DOC_TYPES = ['passport', 'visa', 'vaccination', 'insurance', 'booking', 'other'];

  function typeIcon(type) {
    return { passport: '📕', visa: '🛂', vaccination: '💉', insurance: '🛡️', booking: '🎫', other: '📄' }[type] || '📄';
  }
  function typeLabel(type) {
    return $t('vaultType_' + type) || type;
  }
  function tripLabel(id) {
    const trip = trips.find(t => t.id === id);
    return trip ? (trip.title || trip.destination) : null;
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

  async function loadTrips() {
    try {
      trips = await api('/api/ws-trips');
    } catch {
      trips = [];
    }
  }

  onMount(() => { loadDocuments(); loadTrips(); });

  function setFile(f) {
    file = f;
    if (file && !title.trim()) title = file.name.replace(/\.[^.]+$/, '');
  }
  function onFileChange(e) { setFile(e.target.files?.[0] || null); }
  function onDragOver(e) { e.preventDefault(); dragOver = true; }
  function onDragLeave() { dragOver = false; }
  function onDrop(e) {
    e.preventDefault();
    dragOver = false;
    const f = e.dataTransfer?.files?.[0];
    if (f) setFile(f);
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
      if (tripId) fd.append('trip_id', tripId);
      await apiUpload('/api/documents', fd);
      toast($t('toastSaved'), 'success');
      file = null; title = ''; docType = 'other'; expiryDate = ''; tripId = '';
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

  /** { text, state: null|'soon'|'expired' } — rein clientseitig aus expiry_date abgeleitet. */
  function expiryInfo(doc) {
    if (!doc.expiry_date) return null;
    const days = Math.floor((new Date(doc.expiry_date) - new Date()) / 86400000);
    if (days < 0)  return { text: $t('vaultExpiredSince').replace('{n}', Math.abs(days)), state: 'expired' };
    if (days === 0) return { text: $t('vaultExpiresToday'), state: 'expired' };
    if (days <= 90) return { text: $t('vaultExpiresIn').replace('{n}', days), state: 'soon' };
    return { text: fmtDate(doc.expiry_date), state: null };
  }
</script>

<div class="space-y-4">
  <p class="text-xs" style="color:var(--ws-muted)">{$t('vaultHint')}</p>

  <!-- Upload -->
  <div class="rounded-xl border p-3 space-y-2" style="background:var(--ws-surface2);border-color:var(--ws-border)">
    <!-- Drag & Drop Zone -->
    <div
      role="button" tabindex="0"
      ondragover={onDragOver} ondragleave={onDragLeave} ondrop={onDrop}
      onclick={() => document.getElementById('vault-file-input').click()}
      onkeydown={(e) => e.key === 'Enter' && document.getElementById('vault-file-input').click()}
      class="rounded-xl border-2 border-dashed p-5 text-center cursor-pointer transition-all"
      style="border-color:{dragOver ? 'var(--ws-accent)' : 'var(--ws-border)'};background:{dragOver ? 'color-mix(in srgb,var(--ws-accent) 8%,var(--ws-surface))' : 'var(--ws-surface)'}">
      <input id="vault-file-input" type="file" onchange={onFileChange} class="sr-only"/>
      {#if file}
        <p class="text-sm font-semibold" style="color:var(--ws-text)">📄 {file.name}</p>
        <p class="text-[10px] mt-0.5" style="color:var(--ws-muted)">{$t('vaultChangeFile')}</p>
      {:else}
        <p class="text-2xl mb-1">📤</p>
        <p class="text-sm font-semibold" style="color:var(--ws-text)">{$t('vaultDropHint')}</p>
      {/if}
    </div>

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
    {#if trips.length > 0}
      <select bind:value={tripId}
        class="w-full px-3 py-2 rounded-xl border text-sm"
        style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">
        <option value="">{$t('vaultNoTrip')}</option>
        {#each trips as trip}
          <option value={trip.id}>📍 {trip.title || trip.destination}</option>
        {/each}
      </select>
    {/if}
    <button onclick={upload} disabled={uploading || !file || !title.trim()}
      class="w-full py-2 rounded-xl text-sm font-semibold transition-opacity disabled:opacity-40 hover:opacity-90"
      style="background:var(--ws-accent);color:#fff">
      {uploading ? '⏳…' : ('⬆️ ' + $t('vaultUploadBtn'))}
    </button>
  </div>

  <!-- Grid -->
  {#if loading}
    <p class="text-xs" style="color:var(--ws-muted)">⏳…</p>
  {:else if documents.length === 0}
    <p class="text-xs text-center py-4" style="color:var(--ws-muted)">{$t('vaultEmpty')}</p>
  {:else}
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {#each documents as doc (doc.id)}
        {@const expiry = expiryInfo(doc)}
        {@const linkedTrip = doc.trip_id ? tripLabel(doc.trip_id) : null}
        <div class="rounded-2xl border p-4 space-y-2 transition-shadow hover:shadow-md"
          style="background:var(--ws-surface2);border-color:{expiry?.state === 'expired' ? '#dc2626' : expiry?.state === 'soon' ? '#ca8a04' : 'var(--ws-border)'}">
          <div class="flex items-start justify-between gap-2">
            <span class="text-3xl">{typeIcon(doc.doc_type)}</span>
            <div class="flex gap-1 shrink-0">
              <button onclick={() => download(doc)} title={$t('vaultDownload')}
                class="w-7 h-7 rounded-lg flex items-center justify-center hover:opacity-70"
                style="background:var(--ws-surface);border:1px solid var(--ws-border)">⬇️</button>
              <button onclick={() => remove(doc)} title={$t('vaultDelete')}
                class="w-7 h-7 rounded-lg flex items-center justify-center hover:opacity-70"
                style="background:var(--ws-surface);border:1px solid var(--ws-border)">🗑️</button>
            </div>
          </div>
          <div class="text-sm font-semibold truncate" style="color:var(--ws-text)">{doc.title}</div>
          <div class="text-[10px] uppercase tracking-wider font-semibold" style="color:var(--ws-muted)">{typeLabel(doc.doc_type)}</div>
          {#if linkedTrip}
            <div class="text-xs truncate" style="color:var(--ws-muted)">📍 {linkedTrip}</div>
          {/if}
          {#if expiry}
            <div class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold"
              style="background:{expiry.state === 'expired' ? 'rgba(220,38,38,.12)' : expiry.state === 'soon' ? 'rgba(202,138,4,.12)' : 'var(--ws-surface)'};color:{expiry.state === 'expired' ? '#dc2626' : expiry.state === 'soon' ? '#ca8a04' : 'var(--ws-muted)'}">
              {expiry.state === 'expired' ? '⚠️' : expiry.state === 'soon' ? '⏳' : '📅'} {expiry.text}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>

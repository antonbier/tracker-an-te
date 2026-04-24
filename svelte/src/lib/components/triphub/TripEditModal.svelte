<script>
  /**
   * TripEditModal.svelte — Bearbeiten von Titel + Zielort eines ws_trip.
   * Ausgelagert aus TripHub.svelte.
   *
   * Props:
   *   open    — $bindable, steuert Sichtbarkeit
   *   trip    — aktueller Trip (read-only für Initialwerte)
   *   onsaved — callback(updatedFields) nach erfolgreichem Save
   */
  import { api }   from '$lib/api.js';
  import { toast } from '$lib/toast.js';

  let { open = $bindable(false), trip, onsaved } = $props();

  let editTitle  = $state('');
  let editDest   = $state('');
  let editLat    = $state(null);
  let editLon    = $state(null);
  let editSaving = $state(false);
  let geoQuery   = $state('');
  let geoResults = $state([]);
  let geoLoading = $state(false);
  let geoDebounce = null;

  // Werte aus Trip laden wenn Modal öffnet
  $effect(() => {
    if (open && trip) {
      editTitle  = trip.title       || '';
      editDest   = trip.destination || '';
      editLat    = trip.lat         ?? null;
      editLon    = trip.lon         ?? null;
      geoQuery   = trip.destination || '';
      geoResults = [];
    }
  });

  function close() {
    open = false;
    geoResults = [];
    if (geoDebounce) clearTimeout(geoDebounce);
  }

  function onGeoInput(e) {
    geoQuery = e.target.value;
    editLat = null;
    editLon = null;
    editDest = geoQuery;
    if (geoDebounce) clearTimeout(geoDebounce);
    if (geoQuery.length < 2) { geoResults = []; return; }
    geoDebounce = setTimeout(async () => {
      geoLoading = true;
      try {
        const res = await api(`/api/settings/geocode?q=${encodeURIComponent(geoQuery)}`);
        geoResults = res || [];
      } catch { geoResults = []; }
      geoLoading = false;
    }, 350);
  }

  function selectGeoResult(result) {
    editDest   = result.name || result.display_name || geoQuery;
    editLat    = result.lat  ?? null;
    editLon    = result.lon  ?? null;
    geoQuery   = editDest;
    geoResults = [];
  }

  async function save() {
    if (!editDest.trim()) return;
    editSaving = true;
    try {
      const payload = { title: editTitle.trim() || null, destination: editDest.trim() };
      if (editLat !== null) payload.lat = editLat;
      if (editLon !== null) payload.lon = editLon;
      await api(`/api/ws-trips/${trip.id}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      });
      toast('✅ Reise aktualisiert', 'success');
      onsaved?.(payload);
      close();
    } catch (e) { toast(e.message || 'Fehler', 'error'); }
    editSaving = false;
  }

  const inpCls  = 'w-full px-3 py-2 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ws-accent)]';
  const inpStyle = 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)';
</script>

{#if open}
<div class="fixed inset-0 z-50 flex items-center justify-center"
  style="background:rgba(0,0,0,.52);backdrop-filter:blur(5px)"
  role="dialog" aria-modal="true">
  <div class="w-full max-w-sm mx-4 rounded-2xl border shadow-2xl overflow-hidden"
    style="background:var(--ws-surface);border-color:var(--ws-border)">

    <!-- Header -->
    <div class="px-5 py-4 border-b flex items-center justify-between"
      style="border-color:var(--ws-border)">
      <h3 class="font-bold text-sm" style="color:var(--ws-text)">✏️ Reise bearbeiten</h3>
      <button onclick={close} class="text-lg leading-none hover:opacity-60"
        style="color:var(--ws-muted)">✕</button>
    </div>

    <div class="p-5 space-y-4">

      <!-- Titel (kosmetisch) -->
      <div class="space-y-1.5">
        <label class="text-xs font-semibold" style="color:var(--ws-muted)">
          🏷️ Titel (kosmetisch, optional)
        </label>
        <input type="text" bind:value={editTitle}
          placeholder='z.B. "Roadtrip 2025" oder leer lassen'
          autocapitalize="words"
          class={inpCls} style={inpStyle} />
        <p class="text-[10px]" style="color:var(--ws-muted)">
          Rein kosmetisch — steuert keine Wetter- oder Kartendaten.
        </p>
      </div>

      <!-- Ort / Geocode -->
      <div class="space-y-1.5">
        <label class="text-xs font-semibold" style="color:var(--ws-muted)">
          📍 Ort / Hauptziel <span style="color:#ef4444">*</span>
        </label>
        <div class="relative">
          <input type="text" value={geoQuery} oninput={onGeoInput}
            placeholder="Stadt oder Region suchen…"
            class={inpCls}
            style="background:var(--ws-surface2);border-color:{editLat ? 'var(--ws-green)' : 'var(--ws-border)'};color:var(--ws-text)" />
          {#if geoLoading}
            <span class="absolute right-3 top-2.5 text-xs" style="color:var(--ws-muted)">⏳</span>
          {:else if editLat}
            <span class="absolute right-3 top-2.5 text-xs" style="color:var(--ws-green)">✓</span>
          {/if}

          {#if geoResults.length > 0}
            <div class="absolute top-full mt-1 left-0 right-0 rounded-xl border shadow-xl z-30 overflow-hidden"
              style="background:var(--ws-surface);border-color:var(--ws-border);max-height:200px;overflow-y:auto">
              {#each geoResults.slice(0, 6) as result}
                <button onclick={() => selectGeoResult(result)}
                  class="w-full text-left px-3 py-2.5 text-xs hover:opacity-80 transition-opacity border-b last:border-b-0"
                  style="color:var(--ws-text);border-color:var(--ws-border);background:var(--ws-surface)">
                  <span class="font-semibold">{result.name || result.display_name}</span>
                  {#if result.country}
                    <span style="color:var(--ws-muted)"> · {result.country}</span>
                  {/if}
                </button>
              {/each}
            </div>
          {/if}
        </div>
        <p class="text-[10px]" style="color:var(--ws-muted)">
          Steuert Wetter, Karten & Bildsuche — bitte aus der Liste wählen.
        </p>
        {#if editLat && editLon}
          <p class="text-[10px] font-mono" style="color:var(--ws-green)">
            🌐 {Number(editLat).toFixed(4)}, {Number(editLon).toFixed(4)}
          </p>
        {/if}
      </div>

    </div>

    <!-- Footer -->
    <div class="px-5 pb-5 flex gap-3">
      <button onclick={close}
        class="flex-1 py-2.5 rounded-xl border text-sm font-semibold hover:opacity-70"
        style="border-color:var(--ws-border);color:var(--ws-muted)">Abbrechen</button>
      <button onclick={save}
        disabled={!editDest.trim() || editSaving}
        class="flex-1 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-40"
        style="background:var(--ws-accent);color:#fff5ec">
        {editSaving ? '⏳ Speichern…' : '💾 Speichern'}
      </button>
    </div>

  </div>
</div>
{/if}

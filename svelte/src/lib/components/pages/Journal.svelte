<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';
  import { apiUrl } from '$lib/stores.js';
  import { toast } from '$lib/toast.js';

  let trips   = $state([]);
  let loading = $state(true);
  let syncing = $state(false);
  let syncInfo = $state('');

  onMount(loadTrips);

  async function loadTrips() {
    if (!$apiUrl) { loading = false; return; }
    try { trips = await api('/api/dawarich/trips?limit=100'); }
    catch(e) { toast('Fehler beim Laden: ' + e.message, 'error'); }
    loading = false;
  }

  async function syncJournal() {
    if (!$apiUrl) { toast('Backend-URL fehlt','warning'); return; }
    syncing = true; syncInfo = '';
    try {
      // Backend liest Dawarich-Credentials aus der verschlüsselten DB (user_settings).
      // Kein localStorage-Zugriff — Credentials gehören nicht in den Browser-Storage.
      const r = await api('/api/dawarich/sync', { method: 'POST', body: '{}' });

      if (r.trips_detected === 0 && r.points_loaded === 0) {
        syncInfo = 'Keine GPS-Punkte gefunden — Dawarich URL/Token prüfen';
        toast('Keine Punkte geladen — Einstellungen prüfen', 'warning');
      } else {
        syncInfo = `${r.points_loaded} Punkte · ${r.trips_detected} erkannt · ${r.trips_saved} gespeichert`;
        toast(`${r.trips_detected} Reisen erkannt ✓`, 'success');
      }
      await loadTrips();
    } catch(e) {
      // Detailliertere Fehlermeldung
      const msg = e.message || 'Unbekannter Fehler';
      if (msg.includes('dawarich')) {
        toast('Dawarich nicht erreichbar — URL in Einstellungen prüfen', 'error');
      } else if (msg.includes('422') || msg.includes('credentials')) {
        toast('Dawarich-Credentials fehlen — Einstellungen → Integrationen', 'error');
      } else {
        toast('Sync-Fehler: ' + msg, 'error');
      }
    }
    syncing = false;
  }

  async function deleteTrip(id) {
    if (!confirm('Trip löschen?')) return;
    try {
      await api(`/api/dawarich/trips/${id}`, { method: 'DELETE' });
      toast('Trip gelöscht', 'success');
    } catch(e) { toast(e.message, 'error'); }
    await loadTrips();
  }
</script>

<div class="space-y-4">
  <div class="flex items-start justify-between">
    <div>
      <h1 class="text-2xl font-bold italic" style="font-family:var(--ws-serif)">📓 Reisetagebuch</h1>
      <p class="text-sm mt-0.5" style="color:var(--ws-muted)">{trips.length} Reisen erkannt</p>
    </div>
    <button onclick={syncJournal} disabled={syncing}
      class="px-4 py-2 rounded-xl text-sm font-semibold border transition-all disabled:opacity-50"
      style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">
      {syncing ? '⏳ Sync…' : '🧭 Synchronisieren'}
    </button>
  </div>

  {#if syncInfo}
    <div class="rounded-xl px-4 py-2.5 text-xs border" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">
      ℹ️ {syncInfo}
    </div>
  {/if}

  {#if !$apiUrl}
    <div class="rounded-xl p-6 border-2 border-dashed text-center" style="border-color:var(--ws-border)">
      <div class="text-3xl mb-2">🗺️</div>
      <p class="text-sm italic" style="font-family:var(--ws-serif);color:var(--ws-muted)">Backend-URL in den Einstellungen konfigurieren</p>
    </div>
  {:else if loading}
    <p class="text-sm" style="color:var(--ws-muted)">Lade…</p>
  {:else if trips.length === 0}
    <div class="rounded-xl p-6 border-2 border-dashed text-center" style="border-color:var(--ws-border)">
      <div class="text-3xl mb-2">🗺️</div>
      <p class="text-sm font-semibold italic mb-1" style="font-family:var(--ws-serif);color:var(--ws-text)">Noch keine Reisen erkannt</p>
      <p class="text-xs mb-3" style="color:var(--ws-muted)">
        Dawarich URL + Token + Home-Koordinaten in<br/>Einstellungen → Integrationen eintragen
      </p>
      <button onclick={syncJournal} disabled={syncing}
        class="px-4 py-2 rounded-xl text-sm font-semibold"
        style="background:var(--ws-accent);color:#fff5ec">
        {syncing ? '⏳ Sync…' : '🧭 Jetzt synchronisieren'}
      </button>
    </div>
  {:else}
    <div class="space-y-3">
      {#each trips as trip}
        {@const loc = [trip.location_name, trip.country].filter(Boolean).join(', ') || `${trip.lat},${trip.lon}`}
        {@const mapsUrl = `https://www.google.com/maps?q=${trip.lat},${trip.lon}`}
        <div class="rounded-xl p-4 border flex gap-3" style="background:var(--ws-surface);border-color:var(--ws-border)">
          <div class="w-9 h-9 rounded-full shrink-0 flex items-center justify-center text-sm mt-0.5"
            style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec;box-shadow:0 2px 8px rgba(196,98,45,.3)">
            📍
          </div>
          <div class="flex-1 min-w-0">
            <div class="font-bold italic truncate" style="font-family:var(--ws-serif);color:var(--ws-text)">{loc}</div>
            <div class="text-xs font-mono mt-0.5" style="color:var(--ws-muted)">
              {trip.start_date} → {trip.end_date}
            </div>
            <div class="mt-1.5 flex items-center gap-2">
              <span class="px-2 py-0.5 rounded-full text-xs font-mono font-bold"
                style="background:rgba(196,98,45,.1);color:var(--ws-accent)">
                {trip.nights} {trip.nights===1?$t('night'):$t('nights')}
              </span>
              <a href={mapsUrl} target="_blank"
                class="px-2 py-0.5 rounded-full text-xs border transition-colors hover:border-[var(--ws-accent)]"
                style="border-color:var(--ws-border);color:var(--ws-muted)">
                🗺 Maps
              </a>
              <button onclick={() => deleteTrip(trip.id)}
                class="px-2 py-0.5 rounded-full text-xs border transition-colors ml-auto"
                style="border-color:var(--ws-border);color:var(--ws-muted)">✕</button>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

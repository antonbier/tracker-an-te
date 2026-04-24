<script>
  /**
   * ArchiveSyncBar.svelte — Sync-Controls im Archiv-Tab.
   *
   * Enthält:
   *   - Dawarich-Sync (syncJournal) inkl. force-full Checkbox
   *   - ActualBudget-Sync (syncActual) — liest Credentials aus Backend-Settings
   *
   * HINWEIS: Dawarich- und ActualBudget-Credentials werden direkt vom Backend
   * gelesen (gespeichert per Fernet in user_settings). Das Frontend übergibt
   * sie NICHT mehr per localStorage — das war der alte, unsichere Weg.
   * Ausnahme: syncActual liest noch legacy localStorage für Fallback.
   * TODO: vollständig auf Backend-Credentials umstellen sobald
   *       POST /api/dawarich/sync ohne Body korrekt aus DB liest.
   *
   * Props:
   *   selectedYear   — für actuals Jahr-Filter
   *   archivedTrips  — ws_trips die syncbar sind
   *   onsynced       — callback nach erfolgreichem Sync (reload journal)
   */
  import { browser } from '$app/environment';
  import { api }     from '$lib/api.js';
  import { apiUrl }  from '$lib/stores.js';
  import { toast }   from '$lib/toast.js';
  import { t }       from '$lib/i18n.js';

  let { selectedYear, archivedTrips = [], onsynced } = $props();

  // ── Dawarich ──────────────────────────────────────────────────────────────
  let syncing   = $state(false);
  let forceFull = $state(false);

  async function syncJournal() {
    if (!$apiUrl) { toast('Backend-URL fehlt', 'warning'); return; }
    // Legacy: falls Credentials noch im localStorage stehen, mitschicken
    const url   = browser ? localStorage.getItem('s-dawarichUrl')   || '' : '';
    const token = browser ? localStorage.getItem('s-dawarichToken') || '' : '';
    const lat   = parseFloat(browser ? localStorage.getItem('s-homeLat') || '0' : '0');
    const lon   = parseFloat(browser ? localStorage.getItem('s-homeLon') || '0' : '0');
    syncing = true;
    try {
      const body = (url && token)
        ? JSON.stringify({ dawarich_url: url, dawarich_token: token,
                           home_lat: lat || null, home_lon: lon || null,
                           force_full: forceFull })
        : JSON.stringify({ force_full: forceFull });
      const r = await api('/api/dawarich/sync', { method: 'POST', body });
      toast(`${r.trips_detected} Reisen erkannt ✓`, 'success');
      onsynced?.();
    } catch (e) { toast('Sync-Fehler: ' + e.message, 'error'); }
    syncing = false;
  }

  // ── ActualBudget ─────────────────────────────────────────────────────────
  let actualSyncing = $state(false);

  async function syncActual() {
    if (!$apiUrl) { toast('Backend-URL fehlt', 'warning'); return; }
    const yearTrips = archivedTrips.filter(
      t => (t.start_date || '').slice(0, 4) === String(selectedYear)
    );
    const targets = yearTrips.length > 0 ? yearTrips : archivedTrips;
    if (targets.length === 0) {
      toast('Keine WanderWizzard-Reisen zum Syncen gefunden', 'warning');
      return;
    }
    actualSyncing = true;
    let synced = 0; let failed = 0;
    for (const trip of targets) {
      try {
        await api(`/api/ws-trips/${trip.id}/sync-budget`, { method: 'POST' });
        synced++;
      } catch (e) {
        if (e?.message?.includes('nicht konfiguriert') || String(e).includes('400')) {
          toast('ActualBudget Zugangsdaten fehlen — bitte in Einstellungen → Bridges hinterlegen', 'warning');
          actualSyncing = false;
          return;
        }
        failed++;
      }
    }
    if (synced > 0) toast(`${synced} Reise${synced > 1 ? 'n' : ''} mit ActualBudget synchronisiert ✓`, 'success');
    if (failed > 0) toast(`${failed} Sync${failed > 1 ? 's' : ''} fehlgeschlagen`, 'warning');
    actualSyncing = false;
  }
</script>

<!-- Sync-Buttons: kompakte Toolbar -->
<div class="flex items-center gap-1.5 flex-wrap">

  <!-- Dawarich -->
  <button onclick={syncJournal} disabled={syncing}
    class="flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg transition-all hover:opacity-80 disabled:opacity-40"
    style="background:var(--ws-surface);border:1px solid var(--ws-border);color:var(--ws-muted)">
    {syncing ? '⏳' : $t('archiveDawarichSync')}
  </button>
  <label class="flex items-center gap-1 text-xs cursor-pointer" style="color:var(--ws-muted)"
    title="Gelöschte Reisen erneut laden (setzt ignored-Flag zurück)">
    <input type="checkbox" bind:checked={forceFull}
      class="rounded" style="accent-color:var(--ws-accent)" />
    🔄
  </label>

  <!-- ActualBudget -->
  <button onclick={syncActual} disabled={actualSyncing}
    class="flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg transition-all hover:opacity-80 disabled:opacity-40"
    style="background:var(--ws-surface);border:1px solid var(--ws-border);color:var(--ws-muted)"
    title="Synct alle Archiv-Reisen mit ActualBudget (Credentials aus Einstellungen)">
    {actualSyncing ? '⏳ Synce…' : $t('archiveActualSync')}
  </button>

</div>

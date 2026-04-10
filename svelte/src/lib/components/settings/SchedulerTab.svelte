<script>
  import { apiUrl } from '$lib/stores.js';
  import { api } from '$lib/api.js';
  import { toast } from '$lib/toast.js';

  let schedInterval  = $state(24);
  let schedPriceDrop = $state(true);
  let schedDaily     = $state(false);
  let schedLastRun   = $state('');
  let schedTimezone  = $state('UTC');
  let schedSaving    = $state(false);
  let schedRunning   = $state(false);

  async function loadSchedulerSettings() {
    if (!$apiUrl) return;
    try {
      const s = await api('/api/scheduler/settings');
      schedInterval  = s.update_interval_hours ?? 24;
      schedPriceDrop = s.notify_price_drop      ?? true;
      schedDaily     = s.notify_daily_summary   ?? false;
      schedLastRun   = s.last_run_at            || '';
      schedTimezone  = s.timezone               || 'UTC';
    } catch {}
  }

  async function saveSchedulerSettings() {
    schedSaving = true;
    try {
      await api('/api/scheduler/settings', {
        method: 'PUT',
        body: JSON.stringify({
          update_interval_hours: schedInterval,
          notify_price_drop:     schedPriceDrop,
          notify_daily_summary:  schedDaily,
        }),
      });
      toast('Scheduler gespeichert ✓', 'success');
    } catch (e) { toast(e.message, 'error'); }
    schedSaving = false;
  }

  async function triggerSchedulerRun() {
    schedRunning = true;
    try {
      await api('/api/scheduler/run', { method: 'POST' });
      toast('Preisabfrage gestartet… ⏳', 'warning');
    } catch (e) { toast(e.message, 'error'); }
    setTimeout(() => { schedRunning = false; }, 5000);
  }

  $effect(() => { loadSchedulerSettings(); });
</script>

<div class="space-y-4">
  <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">⏰ Update-Intervall</div>
  <div class="grid grid-cols-3 gap-2">
    {#each [6, 12, 24, 48, 72, 168] as h}
      <button onclick={() => schedInterval = h}
        class="py-2 rounded-xl text-xs font-semibold border transition-all"
        style={schedInterval === h
          ? 'background:var(--ws-accent);color:#fff;border-color:var(--ws-accent)'
          : 'background:var(--ws-surface2);color:var(--ws-muted);border-color:var(--ws-border)'}>
        {h < 24 ? h + 'h' : h === 168 ? '1 Wo.' : (h/24) + 'd'}
      </button>
    {/each}
  </div>

  <div class="text-xs font-bold uppercase tracking-wider pt-2" style="color:var(--ws-muted)">🔔 Benachrichtigungen</div>
  <label class="flex items-center gap-3 cursor-pointer px-3 py-2.5 rounded-xl border"
    style="background:var(--ws-surface2);border-color:var(--ws-border)">
    <input type="checkbox" bind:checked={schedPriceDrop} class="w-4 h-4 accent-[var(--ws-accent)]"/>
    <div>
      <div class="text-sm font-medium" style="color:var(--ws-text)">📉 Preissturz-Alarm</div>
      <div class="text-xs" style="color:var(--ws-muted)">Benachrichtigung wenn Preis sinkt</div>
    </div>
  </label>
  <label class="flex items-center gap-3 cursor-pointer px-3 py-2.5 rounded-xl border"
    style="background:var(--ws-surface2);border-color:var(--ws-border)">
    <input type="checkbox" bind:checked={schedDaily} class="w-4 h-4 accent-[var(--ws-accent)]"/>
    <div>
      <div class="text-sm font-medium" style="color:var(--ws-text)">📋 Tägliche Zusammenfassung</div>
      <div class="text-xs" style="color:var(--ws-muted)">Täglich alle Tracker-Preise senden</div>
    </div>
  </label>

  {#if schedLastRun}
    <p class="text-xs px-3 py-1.5 rounded-lg" style="background:var(--ws-surface2);color:var(--ws-muted)">
      Letzter Lauf: {schedLastRun.slice(0,16).replace('T',' ')} {schedTimezone || 'UTC'}
    </p>
  {/if}

  <div class="flex gap-2 pt-1">
    <button onclick={saveSchedulerSettings} disabled={schedSaving}
      class="flex-1 py-2.5 rounded-xl text-sm font-semibold transition-opacity disabled:opacity-50"
      style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
      {schedSaving ? '⏳…' : '💾 Speichern'}
    </button>
    <button onclick={triggerSchedulerRun} disabled={schedRunning}
      class="flex-1 py-2.5 rounded-xl text-sm font-semibold border transition-opacity disabled:opacity-50"
      style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)">
      {schedRunning ? '⏳ Läuft…' : '▶ Jetzt ausführen'}
    </button>
  </div>
</div>

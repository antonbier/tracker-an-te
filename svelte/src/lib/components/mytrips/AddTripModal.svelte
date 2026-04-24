<script>
  /**
   * AddTripModal.svelte — Modal zum Eintragen einer manuellen Reise.
   * Ausgelagert aus MyTrips.svelte.
   * Props: open (bindable), onadded (callback nach erfolgreichem Add)
   */
  import { api }   from '$lib/api.js';
  import { toast } from '$lib/toast.js';
  import { t }     from '$lib/i18n.js';
  import { today } from '$lib/utils.js';

  let { open = $bindable(false), onadded } = $props();

  let mName    = $state('');
  let mStart   = $state(today);
  let mEnd     = $state('');
  let mCost    = $state('');
  let mAdding  = $state(false);
  let mLat     = $state(null);
  let mLon     = $state(null);
  let mGeoLoad = $state(false);
  let mGeoHint = $state('');

  const inp = 'text-sm rounded-lg focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 p-2.5 w-full outline-none transition-all border';

  function reset() {
    mName = ''; mStart = today; mEnd = ''; mCost = '';
    mLat = null; mLon = null; mGeoHint = '';
  }

  async function geocodeManualTrip() {
    const q = mName.trim();
    if (!q) return;
    mGeoLoad = true; mGeoHint = '';
    try {
      const res = await api(`/api/settings/geocode?q=${encodeURIComponent(q)}`);
      if (res?.lat && res?.lon) {
        mLat = res.lat; mLon = res.lon;
        mGeoHint = `📍 ${res.display_name || q}`;
      }
    } catch { /* silent */ }
    mGeoLoad = false;
  }

  async function addManualTrip() {
    if (!mName || !mStart) { toast($t('addTripRequired') || 'Name + Startdatum pflicht', 'error'); return; }
    mAdding = true;
    try {
      await api('/api/trips', { method: 'POST', body: JSON.stringify({
        name: mName, start_date: mStart, end_date: mEnd || mStart,
        cost: mCost ? parseFloat(mCost) : null,
        lat: mLat, lon: mLon,
      }) });
      reset();
      open = false;
      toast($t('addTripSuccess') || 'Reise eingetragen ✓', 'success');
      onadded?.();
    } catch (e) { toast(e.message, 'error'); }
    mAdding = false;
  }
</script>

{#if open}
<div class="fixed inset-0 z-50 flex items-center justify-center"
  style="background:rgba(0,0,0,.45);backdrop-filter:blur(4px)" role="dialog" aria-modal="true">
  <div class="w-full max-w-sm mx-4 rounded-2xl shadow-2xl border p-6 space-y-4"
    style="background:var(--ws-surface);border-color:var(--ws-border)">

    <h3 class="font-bold text-base" style="color:var(--ws-text)">{$t('addTripTitle')}</h3>

    <div class="relative">
      <input bind:value={mName} placeholder={$t('addTripDest')} class={inp}
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"
        onblur={geocodeManualTrip} />
      {#if mGeoLoad}
        <span class="absolute right-3 top-1/2 -translate-y-1/2 text-xs" style="color:var(--ws-muted)">⏳</span>
      {/if}
    </div>

    {#if mGeoHint}
      <p class="text-[10px] px-1" style="color:var(--ws-muted)">{mGeoHint}</p>
    {/if}

    <div class="grid grid-cols-2 gap-3">
      <div>
        <label class="text-xs mb-1 block" style="color:var(--ws-muted)">{$t('addTripStart')}</label>
        <input type="date" bind:value={mStart} class={inp}
          style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      </div>
      <div>
        <label class="text-xs mb-1 block" style="color:var(--ws-muted)">{$t('addTripEnd')}</label>
        <input type="date" bind:value={mEnd} class={inp}
          style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      </div>
    </div>

    <input type="number" bind:value={mCost} placeholder={$t('addTripCost')} class={inp}
      style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>

    <div class="flex gap-3">
      <button onclick={() => { open = false; reset(); }}
        class="flex-1 py-2.5 rounded-xl border text-sm font-semibold hover:opacity-70"
        style="border-color:var(--ws-border);color:var(--ws-muted)">
        {$t('addTripCancel')}
      </button>
      <button onclick={addManualTrip} disabled={mAdding}
        class="flex-1 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-40"
        style="background:var(--ws-accent);color:#fff5ec">
        {mAdding ? '⏳' : $t('addTripSave')}
      </button>
    </div>

  </div>
</div>
{/if}

<script>
  import { t } from '$lib/i18n.js';
  import { api } from '$lib/api.js';

  let {
    myDawarichUrl   = $bindable(),
    myDawarichToken = $bindable(),
    myHomeLat       = $bindable(),
    myHomeLon       = $bindable(),
    myHomeSearch    = $bindable(),
    myActualUrl     = $bindable(),
    myActualToken   = $bindable(),
    myActualFile    = $bindable(),
    myTravelCats    = $bindable(),
  } = $props();

  let myGeoLoading = $state(false);
  let myGeoResult  = $state('');

  async function geocodeHome() {
    const q = myHomeSearch.trim();
    if (!q) return;
    myGeoLoading = true; myGeoResult = '';
    try {
      const res = await api(`/api/settings/geocode?q=${encodeURIComponent(q)}`);
      if (res.results && res.results.length > 0) {
        const first = res.results[0];
        myHomeLat = String(parseFloat(first.lat));
        myHomeLon = String(parseFloat(first.lon));
        myGeoResult = '✓ ' + first.display_name.split(',').slice(0,2).join(',');
      } else {
        myGeoResult = '✗ Ort nicht gefunden';
      }
    } catch (e) { myGeoResult = '✗ Fehler bei Geocoding: ' + e.message; }
    myGeoLoading = false;
  }
</script>

<!-- Dawarich -->
<div class="space-y-2 mt-1">
  <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">🧭 Dawarich</div>
  <input bind:value={myDawarichUrl} placeholder="https://dawarich.example.com"
    class="w-full px-3 py-2 rounded-xl border text-sm"
    style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
  <input bind:value={myDawarichToken} type="password" placeholder="API Token"
    class="w-full px-3 py-2 rounded-xl border text-sm"
    style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
  <div class="flex gap-2">
    <input bind:value={myHomeSearch} placeholder="Heimatort suchen (z.B. Bruneck)"
      class="flex-1 px-3 py-2 rounded-xl border text-sm"
      style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"
      onkeydown={(e) => e.key === 'Enter' && geocodeHome()}/>
    <button onclick={geocodeHome} disabled={myGeoLoading}
      class="px-3 py-2 rounded-xl border text-sm transition-opacity hover:opacity-70 disabled:opacity-40"
      style="border-color:var(--ws-border);color:var(--ws-muted)">
      {myGeoLoading ? '⏳' : '📍'}
    </button>
  </div>
  {#if myGeoResult}
    <div class="text-xs px-1" style="color:{myGeoResult.startsWith('✓') ? 'var(--ws-green)' : '#dc2626'}">{myGeoResult}</div>
  {/if}
  <div class="grid grid-cols-2 gap-2">
    <input bind:value={myHomeLat} placeholder="Lat: 46.7987" class="px-3 py-2 rounded-xl border text-sm"
      style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
    <input bind:value={myHomeLon} placeholder="Lon: 11.7188" class="px-3 py-2 rounded-xl border text-sm"
      style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
  </div>
  <div class="text-xs" style="color:var(--ws-muted)">{$t('settingsHomeCoordsHint')}</div>
</div>

<hr style="border-color:var(--ws-border)"/>

<!-- ActualBudget -->
<div class="space-y-2">
  <div class="flex items-center gap-2 mb-1">
    <span class="text-base">💶</span>
    <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">ActualBudget</div>
  </div>
  <input bind:value={myActualUrl} placeholder="https://actual.example.com"
    class="w-full px-3 py-2 rounded-xl border text-sm"
    style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
  <input bind:value={myActualToken} type="password" placeholder="Server Password"
    class="w-full px-3 py-2 rounded-xl border text-sm"
    style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
  <input bind:value={myActualFile} placeholder="Budget-Dateiname (z.B. My-Finances-abc123)"
    class="w-full px-3 py-2 rounded-xl border text-sm"
    style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
  <div class="text-xs" style="color:var(--ws-muted)">💡 Dateiname: ActualBudget → Budget-Name oben links anklicken → ID aus der URL entnehmen</div>
  <input bind:value={myTravelCats} placeholder="Kategorien: Holiday, Flights, Hotel"
    class="w-full px-3 py-2 rounded-xl border text-sm"
    style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
</div>

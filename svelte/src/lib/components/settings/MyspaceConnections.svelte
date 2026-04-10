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
    myImmichUrl     = $bindable(),
    myImmichKey     = $bindable(),
    myImmichGeoSync  = $bindable(),
    unsplashKey      = $bindable(),
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

<hr style="border-color:var(--ws-border)"/>

<!-- Unsplash -->
<div class="space-y-2">
  <div class="flex items-center gap-2 mb-1">
    <span class="text-base">🖼️</span>
    <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Unsplash</div>
    <span class="ml-auto text-[10px] px-1.5 py-0.5 rounded-full font-semibold"
      style="background:rgba(196,98,45,.12);color:var(--ws-accent)">Optional</span>
  </div>
  <div class="text-xs rounded-lg px-3 py-2" style="background:rgba(var(--ws-accent-rgb,211,95,57),.08);color:var(--ws-muted)">
    💡 Mit einem <strong>Unsplash API Key</strong> werden im WanderWizzard passende Reisefotos angezeigt.
    API Key: <a href="https://unsplash.com/developers" target="_blank" class="underline" style="color:var(--ws-accent)">unsplash.com/developers</a>
    → App anlegen → Access Key kopieren.
  </div>
  <input bind:value={unsplashKey} type="password" placeholder="Unsplash Access Key"
    class="w-full px-3 py-2 rounded-xl border text-sm"
    style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
</div>

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

<hr style="border-color:var(--ws-border)"/>

<!-- Immich -->
<div class="space-y-2">
  <div class="flex items-center gap-2 mb-1">
    <span class="text-base">📸</span>
    <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Immich</div>
    <span class="ml-auto text-[10px] px-1.5 py-0.5 rounded-full font-semibold"
      style="background:rgba(196,98,45,.12);color:var(--ws-accent)">Optional</span>
  </div>
  <div class="text-xs rounded-lg px-3 py-2" style="background:rgba(var(--ws-accent-rgb,211,95,57),.08);color:var(--ws-muted)">
    💡 Verbinde deine selbst-gehostete <strong>Immich</strong>-Instanz um Reisefotos & GPS-Daten für den WanderWizzard zu nutzen.
    API Key: Immich → Account-Einstellungen → API Keys.
  </div>
  <input bind:value={myImmichUrl} placeholder="https://immich.example.com"
    class="w-full px-3 py-2 rounded-xl border text-sm"
    style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
  <input bind:value={myImmichKey} type="password" placeholder="API Key"
    class="w-full px-3 py-2 rounded-xl border text-sm"
    style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>

  <!-- Geo-Sync Toggle -->
  <label class="flex items-center gap-3 cursor-pointer px-3 py-2.5 rounded-xl border"
    style="background:var(--ws-surface2);border-color:var(--ws-border)">
    <button
      role="switch"
      aria-checked={myImmichGeoSync}
      onclick={() => myImmichGeoSync = !myImmichGeoSync}
      class="relative w-9 h-5 rounded-full transition-colors shrink-0"
      style="background:{myImmichGeoSync ? 'var(--ws-accent)' : 'var(--ws-border)'}">
      <span class="absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all"
        style="left:{myImmichGeoSync ? '20px' : '2px'}"></span>
    </button>
    <div>
      <div class="text-sm font-medium" style="color:var(--ws-text)">📍 Geo-Sync aktivieren</div>
      <div class="text-xs" style="color:var(--ws-muted)">Foto-Standorte für Reisevorschläge verwenden</div>
    </div>
  </label>
</div>

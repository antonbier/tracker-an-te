<script>
  import { theme, apiUrl } from '$lib/stores.js';
  import { t } from '$lib/i18n.js';
  import { api } from '$lib/api.js';

  let {
    urlInput      = $bindable(),
    appTimezone   = $bindable(),
    appDateFormat = $bindable(),
    homeLat       = $bindable(),
    homeLon       = $bindable(),
    homeName      = $bindable(),
    testing,
    testOk,
    ontestconnection,
  } = $props();

  // ── Heimatort geocode search ──────────────────────────────────────────────
  let homeSearch     = $state(homeName || '');
  let homeResults    = $state([]);
  let homeSearching  = $state(false);
  let homeSearchErr  = $state('');

  async function searchHome() {
    const q = homeSearch.trim();
    if (!q || q.length < 2) return;
    if (!$apiUrl) { homeSearchErr = $t('basicHomeNeedsBackend'); return; }
    homeSearching = true;
    homeSearchErr = '';
    homeResults   = [];
    try {
      const data = await api(`/api/settings/geocode?q=${encodeURIComponent(q)}`);
      homeResults = data?.results || [];
      if (!homeResults.length) homeSearchErr = $t('basicHomeNoResults');
    } catch (e) {
      homeSearchErr = e?.message || $t('basicHomeSearchError');
    }
    homeSearching = false;
  }

  function selectHome(r) {
    homeLat     = r.lat;
    homeLon     = r.lon;
    homeName    = r.display_name.split(',')[0].trim();
    homeSearch  = homeName;
    homeResults = [];
  }

  function clearHome() {
    homeLat = ''; homeLon = ''; homeName = '';
    homeSearch = ''; homeResults = [];
  }

</script>

<!-- Backend URL -->
<div>
  <label class="text-xs font-bold uppercase tracking-wider block mb-1" style="color:var(--ws-muted)">{$t('settingsBackendUrl')}</label>
  <input type="url" bind:value={urlInput} placeholder="http://192.168.1.51:8765"
    class="w-full px-3 py-2 rounded-xl border text-sm"
    style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
  <div class="flex items-center gap-2 mt-2">
    <button onclick={ontestconnection} disabled={testing}
      class="px-4 py-1.5 rounded-xl text-xs border transition-opacity hover:opacity-70 disabled:opacity-40"
      style="border-color:var(--ws-border);color:var(--ws-muted)">
      {testing ? $t('settingsTesting') : $t('settingsConnect')}
    </button>
    {#if testOk === true}
      <span class="text-xs font-medium" style="color:var(--ws-green)">{$t('settingsConnected')}</span>
    {:else if testOk === false}
      <span class="text-xs font-medium" style="color:#dc2626">{$t('settingsNotReachable')}</span>
    {/if}
  </div>
</div>

<!-- Theme -->
<div>
  <label class="text-xs font-bold uppercase tracking-wider block mb-2" style="color:var(--ws-muted)">{$t('settingsTheme')}</label>
  <div class="flex gap-2">
    {#each [{ val: '', label: $t('settingsLight') }, { val: 'dark', label: $t('settingsDark') }] as opt}
      <button onclick={() => theme.set(opt.val)}
        class="flex-1 py-2 rounded-xl text-sm border transition-all"
        style={$theme === opt.val
          ? 'background:var(--ws-accent);color:#fff;border-color:var(--ws-accent)'
          : 'background:var(--ws-surface2);color:var(--ws-muted);border-color:var(--ws-border)'}>
        {opt.label}
      </button>
    {/each}
  </div>
</div>

<!-- Timezone -->
<div>
  <label class="text-xs font-bold uppercase tracking-wider block mb-2" style="color:var(--ws-muted)">🌍 {$t('settingsTimezone')}</label>
  <select bind:value={appTimezone}
    class="w-full px-3 py-2 rounded-xl border text-sm"
    style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)">
    {#each ['Europe/Rome','Europe/Berlin','Europe/Vienna','Europe/Zurich','Europe/London','Europe/Paris','America/New_York','America/Chicago','America/Los_Angeles','Asia/Tokyo','Asia/Singapore','Australia/Sydney','UTC'] as tz}
      <option value={tz}>{tz}</option>
    {/each}
  </select>
</div>

<!-- Datumsformat -->
<div>
  <label class="text-xs font-bold uppercase tracking-wider block mb-2" style="color:var(--ws-muted)">📅 {$t('settingsDateFormat')}</label>
  <div class="flex gap-2">
    {#each [{ val: 'DD.MM.YYYY', label: '31.12.2025' }, { val: 'MM/DD/YYYY', label: '12/31/2025' }, { val: 'YYYY-MM-DD', label: '2025-12-31' }] as fmt}
      <button onclick={() => appDateFormat = fmt.val}
        class="flex-1 py-2 rounded-xl text-xs border transition-all"
        style={appDateFormat === fmt.val
          ? 'background:var(--ws-accent);color:#fff;border-color:var(--ws-accent)'
          : 'background:var(--ws-surface2);color:var(--ws-muted);border-color:var(--ws-border)'}>
        {fmt.label}
      </button>
    {/each}
  </div>
  <!-- Live-Vorschau -->
  {@const _now = new Date()}
  {@const _dd = String(_now.getDate()).padStart(2,'0')}
  {@const _mm = String(_now.getMonth()+1).padStart(2,'0')}
  {@const _yyyy = String(_now.getFullYear())}
  {@const _hh = String(_now.getHours()).padStart(2,'0')}
  {@const _min = String(_now.getMinutes()).padStart(2,'0')}
  {@const _previewDate = appDateFormat === 'MM/DD/YYYY' ? `${_mm}/${_dd}/${_yyyy}` : appDateFormat === 'YYYY-MM-DD' ? `${_yyyy}-${_mm}-${_dd}` : `${_dd}.${_mm}.${_yyyy}`}
  <p class="text-xs mt-2 px-3 py-1.5 rounded-lg" style="background:var(--ws-surface2);border:1px solid var(--ws-border);color:var(--ws-muted)">
    📅 {$t('settingsPreviewLabel') || 'Aktuell'}: <span class="font-mono font-semibold" style="color:var(--ws-text)">{_previewDate} {_hh}:{_min}</span>
  </p>
</div>


<!-- Heimatort -->
<div>
  <label class="text-xs font-bold uppercase tracking-wider block mb-2" style="color:var(--ws-muted)">🏠 {$t('settingsHomeLocation')}</label>
  <p class="text-xs mb-2" style="color:var(--ws-muted)">{$t('settingsHomeLocationHint')}</p>

  <!-- Current home display -->
  {#if homeName || (homeLat && homeLon)}
    <div class="flex items-center gap-2 mb-2 px-3 py-2 rounded-xl border"
      style="background:color-mix(in srgb,var(--ws-accent) 6%,var(--ws-surface));border-color:color-mix(in srgb,var(--ws-accent) 25%,var(--ws-border))">
      <span class="text-sm">🏠</span>
      <span class="text-xs font-semibold flex-1" style="color:var(--ws-text)">
        {homeName || `${parseFloat(homeLat).toFixed(4)}, ${parseFloat(homeLon).toFixed(4)}`}
      </span>
      {#if homeLat}
        <span class="text-[10px] font-mono" style="color:var(--ws-muted)">{parseFloat(homeLat).toFixed(4)}, {parseFloat(homeLon).toFixed(4)}</span>
      {/if}
      <button onclick={clearHome} class="text-xs px-2 py-0.5 rounded-lg hover:opacity-70"
        style="color:var(--ws-muted);background:var(--ws-surface2)">✕</button>
    </div>
  {/if}

  <!-- Search box -->
  <div class="flex gap-2">
    <input
      bind:value={homeSearch}
      placeholder={$t('settingsHomeSearchPlaceholder')}
      onkeydown={(e) => e.key === 'Enter' && searchHome()}
      class="flex-1 px-3 py-2 rounded-xl border text-sm"
      style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"
    />
    <button onclick={searchHome} disabled={homeSearching}
      class="px-3 py-2 rounded-xl text-xs border font-semibold transition-opacity hover:opacity-70 disabled:opacity-40"
      style="border-color:var(--ws-border);color:var(--ws-accent);background:var(--ws-surface2)">
      {homeSearching ? '⏳' : '🔍'}
    </button>
  </div>

  {#if homeSearchErr}
    <p class="text-xs mt-1" style="color:#dc2626">{homeSearchErr}</p>
  {/if}

  <!-- Results dropdown -->
  {#if homeResults.length}
    <div class="mt-1 rounded-xl border overflow-hidden shadow-lg"
      style="background:var(--ws-surface);border-color:var(--ws-border)">
      {#each homeResults as r}
        <button onclick={() => selectHome(r)}
          class="w-full text-left px-4 py-2.5 text-xs hover:opacity-80 border-b last:border-b-0 transition-opacity"
          style="border-color:var(--ws-border);color:var(--ws-text);background:var(--ws-surface2)">
          📍 {r.display_name}
        </button>
      {/each}
    </div>
  {/if}

  <!-- Manual lat/lon input fallback -->
  <details class="mt-2">
    <summary class="text-xs cursor-pointer" style="color:var(--ws-muted)">{$t('settingsHomeManual')}</summary>
    <div class="grid grid-cols-2 gap-2 mt-2">
      <input bind:value={homeLat} placeholder="Lat: 46.7987"
        class="px-3 py-2 rounded-xl border text-sm"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      <input bind:value={homeLon} placeholder="Lon: 11.7188"
        class="px-3 py-2 rounded-xl border text-sm"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
    </div>
  </details>
</div>

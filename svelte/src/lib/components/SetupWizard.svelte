<script>
  /**
   * SetupWizard.svelte — 5-Step Setup Wizard
   * Triggered via 🪄 in the Header.
   * Step 1: Basis & Heimat  (timezone, date format, currency, home location)
   * Step 2: Self-Hosted Bridges (Dawarich, Immich, ActualBudget)
   * Step 3–5: reserved for future implementation
   *
   * Save-on-Next: each step POSTs only its own fields to /api/settings/wizard/step
   * → safe partial update, never nulls keys from other steps.
   */
  import { onMount } from 'svelte';
  import { t } from '$lib/i18n.js';
  import { apiUrl } from '$lib/stores.js';
  import { api, checkApiStatus } from '$lib/api.js';
  import { toast } from '$lib/toast.js';
  import { browser } from '$app/environment';

  let { open = $bindable(false) } = $props();

  // ── Wizard state ──────────────────────────────────────────────────────────
  let step        = $state(1);
  let saving      = $state(false);
  let loading     = $state(false);
  const TOTAL_STEPS = 5;

  // ── Step 1: Basis & Heimat ────────────────────────────────────────────────
  let urlInput      = $state('');
  let testing       = $state(false);
  let testOk        = $state(null);
  let appTimezone   = $state('Europe/Rome');
  let appDateFormat = $state('DD.MM.YYYY');
  let appCurrency   = $state('EUR');
  let homeLat       = $state('');
  let homeLon       = $state('');
  let homeName      = $state('');
  // geocode
  let homeSearch    = $state('');
  let homeResults   = $state([]);
  let homeSearching = $state(false);
  let homeSearchErr = $state('');

  // ── Step 2: Self-Hosted Bridges ───────────────────────────────────────────
  let dawarichUrl   = $state('');
  let dawarichToken = $state('');
  let immichUrl     = $state('');
  let immichKey     = $state('');
  let immichGeoSync = $state(false);
  let actualUrl     = $state('');
  let actualToken   = $state('');
  let actualFile    = $state('');
  let travelCats    = $state('');

  const CURRENCIES  = ['EUR','USD','GBP','CHF','JPY','AUD','CAD','SEK','NOK','DKK'];
  const TIMEZONES   = ['Europe/Rome','Europe/Berlin','Europe/Vienna','Europe/Zurich',
                       'Europe/London','Europe/Paris','America/New_York',
                       'America/Los_Angeles','Asia/Tokyo','Australia/Sydney','UTC'];

  // ── Load existing settings on open ───────────────────────────────────────
  async function loadExistingSettings() {
    loading = true;
    urlInput = $apiUrl || '';
    if (browser) {
      homeLat   = localStorage.getItem('s-homeLat')   || '';
      homeLon   = localStorage.getItem('s-homeLon')   || '';
      homeName  = localStorage.getItem('s-homeName')  || '';
      homeSearch = homeName;
      dawarichUrl = localStorage.getItem('s-dawarichUrl') || '';
      actualUrl   = localStorage.getItem('s-actualUrl')   || '';
      actualFile  = localStorage.getItem('s-actualFile')  || '';
    }
    if ($apiUrl) {
      try {
        const [gs, us] = await Promise.allSettled([
          api('/api/settings'),
          api('/api/settings/user'),
        ]);
        if (gs.status === 'fulfilled') {
          const s = gs.value;
          appTimezone   = s.timezone     || 'Europe/Rome';
          appDateFormat = s.date_format  || 'DD.MM.YYYY';
          appCurrency   = s.currency     || 'EUR';
          if (s.home_lat)  { homeLat = s.home_lat; }
          if (s.home_lon)  { homeLon = s.home_lon; }
          if (s.home_name) { homeName = s.home_name; homeSearch = s.home_name; }
        }
        if (us.status === 'fulfilled') {
          const u = us.value;
          dawarichUrl   = u.dawarich_url    || dawarichUrl;
          dawarichToken = u.dawarich_token  ? '••••••••' : '';
          immichUrl     = u.immich_url      || '';
          immichKey     = u.immich_api_key  ? '••••••••' : '';
          immichGeoSync = u.immich_geo_sync === 'true' || u.immich_geo_sync === true;
          actualUrl     = u.actual_url      || actualUrl;
          actualToken   = u.actual_token    ? '••••••••' : '';
          actualFile    = u.actual_file     || actualFile;
          travelCats    = u.travel_categories || '';
        }
      } catch {}
    }
    loading = false;
  }

  $effect(() => {
    if (open) { step = 1; loadExistingSettings(); }
  });

  // ── Geocode ───────────────────────────────────────────────────────────────
  async function searchHome() {
    const q = homeSearch.trim();
    if (!q || q.length < 2) return;
    const base = urlInput.trim() || $apiUrl;
    if (!base) { homeSearchErr = $t('basicHomeNeedsBackend'); return; }
    homeSearching = true; homeSearchErr = ''; homeResults = [];
    try {
      const data = await api(`/api/settings/geocode?q=${encodeURIComponent(q)}`);
      homeResults = data?.results || [];
      if (!homeResults.length) homeSearchErr = $t('basicHomeNoResults');
    } catch (e) { homeSearchErr = e?.message || $t('basicHomeSearchError'); }
    homeSearching = false;
  }

  function selectHome(r) {
    homeLat = r.lat; homeLon = r.lon;
    homeName = r.display_name.split(',')[0].trim();
    homeSearch = homeName; homeResults = [];
  }

  function clearHome() {
    homeLat = ''; homeLon = ''; homeName = '';
    homeSearch = ''; homeResults = [];
  }

  // ── Test connection ───────────────────────────────────────────────────────
  async function testConnection() {
    testing = true; testOk = null;
    testOk = await checkApiStatus(urlInput);
    testing = false;
  }

  // ── Save current step then advance ───────────────────────────────────────
  async function saveAndNext() {
    saving = true;

    // Always persist backend URL client-side
    if (urlInput) {
      const clean = urlInput.trim().replace(/\/$/, '');
      apiUrl.set(clean);
      if (browser) localStorage.setItem('apiUrl', clean);
    }

    try {
      if (step === 1) {
        // Save step 1: global settings only
        const payload = {};
        if (appTimezone)   payload.timezone    = appTimezone;
        if (appDateFormat) payload.date_format = appDateFormat;
        if (appCurrency)   payload.currency    = appCurrency;
        if (homeLat)       payload.home_lat    = homeLat;
        if (homeLon)       payload.home_lon    = homeLon;
        if (homeName)      payload.home_name   = homeName;
        // Persist to localStorage too
        if (browser) {
          if (homeLat)  localStorage.setItem('s-homeLat',  homeLat);
          if (homeLon)  localStorage.setItem('s-homeLon',  homeLon);
          if (homeName) localStorage.setItem('s-homeName', homeName);
          localStorage.setItem('ws-timezone',    appTimezone   || 'Europe/Rome');
          localStorage.setItem('ws-date-format', appDateFormat || 'DD.MM.YYYY');
        }
        if ($apiUrl && Object.keys(payload).length > 0) {
          await api('/api/settings/wizard/step', { method: 'POST', body: JSON.stringify(payload) });
        }

      } else if (step === 2) {
        // Save step 2: user-level bridge settings
        const payload = {};
        if (dawarichUrl   && dawarichUrl   !== '••••••••') payload.dawarich_url   = dawarichUrl;
        if (dawarichToken && dawarichToken !== '••••••••') payload.dawarich_token = dawarichToken;
        if (immichUrl     && immichUrl     !== '••••••••') payload.immich_url     = immichUrl;
        if (immichKey     && immichKey     !== '••••••••') payload.immich_api_key = immichKey;
        payload.immich_geo_sync = immichGeoSync;
        if (actualUrl   && actualUrl   !== '••••••••') payload.actual_url   = actualUrl;
        if (actualToken && actualToken !== '••••••••') payload.actual_token = actualToken;
        if (actualFile)   payload.actual_file       = actualFile;
        if (travelCats)   payload.travel_categories = travelCats;
        if (browser) {
          if (dawarichUrl) localStorage.setItem('s-dawarichUrl', dawarichUrl);
          if (actualUrl)   localStorage.setItem('s-actualUrl',   actualUrl);
          if (actualFile)  localStorage.setItem('s-actualFile',  actualFile);
          if (travelCats)  localStorage.setItem('s-travelCategories', travelCats);
        }
        if ($apiUrl && Object.keys(payload).length > 0) {
          await api('/api/settings/wizard/step', { method: 'POST', body: JSON.stringify(payload) });
        }
      }
      // Steps 3–5 reserved — just advance

      toast($t('wizardStepSaved'), 'success');
      if (step < TOTAL_STEPS) { step += 1; }
      else { open = false; }

    } catch (e) {
      toast(e.message || $t('wizardSaveError'), 'error');
    }
    saving = false;
  }

  function skip() {
    if (step < TOTAL_STEPS) step += 1;
    else open = false;
  }
</script>

{#if open}
  <!-- Backdrop -->
  <div class="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
    onclick={() => open = false}
    onkeydown={(e) => e.key === 'Escape' && (open = false)}
    role="button" tabindex="-1" aria-label={$t('settingsClose')}>
  </div>

  <!-- Panel -->
  <div class="fixed inset-0 md:inset-[4vh_12vw] lg:inset-[8vh_20vw] md:rounded-2xl z-50 flex flex-col shadow-2xl overflow-hidden"
    style="background:var(--ws-surface)">

    <!-- Header -->
    <div class="flex items-center justify-between px-6 py-4 border-b shrink-0"
      style="border-color:var(--ws-border);background:linear-gradient(135deg,var(--ws-accent) 0%,#b84928 100%)">
      <div class="flex items-center gap-3">
        <span class="text-2xl">🪄</span>
        <div>
          <h2 class="font-bold text-base" style="color:#fff5ec">{$t('wizardTitle')}</h2>
          <p class="text-xs" style="color:rgba(255,245,236,.7)">{$t('wizardSubtitle')}</p>
        </div>
      </div>
      <button onclick={() => open = false} class="p-1.5 rounded-lg hover:opacity-60" style="color:#fff5ec">✕</button>
    </div>

    <!-- Step progress bar -->
    <div class="flex items-center gap-2 px-6 py-3 shrink-0 border-b" style="border-color:var(--ws-border);background:var(--ws-surface2)">
      {#each Array.from({length: TOTAL_STEPS}, (_, i) => i + 1) as s}
        <div class="flex items-center gap-2" class:flex-1={s < TOTAL_STEPS}>
          <div class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 transition-all"
            style={s < step
              ? 'background:var(--ws-green);color:#fff'
              : s === step
                ? 'background:var(--ws-accent);color:#fff5ec;box-shadow:0 0 0 3px color-mix(in srgb,var(--ws-accent) 25%,transparent)'
                : 'background:var(--ws-border);color:var(--ws-muted)'}>
            {s < step ? '✓' : s}
          </div>
          {#if s < TOTAL_STEPS}
            <div class="h-0.5 flex-1 rounded-full transition-all"
              style={s < step ? 'background:var(--ws-green)' : 'background:var(--ws-border)'}></div>
          {/if}
        </div>
      {/each}
      <span class="text-xs ml-2 shrink-0" style="color:var(--ws-muted)">
        {$t('wizardStepOf').replace('{n}', step).replace('{total}', TOTAL_STEPS)}
      </span>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto p-6 space-y-5">

      {#if loading}
        <div class="flex items-center justify-center h-40">
          <span class="text-3xl animate-pulse">🪄</span>
        </div>

      {:else if step === 1}
        <!-- ── Step 1: Basis & Heimat ── -->
        <div>
          <h3 class="text-sm font-bold mb-1" style="color:var(--ws-text)">⚙️ {$t('wizardStep1Title')}</h3>
          <p class="text-xs mb-4" style="color:var(--ws-muted)">{$t('wizardStep1Desc')}</p>
        </div>

        <!-- Backend URL -->
        <div>
          <label class="text-xs font-bold uppercase tracking-wider block mb-1" style="color:var(--ws-muted)">{$t('settingsBackendUrl')}</label>
          <input type="url" bind:value={urlInput} placeholder="http://192.168.1.51:8765"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <div class="flex items-center gap-2 mt-2">
            <button onclick={testConnection} disabled={testing}
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

        <!-- Timezone -->
        <div>
          <label class="text-xs font-bold uppercase tracking-wider block mb-2" style="color:var(--ws-muted)">🌍 {$t('settingsTimezone')}</label>
          <select bind:value={appTimezone}
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)">
            {#each TIMEZONES as tz}
              <option value={tz}>{tz}</option>
            {/each}
          </select>
        </div>

        <!-- Date format -->
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
        </div>

        <!-- Currency -->
        <div>
          <label class="text-xs font-bold uppercase tracking-wider block mb-2" style="color:var(--ws-muted)">💱 {$t('settingsCurrency')}</label>
          <div class="flex flex-wrap gap-2">
            {#each CURRENCIES as cur}
              <button onclick={() => appCurrency = cur}
                class="px-3 py-1.5 rounded-xl text-xs border transition-all"
                style={appCurrency === cur
                  ? 'background:var(--ws-accent);color:#fff;border-color:var(--ws-accent)'
                  : 'background:var(--ws-surface2);color:var(--ws-muted);border-color:var(--ws-border)'}>
                {cur}
              </button>
            {/each}
          </div>
        </div>

        <!-- Home Location -->
        <div>
          <label class="text-xs font-bold uppercase tracking-wider block mb-1" style="color:var(--ws-muted)">🏠 {$t('settingsHomeLocation')}</label>
          <p class="text-xs mb-3" style="color:var(--ws-muted)">{$t('settingsHomeLocationHint')}</p>

          {#if homeName || (homeLat && homeLon)}
            <div class="flex items-center gap-2 mb-3 px-3 py-2 rounded-xl border"
              style="background:color-mix(in srgb,var(--ws-accent) 6%,var(--ws-surface));border-color:color-mix(in srgb,var(--ws-accent) 25%,var(--ws-border))">
              <span>🏠</span>
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

          <div class="flex gap-2">
            <input bind:value={homeSearch}
              placeholder={$t('settingsHomeSearchPlaceholder')}
              onkeydown={(e) => e.key === 'Enter' && searchHome()}
              class="flex-1 px-3 py-2 rounded-xl border text-sm"
              style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
            <button onclick={searchHome} disabled={homeSearching}
              class="px-3 py-2 rounded-xl text-xs border font-semibold transition-opacity hover:opacity-70 disabled:opacity-40"
              style="border-color:var(--ws-border);color:var(--ws-accent);background:var(--ws-surface2)">
              {homeSearching ? '⏳' : '🔍'}
            </button>
          </div>
          {#if homeSearchErr}
            <p class="text-xs mt-1" style="color:#dc2626">{homeSearchErr}</p>
          {/if}
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

      {:else if step === 2}
        <!-- ── Step 2: Self-Hosted Bridges ── -->
        <div>
          <h3 class="text-sm font-bold mb-1" style="color:var(--ws-text)">🔗 {$t('wizardStep2Title')}</h3>
          <p class="text-xs mb-4" style="color:var(--ws-muted)">{$t('wizardStep2Desc')}</p>
        </div>

        <!-- Dawarich -->
        <div class="space-y-2">
          <div class="flex items-center gap-2">
            <span class="text-base">📡</span>
            <span class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Dawarich</span>
          </div>
          <div class="text-xs rounded-xl px-3 py-2.5 border" style="background:rgba(var(--ws-accent-rgb,211,95,57),.06);border-color:var(--ws-border);color:var(--ws-muted)">
            💡 {$t('integrationsDawarichHint')}
          </div>
          <input bind:value={dawarichUrl} placeholder="https://dawarich.example.com"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <input bind:value={dawarichToken} type="password" placeholder="API Token"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <p class="text-[10px]" style="color:var(--ws-muted)">{$t('integrationsDawarichTokenHint')}</p>
        </div>

        <hr style="border-color:var(--ws-border)"/>

        <!-- Immich -->
        <div class="space-y-2">
          <div class="flex items-center gap-2">
            <span class="text-base">📸</span>
            <span class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Immich</span>
          </div>
          <div class="text-xs rounded-xl px-3 py-2.5 border" style="background:rgba(var(--ws-accent-rgb,211,95,57),.06);border-color:var(--ws-border);color:var(--ws-muted)">
            💡 {$t('integrationsImmichHint')}
          </div>
          <input bind:value={immichUrl} placeholder="https://immich.example.com"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <input bind:value={immichKey} type="password" placeholder="API Key"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" bind:checked={immichGeoSync} class="w-4 h-4 rounded accent-[var(--ws-accent)]"/>
            <span class="text-xs" style="color:var(--ws-muted)">{$t('integrationsImmichGeoSync')}</span>
          </label>
        </div>

        <hr style="border-color:var(--ws-border)"/>

        <!-- ActualBudget -->
        <div class="space-y-2">
          <div class="flex items-center gap-2">
            <span class="text-base">💳</span>
            <span class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">ActualBudget</span>
          </div>
          <div class="text-xs rounded-xl px-3 py-2.5 border" style="background:rgba(var(--ws-accent-rgb,211,95,57),.06);border-color:var(--ws-border);color:var(--ws-muted)">
            💡 {$t('integrationsActualHint')}
          </div>
          <input bind:value={actualUrl} placeholder="https://actual.example.com"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <input bind:value={actualToken} type="password" placeholder="Server Password"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <input bind:value={actualFile} placeholder={$t('integrationsActualFilePlaceholder')}
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <p class="text-[10px]" style="color:var(--ws-muted)">{$t('settingsActualHint')}</p>
          <input bind:value={travelCats} placeholder={$t('settingsCategoriesPlaceholder')}
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
        </div>

      {:else}
        <!-- Steps 3–5: Coming Soon placeholder -->
        <div class="flex flex-col items-center justify-center gap-4 py-16">
          <span class="text-5xl">🚧</span>
          <h3 class="text-base font-bold" style="color:var(--ws-text)">{$t('wizardComingSoon')}</h3>
          <p class="text-xs text-center max-w-xs" style="color:var(--ws-muted)">
            {$t('wizardComingSoonDesc').replace('{n}', step)}
          </p>
        </div>
      {/if}

    </div>

    <!-- Footer -->
    <div class="p-5 border-t shrink-0 flex items-center justify-between gap-3" style="border-color:var(--ws-border)">
      <!-- Back -->
      <button
        onclick={() => step > 1 ? step -= 1 : (open = false)}
        class="px-4 py-2.5 rounded-xl text-sm border font-semibold transition-opacity hover:opacity-70"
        style="border-color:var(--ws-border);color:var(--ws-muted);background:var(--ws-surface2)">
        {step > 1 ? $t('wwBtnBack') : $t('wizardClose')}
      </button>

      <!-- Skip + Next -->
      <div class="flex items-center gap-2">
        {#if step <= 2}
          <button onclick={skip}
            class="px-4 py-2.5 rounded-xl text-sm border font-semibold transition-opacity hover:opacity-70"
            style="border-color:var(--ws-border);color:var(--ws-muted)">
            {$t('onboardingSkip')}
          </button>
        {/if}

        <button onclick={saveAndNext} disabled={saving}
          class="px-6 py-2.5 rounded-xl text-sm font-bold transition-all hover:opacity-90 active:scale-[.98] disabled:opacity-40"
          style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec;min-width:120px">
          {#if saving}
            ⏳ {$t('wizardSaving')}
          {:else if step < TOTAL_STEPS}
            {$t('wizardNext')} →
          {:else}
            ✓ {$t('wizardFinish')}
          {/if}
        </button>
      </div>
    </div>

  </div>
{/if}

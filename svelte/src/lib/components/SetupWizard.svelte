<script>
  /**
   * SetupWizard.svelte — 5-Step Setup Wizard
   * Step 1: Basis & Heimat
   * Step 2: Self-Hosted Bridges (Dawarich, Immich, ActualBudget)
   * Step 3: Reise-Defaults (2 Akkordeons: Logistik + Persönlichkeit)
   * Step 4: KI & Engines (OpenAI, Gemini, SerpAPI)
   * Step 5: Erfolg + Konfetti
   *
   * Save-on-Next: safe partial save via POST /api/settings/wizard/step
   */
  import { t } from '$lib/i18n.js';
  import { apiUrl } from '$lib/stores.js';
  import { api, checkApiStatus } from '$lib/api.js';
  import { toast } from '$lib/toast.js';
  import { browser } from '$app/environment';
  import { onMount } from 'svelte';

  let { open = $bindable(false) } = $props();

  const TOTAL_STEPS = 5;
  let step    = $state(1);
  let saving  = $state(false);
  let loading = $state(false);

  // ── Step 1 state ──────────────────────────────────────────────────────────
  let urlInput      = $state('');
  let testing       = $state(false);
  let testOk        = $state(null);
  let appTimezone   = $state('Europe/Rome');
  let appDateFormat = $state('DD.MM.YYYY');
  let appCurrency   = $state('EUR');
  let homeLat       = $state('');
  let homeLon       = $state('');
  let homeName      = $state('');
  let homeSearch    = $state('');
  let homeResults   = $state([]);
  let homeSearching = $state(false);
  let homeSearchErr = $state('');

  // ── Step 2 state ──────────────────────────────────────────────────────────
  let dawarichUrl   = $state('');
  let dawarichToken = $state('');
  let immichUrl     = $state('');
  let immichKey     = $state('');
  let immichGeoSync = $state(false);
  let actualUrl     = $state('');
  let actualToken   = $state('');
  let actualFile    = $state('');
  let travelCats    = $state('');

  // ── Step 3 state ──────────────────────────────────────────────────────────
  let defAdults     = $state(2);
  let defChildren   = $state(0);
  let homeAirport   = $state('');
  let lugS10 = $state(0); let lugS20 = $state(0); let lugS23 = $state(0);
  let lugL10 = $state(0); let lugL20 = $state(1); let lugL23 = $state(0);
  let fDepMin = $state(''); let fDepMax = $state('');
  let fArrMin = $state(''); let fArrMax = $state('');
  let travelStyle   = $state('');
  let climatePref   = $state('');
  let landscapePref = $state('');
  let companions    = $state('');
  let wishText      = $state('');
  let travelMode    = $state('flight');
  let maxTravelTime = $state('any');
  let historyMode   = $state('blacklist');
  // Accordion open state for step 3
  let openLogistik    = $state(true);
  let openPersonality = $state(false);

  // ── Step 4 state ──────────────────────────────────────────────────────────
  let openaiKey  = $state('');
  let geminiKey  = $state('');
  let serpApiKey = $state('');

  const CURRENCIES = ['EUR','USD','GBP','CHF','JPY','AUD','CAD','SEK','NOK','DKK'];
  const TIMEZONES  = ['Europe/Rome','Europe/Berlin','Europe/Vienna','Europe/Zurich',
                      'Europe/London','Europe/Paris','America/New_York',
                      'America/Los_Angeles','Asia/Tokyo','Australia/Sydney','UTC'];

  const inputCls   = 'w-full px-3 py-2 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ws-accent)]';
  const inputStyle = 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)';
  const labelCls   = 'block text-xs font-bold uppercase tracking-wider mb-1';

  // ── Load ──────────────────────────────────────────────────────────────────
  async function loadExistingSettings() {
    loading = true;
    urlInput = $apiUrl || '';
    if (browser) {
      homeLat    = localStorage.getItem('s-homeLat')   || '';
      homeLon    = localStorage.getItem('s-homeLon')   || '';
      homeName   = localStorage.getItem('s-homeName')  || '';
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
          appTimezone   = s.timezone    || 'Europe/Rome';
          appDateFormat = s.date_format || 'DD.MM.YYYY';
          appCurrency   = s.currency    || 'EUR';
          if (s.home_lat)  homeLat = s.home_lat;
          if (s.home_lon)  homeLon = s.home_lon;
          if (s.home_name) { homeName = s.home_name; homeSearch = s.home_name; }
          serpApiKey = s.serpapi_key ? '••••••••' : '';
          geminiKey  = s.gemini_key  ? '••••••••' : '';
          openaiKey  = s.openai_key  ? '••••••••' : '';
        }
        if (us.status === 'fulfilled') {
          const u = us.value;
          dawarichUrl   = u.dawarich_url   || dawarichUrl;
          dawarichToken = u.dawarich_token ? '••••••••' : '';
          immichUrl     = u.immich_url     || '';
          immichKey     = u.immich_api_key ? '••••••••' : '';
          immichGeoSync = u.immich_geo_sync === 'true' || u.immich_geo_sync === true;
          actualUrl     = u.actual_url     || actualUrl;
          actualToken   = u.actual_token   ? '••••••••' : '';
          actualFile    = u.actual_file    || actualFile;
          travelCats    = u.travel_categories || '';
          defAdults     = parseInt(u.ww_adults)   || 2;
          defChildren   = parseInt(u.ww_children) || 0;
          homeAirport   = u.ww_home_airport || '';
          lugS10 = parseInt(u.ww_lug_s10) || 0; lugS20 = parseInt(u.ww_lug_s20) || 0;
          lugS23 = parseInt(u.ww_lug_s23) || 0; lugL10 = parseInt(u.ww_lug_l10) || 0;
          lugL20 = parseInt(u.ww_lug_l20) || 1; lugL23 = parseInt(u.ww_lug_l23) || 0;
          fDepMin = u.ww_dep_min || ''; fDepMax = u.ww_dep_max || '';
          fArrMin = u.ww_arr_min || ''; fArrMax = u.ww_arr_max || '';
          travelStyle   = u.travel_style   || '';
          climatePref   = u.climate_pref   || '';
          landscapePref = u.landscape_pref || '';
          companions    = u.companions     || '';
          wishText      = u.wish_text      || '';
          travelMode    = u.travel_mode    || 'flight';
          maxTravelTime = u.max_travel_time || 'any';
          historyMode   = u.history_mode   || 'blacklist';
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
    if (!$apiUrl) { homeSearchErr = $t('basicHomeNeedsBackend'); return; }
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

  async function testConnection() {
    testing = true; testOk = null;
    testOk = await checkApiStatus(urlInput);
    testing = false;
  }

  // ── Save-on-Next ─────────────────────────────────────────────────────────
  async function saveAndNext() {
    saving = true;
    // Persist backend URL always
    if (urlInput) {
      const clean = urlInput.trim().replace(/\/$/, '');
      apiUrl.set(clean);
      if (browser) localStorage.setItem('apiUrl', clean);
    }

    try {
      if (step === 1) {
        const p = {};
        if (appTimezone)   p.timezone    = appTimezone;
        if (appDateFormat) p.date_format = appDateFormat;
        if (appCurrency)   p.currency    = appCurrency;
        if (homeLat)       p.home_lat    = homeLat;
        if (homeLon)       p.home_lon    = homeLon;
        if (homeName)      p.home_name   = homeName;
        if (browser) {
          if (homeLat)  localStorage.setItem('s-homeLat',  homeLat);
          if (homeLon)  localStorage.setItem('s-homeLon',  homeLon);
          if (homeName) localStorage.setItem('s-homeName', homeName);
          localStorage.setItem('ws-timezone',    appTimezone   || 'Europe/Rome');
          localStorage.setItem('ws-date-format', appDateFormat || 'DD.MM.YYYY');
        }
        if ($apiUrl && Object.keys(p).length) await api('/api/settings/wizard/step', { method: 'POST', body: JSON.stringify(p) });

      } else if (step === 2) {
        const p = {};
        if (dawarichUrl   && dawarichUrl   !== '••••••••') p.dawarich_url   = dawarichUrl;
        if (dawarichToken && dawarichToken !== '••••••••') p.dawarich_token = dawarichToken;
        if (immichUrl     && immichUrl     !== '••••••••') p.immich_url     = immichUrl;
        if (immichKey     && immichKey     !== '••••••••') p.immich_api_key = immichKey;
        p.immich_geo_sync = immichGeoSync;
        if (actualUrl   && actualUrl   !== '••••••••') p.actual_url   = actualUrl;
        if (actualToken && actualToken !== '••••••••') p.actual_token = actualToken;
        if (actualFile)  p.actual_file       = actualFile;
        if (travelCats)  p.travel_categories = travelCats;
        if (browser) {
          if (dawarichUrl) localStorage.setItem('s-dawarichUrl', dawarichUrl);
          if (actualUrl)   localStorage.setItem('s-actualUrl',   actualUrl);
          if (actualFile)  localStorage.setItem('s-actualFile',  actualFile);
          if (travelCats)  localStorage.setItem('s-travelCategories', travelCats);
        }
        if ($apiUrl && Object.keys(p).length) await api('/api/settings/wizard/step', { method: 'POST', body: JSON.stringify(p) });

      } else if (step === 3) {
        // Step 3: user-level ww_* + personality prefs
        const p = {
          ww_adults: defAdults, ww_children: defChildren,
          ww_home_airport: homeAirport || null,
          ww_lug_s10: lugS10, ww_lug_s20: lugS20, ww_lug_s23: lugS23,
          ww_lug_l10: lugL10, ww_lug_l20: lugL20, ww_lug_l23: lugL23,
          ww_dep_min: fDepMin || null, ww_dep_max: fDepMax || null,
          ww_arr_min: fArrMin || null, ww_arr_max: fArrMax || null,
          travel_mode: travelMode, max_travel_time: maxTravelTime,
          history_mode: historyMode,
        };
        if (travelStyle)   p.travel_style   = travelStyle;
        if (climatePref)   p.climate_pref   = climatePref;
        if (landscapePref) p.landscape_pref = landscapePref;
        if (companions)    p.companions     = companions;
        if (wishText)      p.wish_text      = wishText;
        if ($apiUrl) await api('/api/settings/wizard/step', { method: 'POST', body: JSON.stringify(p) });

      } else if (step === 4) {
        // Step 4: API keys — global settings, only update if changed from masked
        const p = {};
        if (openaiKey  && openaiKey  !== '••••••••') p.openai_key  = openaiKey;
        if (geminiKey  && geminiKey  !== '••••••••') p.gemini_key  = geminiKey;
        if (serpApiKey && serpApiKey !== '••••••••') p.serpapi_key = serpApiKey;
        if ($apiUrl && Object.keys(p).length) await api('/api/settings/wizard/step', { method: 'POST', body: JSON.stringify(p) });
      }
      // Step 5: success screen — no save needed

      if (step < TOTAL_STEPS) {
        toast($t('wizardStepSaved'), 'success');
        step += 1;
      } else {
        // Final step done
        open = false;
      }
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
  <div class="fixed inset-0 md:inset-[4vh_12vw] lg:inset-[6vh_18vw] md:rounded-2xl z-50 flex flex-col shadow-2xl overflow-hidden"
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

    <!-- Progress bar -->
    <div class="flex items-center gap-1.5 px-6 py-3 shrink-0 border-b" style="border-color:var(--ws-border);background:var(--ws-surface2)">
      {#each Array.from({length: TOTAL_STEPS}, (_, i) => i + 1) as s}
        <div class="flex items-center gap-1.5" class:flex-1={s < TOTAL_STEPS}>
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
        <div>
          <h3 class="text-sm font-bold mb-1" style="color:var(--ws-text)">⚙️ {$t('wizardStep1Title')}</h3>
          <p class="text-xs mb-4" style="color:var(--ws-muted)">{$t('wizardStep1Desc')}</p>
        </div>

        <!-- Backend URL -->
        <div>
          <label class="text-xs font-bold uppercase tracking-wider block mb-1" style="color:var(--ws-muted)">{$t('settingsBackendUrl')}</label>
          <input type="url" bind:value={urlInput} placeholder="http://192.168.1.51:8765"
            class={inputCls} style={inputStyle}/>
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

        <div>
          <label class="text-xs font-bold uppercase tracking-wider block mb-2" style="color:var(--ws-muted)">🌍 {$t('settingsTimezone')}</label>
          <select bind:value={appTimezone} class={inputCls} style={inputStyle}>
            {#each TIMEZONES as tz}<option value={tz}>{tz}</option>{/each}
          </select>
        </div>

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
              <span class="text-xs font-semibold flex-1" style="color:var(--ws-text)">{homeName || `${parseFloat(homeLat).toFixed(4)}, ${parseFloat(homeLon).toFixed(4)}`}</span>
              {#if homeLat}<span class="text-[10px] font-mono" style="color:var(--ws-muted)">{parseFloat(homeLat).toFixed(4)}, {parseFloat(homeLon).toFixed(4)}</span>{/if}
              <button onclick={clearHome} class="text-xs px-2 py-0.5 rounded-lg hover:opacity-70" style="color:var(--ws-muted);background:var(--ws-surface2)">✕</button>
            </div>
          {/if}
          <div class="flex gap-2">
            <input bind:value={homeSearch} placeholder={$t('settingsHomeSearchPlaceholder')}
              onkeydown={(e) => e.key === 'Enter' && searchHome()}
              class="flex-1 px-3 py-2 rounded-xl border text-sm" style={inputStyle}/>
            <button onclick={searchHome} disabled={homeSearching}
              class="px-3 py-2 rounded-xl text-xs border font-semibold transition-opacity hover:opacity-70 disabled:opacity-40"
              style="border-color:var(--ws-border);color:var(--ws-accent);background:var(--ws-surface2)">
              {homeSearching ? '⏳' : '🔍'}
            </button>
          </div>
          {#if homeSearchErr}<p class="text-xs mt-1" style="color:#dc2626">{homeSearchErr}</p>{/if}
          {#if homeResults.length}
            <div class="mt-1 rounded-xl border overflow-hidden shadow-lg" style="background:var(--ws-surface);border-color:var(--ws-border)">
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
              <input bind:value={homeLat} placeholder="Lat: 46.7987" class="px-3 py-2 rounded-xl border text-sm" style={inputStyle}/>
              <input bind:value={homeLon} placeholder="Lon: 11.7188" class="px-3 py-2 rounded-xl border text-sm" style={inputStyle}/>
            </div>
          </details>
        </div>

      {:else if step === 2}
        <div>
          <h3 class="text-sm font-bold mb-1" style="color:var(--ws-text)">🔗 {$t('wizardStep2Title')}</h3>
          <p class="text-xs mb-4" style="color:var(--ws-muted)">{$t('wizardStep2Desc')}</p>
        </div>

        <div class="space-y-2">
          <div class="flex items-center gap-2"><span>📡</span><span class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Dawarich</span></div>
          <div class="text-xs rounded-xl px-3 py-2.5 border" style="background:rgba(var(--ws-accent-rgb,211,95,57),.06);border-color:var(--ws-border);color:var(--ws-muted)">💡 {$t('integrationsDawarichHint')}</div>
          <input bind:value={dawarichUrl} placeholder="https://dawarich.example.com" class={inputCls} style={inputStyle}/>
          <input bind:value={dawarichToken} type="password" placeholder="API Token" class={inputCls} style={inputStyle}/>
          <p class="text-[10px]" style="color:var(--ws-muted)">{$t('integrationsDawarichTokenHint')}</p>
        </div>

        <hr style="border-color:var(--ws-border)"/>

        <div class="space-y-2">
          <div class="flex items-center gap-2"><span>📸</span><span class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Immich</span></div>
          <div class="text-xs rounded-xl px-3 py-2.5 border" style="background:rgba(var(--ws-accent-rgb,211,95,57),.06);border-color:var(--ws-border);color:var(--ws-muted)">💡 {$t('integrationsImmichHint')}</div>
          <input bind:value={immichUrl} placeholder="https://immich.example.com" class={inputCls} style={inputStyle}/>
          <input bind:value={immichKey} type="password" placeholder="API Key" class={inputCls} style={inputStyle}/>
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" bind:checked={immichGeoSync} class="w-4 h-4 rounded accent-[var(--ws-accent)]"/>
            <span class="text-xs" style="color:var(--ws-muted)">{$t('integrationsImmichGeoSync')}</span>
          </label>
        </div>

        <hr style="border-color:var(--ws-border)"/>

        <div class="space-y-2">
          <div class="flex items-center gap-2"><span>💳</span><span class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">ActualBudget</span></div>
          <div class="text-xs rounded-xl px-3 py-2.5 border" style="background:rgba(var(--ws-accent-rgb,211,95,57),.06);border-color:var(--ws-border);color:var(--ws-muted)">💡 {$t('integrationsActualHint')}</div>
          <input bind:value={actualUrl} placeholder="https://actual.example.com" class={inputCls} style={inputStyle}/>
          <input bind:value={actualToken} type="password" placeholder="Server Password" class={inputCls} style={inputStyle}/>
          <input bind:value={actualFile} placeholder={$t('integrationsActualFilePlaceholder')} class={inputCls} style={inputStyle}/>
          <p class="text-[10px]" style="color:var(--ws-muted)">{$t('settingsActualHint')}</p>
          <input bind:value={travelCats} placeholder={$t('settingsCategoriesPlaceholder')} class={inputCls} style={inputStyle}/>
        </div>

      {:else if step === 3}
        <!-- ── Step 3: Reise-Defaults (2 Akkordeons) ── -->
        <div>
          <h3 class="text-sm font-bold mb-1" style="color:var(--ws-text)">🧳 {$t('wizardStep3Title')}</h3>
          <p class="text-xs mb-4" style="color:var(--ws-muted)">{$t('wizardStep3Desc')}</p>
        </div>

        <!-- Akkordeon 1: Logistik -->
        <div class="rounded-2xl border overflow-hidden" style="border-color:var(--ws-border)">
          <button onclick={() => openLogistik = !openLogistik}
            class="w-full flex items-center justify-between px-4 py-3 text-left transition-opacity hover:opacity-80"
            style="background:var(--ws-surface2)">
            <div class="flex items-center gap-2">
              <span>🧳</span>
              <span class="text-sm font-bold" style="color:var(--ws-text)">{$t('defaultsAccLogistikTitle')}</span>
              <span class="text-xs px-2 py-0.5 rounded-full" style="background:rgba(196,98,45,.1);color:var(--ws-accent)">{$t('defaultsAccLogistikSub')}</span>
            </div>
            <span class="text-xs" style="color:var(--ws-muted);transform:{openLogistik?'rotate(180deg)':'rotate(0)'}">▼</span>
          </button>
          {#if openLogistik}
            <div class="px-4 py-4 space-y-4 border-t" style="border-color:var(--ws-border)">

              <!-- Reisende -->
              <div>
                <div class="text-xs font-bold uppercase tracking-wider mb-3" style="color:var(--ws-muted)">👥 {$t('defaultsTravelers')}</div>
                <div class="grid grid-cols-3 gap-3">
                  <div class="rounded-xl border p-3 flex flex-col items-center gap-2" style="background:var(--ws-surface);border-color:var(--ws-border)">
                    <div class="text-xs font-semibold" style="color:var(--ws-muted)">{$t('wwAdults')}</div>
                    <div class="flex items-center gap-2">
                      <button onclick={() => defAdults = Math.max(1, defAdults - 1)} class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)">−</button>
                      <span class="text-sm font-bold w-5 text-center" style="color:var(--ws-text)">{defAdults}</span>
                      <button onclick={() => defAdults = Math.min(9, defAdults + 1)} class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center" style="background:var(--ws-accent);color:#fff">+</button>
                    </div>
                  </div>
                  <div class="rounded-xl border p-3 flex flex-col items-center gap-2" style="background:var(--ws-surface);border-color:var(--ws-border)">
                    <div class="text-xs font-semibold" style="color:var(--ws-muted)">{$t('wwChildren')}</div>
                    <div class="flex items-center gap-2">
                      <button onclick={() => defChildren = Math.max(0, defChildren - 1)} class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)">−</button>
                      <span class="text-sm font-bold w-5 text-center" style="color:var(--ws-text)">{defChildren}</span>
                      <button onclick={() => defChildren = Math.min(8, defChildren + 1)} class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center" style="background:var(--ws-accent);color:#fff">+</button>
                    </div>
                  </div>
                  <div class="rounded-xl border p-3 flex flex-col gap-1" style="background:var(--ws-surface);border-color:var(--ws-border)">
                    <div class="text-xs font-semibold" style="color:var(--ws-muted)">{$t('wwHomeAirportShort')}</div>
                    <input bind:value={homeAirport} maxlength="3" placeholder="BGY"
                      class="w-full px-2 py-1 rounded-lg border text-sm font-mono uppercase text-center focus:outline-none" style={inputStyle}/>
                  </div>
                </div>
              </div>

              <hr style="border-color:var(--ws-border)"/>

              <!-- Gepäck -->
              <div>
                <div class="text-xs font-bold uppercase tracking-wider mb-3" style="color:var(--ws-muted)">🧳 {$t('defaultsLuggage')}</div>
                <div class="grid grid-cols-2 gap-3">
                  {#each [
                    ['⚡ ' + $t('wwLugShort'), [['10 kg', () => lugS10, v => lugS10 = v], ['20 kg', () => lugS20, v => lugS20 = v], ['23 kg', () => lugS23, v => lugS23 = v]]],
                    ['🌍 ' + $t('wwLugLong'),  [['10 kg', () => lugL10, v => lugL10 = v], ['20 kg', () => lugL20, v => lugL20 = v], ['23 kg', () => lugL23, v => lugL23 = v]]],
                  ] as [title, rows]}
                    <div class="rounded-xl border p-3 space-y-2" style="background:var(--ws-surface);border-color:var(--ws-border)">
                      <div class="text-xs font-semibold mb-1" style="color:var(--ws-text)">{title}</div>
                      {#each rows as [label, getter, setter]}
                        <div class="flex items-center justify-between gap-2">
                          <span class="text-xs w-10 shrink-0" style="color:var(--ws-muted)">{label}</span>
                          <div class="flex items-center gap-1.5">
                            <button onclick={() => setter(Math.max(0, getter() - 1))} class="w-6 h-6 rounded border text-sm font-bold flex items-center justify-center" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)">−</button>
                            <span class="w-4 text-center text-sm font-bold" style="color:{getter()>0?'var(--ws-accent)':'var(--ws-muted)'}">{getter()}</span>
                            <button onclick={() => setter(Math.min(9, getter() + 1))} class="w-6 h-6 rounded border text-sm font-bold flex items-center justify-center" style="background:var(--ws-accent);color:#fff">+</button>
                          </div>
                        </div>
                      {/each}
                    </div>
                  {/each}
                </div>
              </div>

              <hr style="border-color:var(--ws-border)"/>

              <!-- Flugzeiten -->
              <div>
                <div class="text-xs font-bold uppercase tracking-wider mb-3" style="color:var(--ws-muted)">⏱️ {$t('defaultsFlightTimes')}</div>
                <div class="grid grid-cols-2 gap-4">
                  {#each [[$t('wwDepLabel'), fDepMin, fDepMax, v => fDepMin = v, v => fDepMax = v], [$t('wwArrLabel'), fArrMin, fArrMax, v => fArrMin = v, v => fArrMax = v]] as [title, vMin, vMax, setMin, setMax]}
                    <div class="space-y-2">
                      <div class="text-xs font-semibold" style="color:var(--ws-text)">{title}</div>
                      <div class="grid grid-cols-2 gap-2">
                        <div>
                          <label class={labelCls} style="color:var(--ws-muted)">{$t('wwTimeFrom')}</label>
                          <input type="time" value={vMin} oninput={(e) => setMin(e.currentTarget.value)} class={inputCls} style={inputStyle}/>
                        </div>
                        <div>
                          <label class={labelCls} style="color:var(--ws-muted)">{$t('wwTimeTo')}</label>
                          <input type="time" value={vMax} oninput={(e) => setMax(e.currentTarget.value)} class={inputCls} style={inputStyle}/>
                        </div>
                      </div>
                    </div>
                  {/each}
                </div>
                <p class="text-xs mt-2" style="color:var(--ws-muted)">{$t('defaultsFlightTimesHint')}</p>
              </div>

            </div>
          {/if}
        </div>

        <!-- Akkordeon 2: Persönlichkeit -->
        <div class="rounded-2xl border overflow-hidden" style="border-color:var(--ws-border)">
          <button onclick={() => openPersonality = !openPersonality}
            class="w-full flex items-center justify-between px-4 py-3 text-left transition-opacity hover:opacity-80"
            style="background:var(--ws-surface2)">
            <div class="flex items-center gap-2">
              <span>🧭</span>
              <span class="text-sm font-bold" style="color:var(--ws-text)">{$t('defaultsAccPersonalityTitle')}</span>
              <span class="text-xs px-2 py-0.5 rounded-full" style="background:rgba(196,98,45,.1);color:var(--ws-accent)">{$t('defaultsAccPersonalitySub')}</span>
            </div>
            <span class="text-xs" style="color:var(--ws-muted);transform:{openPersonality?'rotate(180deg)':'rotate(0)'}">▼</span>
          </button>
          {#if openPersonality}
            <div class="px-4 py-4 space-y-4 border-t" style="border-color:var(--ws-border)">
              {#each [
                [$t('defaultsTravelStyle'), travelStyle, v => travelStyle = v, [['adventure','🏔️ Abenteuer'],['relaxation','🏖️ Entspannung'],['culture','🏛️ Kultur'],['nature','🌿 Natur'],['city','🌆 City']]],
                [$t('defaultsClimate'), climatePref, v => climatePref = v, [['warm','☀️ Warm'],['mild','🌤️ Mild'],['cold','❄️ Kalt'],['any','🌍 Egal']]],
                [$t('defaultsLandscape'), landscapePref, v => landscapePref = v, [['mountains','⛰️ Berge'],['sea','🌊 Meer'],['forest','🌲 Wald'],['city','🏙️ Stadt'],['mix','🎲 Mix']]],
                [$t('defaultsCompanions'), companions, v => companions = v, [['solo','🧍 Solo'],['couple','👫 Pärchen'],['family','👨‍👩‍👧 Familie'],['friends','👯 Freunde']]],
              ] as [label, current, setter, opts]}
                <div>
                  <div class="text-xs font-semibold mb-2" style="color:var(--ws-text)">{label}</div>
                  <div class="flex flex-wrap gap-2">
                    {#each opts as [val, lbl]}
                      <button onclick={() => setter(current === val ? '' : val)}
                        class="px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all"
                        style={current === val
                          ? 'background:var(--ws-accent);border-color:var(--ws-accent);color:#fff5ec'
                          : 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)'}>
                        {lbl}
                      </button>
                    {/each}
                  </div>
                </div>
              {/each}

              <hr style="border-color:var(--ws-border)"/>

              <div>
                <div class="text-xs font-semibold mb-2" style="color:var(--ws-text)">🚗 {$t('defaultsTravelMode')}</div>
                <div class="flex gap-2">
                  {#each [['flight','✈️ Flugreise'],['car','🚗 Autoreise']] as [val, lbl]}
                    <button onclick={() => travelMode = val}
                      class="flex-1 py-2 rounded-xl border text-xs font-semibold transition-all"
                      style={travelMode === val ? 'background:var(--ws-accent);border-color:var(--ws-accent);color:#fff5ec' : 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)'}>{lbl}</button>
                  {/each}
                </div>
              </div>

              <div>
                <div class="text-xs font-semibold mb-2" style="color:var(--ws-text)">⏳ {$t('defaultsMaxTime')}</div>
                <div class="flex flex-wrap gap-2">
                  {#each [['2h','2h'],['4h','4h'],['8h','8h'],['12h','12h'],['12h+','12h+'],['any',$t('wwMaxTimeAny')]] as [val, lbl]}
                    <button onclick={() => maxTravelTime = val}
                      class="px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all"
                      style={maxTravelTime === val ? 'background:var(--ws-accent);border-color:var(--ws-accent);color:#fff5ec' : 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)'}>{lbl}</button>
                  {/each}
                </div>
              </div>

              <div>
                <div class="text-xs font-semibold mb-2" style="color:var(--ws-text)">💭 {$t('defaultsWishText')}</div>
                <textarea bind:value={wishText} maxlength="500" rows="3"
                  placeholder={$t('defaultsWishPlaceholder')}
                  class="w-full px-3 py-2 rounded-xl border text-sm resize-none focus:outline-none focus:ring-2 focus:ring-[var(--ws-accent)]"
                  style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"></textarea>
                <div class="text-xs mt-1 text-right" style="color:var(--ws-muted)">{(wishText||'').length}/500</div>
              </div>
            </div>
          {/if}
        </div>

      {:else if step === 4}
        <!-- ── Step 4: KI & Engines ── -->
        <div>
          <h3 class="text-sm font-bold mb-1" style="color:var(--ws-text)">🤖 {$t('wizardStep4Title')}</h3>
          <p class="text-xs mb-4" style="color:var(--ws-muted)">{$t('wizardStep4Desc')}</p>
        </div>

        <!-- OpenAI -->
        <div class="space-y-2">
          <div class="flex items-center gap-2">
            <span class="text-base">🧠</span>
            <span class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">OpenAI</span>
          </div>
          <div class="text-xs rounded-xl px-3 py-2.5 border" style="background:rgba(var(--ws-accent-rgb,211,95,57),.06);border-color:var(--ws-border);color:var(--ws-muted)">
            💡 {$t('wizardOpenAiHint')} →
            <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener"
              style="color:var(--ws-accent);text-decoration:underline">platform.openai.com/api-keys ↗</a>
          </div>
          <input bind:value={openaiKey} type="password" placeholder="sk-proj-…"
            class={inputCls} style={inputStyle}/>
          <p class="text-[10px]" style="color:var(--ws-muted)">{$t('settingsOpenaiHint')}</p>
        </div>

        <hr style="border-color:var(--ws-border)"/>

        <!-- Gemini -->
        <div class="space-y-2">
          <div class="flex items-center gap-2">
            <span class="text-base">✨</span>
            <span class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Google Gemini</span>
          </div>
          <div class="text-xs rounded-xl px-3 py-2.5 border" style="background:rgba(var(--ws-accent-rgb,211,95,57),.06);border-color:var(--ws-border);color:var(--ws-muted)">
            💡 {$t('wizardGeminiHint')} →
            <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener"
              style="color:var(--ws-accent);text-decoration:underline">aistudio.google.com/app/apikey ↗</a>
          </div>
          <input bind:value={geminiKey} type="password" placeholder="AIza…"
            class={inputCls} style={inputStyle}/>
          <p class="text-[10px]" style="color:var(--ws-muted)">{$t('settingsGeminiHint')}</p>
        </div>

        <hr style="border-color:var(--ws-border)"/>

        <!-- SerpAPI -->
        <div class="space-y-2">
          <div class="flex items-center gap-2">
            <span class="text-base">🔍</span>
            <span class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">SerpAPI</span>
          </div>
          <div class="text-xs rounded-xl px-3 py-2.5 border" style="background:rgba(var(--ws-accent-rgb,211,95,57),.06);border-color:var(--ws-border);color:var(--ws-muted)">
            💡 {$t('wizardSerpApiHint')} →
            <a href="https://serpapi.com/manage-api-key" target="_blank" rel="noopener"
              style="color:var(--ws-accent);text-decoration:underline">serpapi.com/manage-api-key ↗</a>
          </div>
          <input bind:value={serpApiKey} type="password" placeholder="…"
            class={inputCls} style={inputStyle}/>
          <p class="text-[10px]" style="color:var(--ws-muted)">{$t('settingsSerpHint')}</p>
        </div>

      {:else if step === 5}
        <!-- ── Step 5: Erfolgs-Screen + Konfetti ── -->
        <style>
          @keyframes ws-confetti-fall {
            0%   { transform: translateY(-20px) rotate(0deg);   opacity: 1; }
            100% { transform: translateY(320px) rotate(720deg); opacity: 0; }
          }
          .ws-confetti-piece {
            position: absolute;
            width: 10px; height: 10px;
            border-radius: 2px;
            animation: ws-confetti-fall linear forwards;
          }
        </style>

        <div class="relative flex flex-col items-center justify-center gap-6 py-10 overflow-hidden">
          <!-- Konfetti pieces -->
          {#each [
            {l:'12%', d:'0.1s', dur:'1.8s', c:'var(--ws-accent)'},
            {l:'25%', d:'0.3s', dur:'2.1s', c:'var(--ws-green)'},
            {l:'38%', d:'0.0s', dur:'1.6s', c:'#f59e0b'},
            {l:'52%', d:'0.5s', dur:'2.3s', c:'var(--ws-accent)'},
            {l:'65%', d:'0.2s', dur:'1.9s', c:'#8b5cf6'},
            {l:'78%', d:'0.4s', dur:'2.0s', c:'var(--ws-green)'},
            {l:'88%', d:'0.1s', dur:'1.7s', c:'#ef4444'},
            {l:'20%', d:'0.6s', dur:'2.2s', c:'#f59e0b'},
            {l:'45%', d:'0.35s', dur:'1.5s', c:'var(--ws-accent)'},
            {l:'70%', d:'0.15s', dur:'2.4s', c:'#8b5cf6'},
            {l:'5%',  d:'0.7s', dur:'1.8s', c:'var(--ws-green)'},
            {l:'92%', d:'0.25s', dur:'2.1s', c:'#ef4444'},
          ] as p}
            <div class="ws-confetti-piece pointer-events-none"
              style="left:{p.l};top:-10px;background:{p.c};animation-delay:{p.d};animation-duration:{p.dur}">
            </div>
          {/each}

          <div class="relative z-10 flex flex-col items-center gap-4 text-center max-w-sm">
            <div class="w-20 h-20 rounded-full flex items-center justify-center text-4xl"
              style="background:linear-gradient(135deg,var(--ws-accent),#b84928);box-shadow:0 4px 24px rgba(196,98,45,.35)">
              ✓
            </div>
            <h2 class="text-xl font-bold" style="color:var(--ws-text);font-family:var(--ws-serif)">
              {$t('wizardSuccessTitle')}
            </h2>
            <p class="text-sm leading-relaxed" style="color:var(--ws-muted)">
              {$t('wizardSuccessDesc')}
            </p>

            <!-- Summary chips -->
            <div class="flex flex-wrap gap-2 justify-center mt-2">
              {#if $apiUrl}
                <span class="text-xs px-3 py-1.5 rounded-full font-semibold"
                  style="background:color-mix(in srgb,var(--ws-green) 12%,var(--ws-surface));border:1px solid color-mix(in srgb,var(--ws-green) 30%,var(--ws-border));color:var(--ws-green)">
                  ✓ {$t('wizardSuccessBackend')}
                </span>
              {/if}
              {#if homeName}
                <span class="text-xs px-3 py-1.5 rounded-full font-semibold"
                  style="background:color-mix(in srgb,var(--ws-accent) 10%,var(--ws-surface));border:1px solid color-mix(in srgb,var(--ws-accent) 25%,var(--ws-border));color:var(--ws-accent)">
                  🏠 {homeName}
                </span>
              {/if}
              {#if dawarichUrl}
                <span class="text-xs px-3 py-1.5 rounded-full font-semibold"
                  style="background:color-mix(in srgb,var(--ws-accent) 10%,var(--ws-surface));border:1px solid color-mix(in srgb,var(--ws-accent) 25%,var(--ws-border));color:var(--ws-accent)">
                  📡 Dawarich
                </span>
              {/if}
              {#if geminiKey || openaiKey}
                <span class="text-xs px-3 py-1.5 rounded-full font-semibold"
                  style="background:color-mix(in srgb,var(--ws-accent) 10%,var(--ws-surface));border:1px solid color-mix(in srgb,var(--ws-accent) 25%,var(--ws-border));color:var(--ws-accent)">
                  🤖 {$t('wizardSuccessAi')}
                </span>
              {/if}
            </div>

            <p class="text-xs mt-1" style="color:var(--ws-muted)">{$t('wizardSuccessHint')}</p>
          </div>
        </div>
      {/if}

    </div>

    <!-- Footer -->
    <div class="p-5 border-t shrink-0 flex items-center justify-between gap-3" style="border-color:var(--ws-border)">
      <button
        onclick={() => step > 1 ? step -= 1 : (open = false)}
        class="px-4 py-2.5 rounded-xl text-sm border font-semibold transition-opacity hover:opacity-70"
        style="border-color:var(--ws-border);color:var(--ws-muted);background:var(--ws-surface2)">
        {step > 1 ? $t('wwBtnBack') : $t('wizardClose')}
      </button>

      <div class="flex items-center gap-2">
        {#if step < 5}
          <button onclick={skip}
            class="px-4 py-2.5 rounded-xl text-sm border font-semibold transition-opacity hover:opacity-70"
            style="border-color:var(--ws-border);color:var(--ws-muted)">
            {$t('onboardingSkip')}
          </button>
        {/if}

        <button onclick={saveAndNext} disabled={saving}
          class="px-6 py-2.5 rounded-xl text-sm font-bold transition-all hover:opacity-90 active:scale-[.98] disabled:opacity-40"
          style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec;min-width:130px">
          {#if saving}
            ⏳ {$t('wizardSaving')}
          {:else if step === 5}
            🎉 {$t('wizardFinish')}
          {:else}
            {$t('wizardNext')} →
          {/if}
        </button>
      </div>
    </div>

  </div>
{/if}

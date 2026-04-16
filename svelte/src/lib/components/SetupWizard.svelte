<script>
  /**
   * SetupWizard.svelte — 5-Step Setup Wizard (+ Step 0: Vision)
   * Step 0: Vision — Willkommen, was ist WanderSuite
   * Step 1: Basis & Heimat
   * Step 2: Self-Hosted Bridges
   * Step 3: Reise-Defaults (2 Akkordeons)
   * Step 4: KI & Engines
   * Step 5: Erfolg + Konfetti
   *
   * Save-on-Next: safe partial save via POST /api/settings/wizard/step
   * Help buttons open FieldGuide with deep-link tab per step.
   */
  import { t } from '$lib/i18n.js';
  import { apiUrl, wizardOpen } from '$lib/stores.js';
  import { api, checkApiStatus } from '$lib/api.js';
  import { toast } from '$lib/toast.js';
  import { browser } from '$app/environment';
  import FieldGuide from './FieldGuide.svelte';

  let { open = $bindable(false) } = $props();

  const TOTAL_STEPS = 5;   // Steps 1–5; step 0 = intro/vision
  let step    = $state(0);
  let saving  = $state(false);
  let loading = $state(false);

  // FieldGuide deep-link state
  let guideOpen = $state(false);
  let guideTab  = $state('vision');

  function openHelp(tab = 'vision') {
    guideTab = tab;
    guideOpen = true;
  }

  // Help tab per wizard step
  const STEP_HELP_TAB = ['vision', 'wizard', 'bridges', 'trips', 'apis', 'vision'];

  // ── Step 1 state ──────────────────────────────────────────────────────────
  let urlInput      = $state('');
  let testing       = $state(false);
  let testOk        = $state(null);
  let appTimezone   = $state('Europe/Rome');
  let appDateFormat = $state('DD.MM.YYYY');
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
  let openLogistik    = $state(true);
  let openPersonality = $state(false);

  // ── Step 4 state ──────────────────────────────────────────────────────────
  let openaiKey  = $state('');
  let geminiKey  = $state('');
  let serpApiKey = $state('');

  const TIMEZONES  = ['Europe/Rome','Europe/Berlin','Europe/Vienna','Europe/Zurich',
                      'Europe/London','Europe/Paris','America/New_York',
                      'America/Los_Angeles','Asia/Tokyo','Australia/Sydney','UTC'];

  const inputCls   = 'w-full px-3 py-2 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ws-accent)]';
  const inputStyle = 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)';
  const labelCls   = 'block text-xs font-bold uppercase tracking-wider mb-1';

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
        const [gs, us] = await Promise.allSettled([api('/api/settings'), api('/api/settings/user')]);
        if (gs.status === 'fulfilled') {
          const s = gs.value;
          appTimezone   = s.timezone    || 'Europe/Rome';
          appDateFormat = s.date_format || 'DD.MM.YYYY';
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
          lugS10=parseInt(u.ww_lug_s10)||0; lugS20=parseInt(u.ww_lug_s20)||0; lugS23=parseInt(u.ww_lug_s23)||0;
          lugL10=parseInt(u.ww_lug_l10)||0; lugL20=parseInt(u.ww_lug_l20)||1; lugL23=parseInt(u.ww_lug_l23)||0;
          fDepMin=u.ww_dep_min||''; fDepMax=u.ww_dep_max||''; fArrMin=u.ww_arr_min||''; fArrMax=u.ww_arr_max||'';
          travelStyle=u.travel_style||''; climatePref=u.climate_pref||''; landscapePref=u.landscape_pref||'';
          companions=u.companions||''; wishText=u.wish_text||''; travelMode=u.travel_mode||'flight';
          maxTravelTime=u.max_travel_time||'any'; historyMode=u.history_mode||'blacklist';
        }
      } catch {}
    }
    loading = false;
  }

  $effect(() => { if (open) { step = 0; loadExistingSettings(); } });

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

  function clearHome() { homeLat=''; homeLon=''; homeName=''; homeSearch=''; homeResults=[]; }

  async function testConnection() {
    testing = true; testOk = null;
    testOk = await checkApiStatus(urlInput);
    testing = false;
  }

  async function saveAndNext() {
    // Step 0 is vision — no save, just advance
    if (step === 0) { step = 1; return; }

    saving = true;
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
        const p = {
          ww_adults: defAdults, ww_children: defChildren,
          ww_home_airport: homeAirport || null,
          ww_lug_s10: lugS10, ww_lug_s20: lugS20, ww_lug_s23: lugS23,
          ww_lug_l10: lugL10, ww_lug_l20: lugL20, ww_lug_l23: lugL23,
          ww_dep_min: fDepMin || null, ww_dep_max: fDepMax || null,
          ww_arr_min: fArrMin || null, ww_arr_max: fArrMax || null,
          travel_mode: travelMode, max_travel_time: maxTravelTime, history_mode: historyMode,
        };
        if (travelStyle)   p.travel_style   = travelStyle;
        if (climatePref)   p.climate_pref   = climatePref;
        if (landscapePref) p.landscape_pref = landscapePref;
        if (companions)    p.companions     = companions;
        if (wishText)      p.wish_text      = wishText;
        if ($apiUrl) await api('/api/settings/wizard/step', { method: 'POST', body: JSON.stringify(p) });

      } else if (step === 4) {
        const p = {};
        if (openaiKey  && openaiKey  !== '••••••••') p.openai_key  = openaiKey;
        if (geminiKey  && geminiKey  !== '••••••••') p.gemini_key  = geminiKey;
        if (serpApiKey && serpApiKey !== '••••••••') p.serpapi_key = serpApiKey;
        if ($apiUrl && Object.keys(p).length) await api('/api/settings/wizard/step', { method: 'POST', body: JSON.stringify(p) });
      }

      if (step < TOTAL_STEPS) {
        toast($t('wizardStepSaved'), 'success');
        step += 1;
      } else {
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

<!-- FieldGuide deep-link modal -->
<FieldGuide bind:open={guideOpen} initialTab={guideTab} />

{#if open}
  <div class="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
    onclick={() => open = false}
    onkeydown={(e) => e.key === 'Escape' && (open = false)}
    role="button" tabindex="-1" aria-label={$t('settingsClose')}>
  </div>

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
      <div class="flex items-center gap-2">
        <button onclick={() => open = false} class="p-1.5 rounded-lg hover:opacity-60" style="color:#fff5ec">✕</button>
      </div>
    </div>

    <!-- Progress bar (only for steps 1–5) -->
    {#if step > 0}
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
    {/if}

    <!-- Content -->
    <div class="flex-1 overflow-y-auto p-6 space-y-5">

      {#if loading && step > 0}
        <div class="flex items-center justify-center h-40">
          <span class="text-3xl animate-pulse">🪄</span>
        </div>

      {:else if step === 0}
        <!-- ── Step 0: Vision / Welcome ── -->
        <div class="flex flex-col items-center text-center gap-4 pt-4 pb-6">
          <div class="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl"
            style="background:linear-gradient(135deg,var(--ws-accent),#b84928);box-shadow:0 4px 20px rgba(196,98,45,.3)">
            🧭
          </div>
          <div>
            <h2 class="text-xl font-bold mb-2" style="color:var(--ws-text);font-family:var(--ws-serif)">{$t('wizardVisionTitle')}</h2>
            <p class="text-sm leading-relaxed max-w-md" style="color:var(--ws-muted)">{$t('wizardVisionSubtitle')}</p>
          </div>
        </div>

        <!-- 3 Phases -->
        <div class="space-y-3">
          {#each [
            { icon: '✈️', color: 'var(--ws-accent)', key: 'wizardVisionPhase1' },
            { icon: '🌍', color: 'var(--ws-green)',  key: 'wizardVisionPhase2' },
            { icon: '📓', color: 'var(--ws-muted)',  key: 'wizardVisionPhase3' },
          ] as ph}
            <div class="flex gap-3 items-start rounded-2xl border p-4"
              style="background:var(--ws-surface2);border-color:var(--ws-border)">
              <span class="text-2xl shrink-0">{ph.icon}</span>
              <div>
                <div class="font-bold text-sm mb-1" style="color:{ph.color}">{$t(ph.key + 'Title')}</div>
                <p class="text-xs leading-relaxed" style="color:var(--ws-muted)">{$t(ph.key + 'Desc')}</p>
              </div>
            </div>
          {/each}
        </div>

        <!-- Feature highlights -->
        <div class="rounded-2xl border p-4" style="background:color-mix(in srgb,var(--ws-accent) 5%,var(--ws-surface2));border-color:color-mix(in srgb,var(--ws-accent) 20%,var(--ws-border))">
          <div class="text-xs font-bold uppercase tracking-wider mb-3" style="color:var(--ws-accent)">{$t('wizardVisionFeaturesTitle')}</div>
          <div class="grid grid-cols-2 gap-2">
            {#each ($t('wizardVisionFeatures') || '').split('|').filter(Boolean) as feat}
              <div class="flex gap-1.5 text-xs" style="color:var(--ws-text)">
                <span style="color:var(--ws-accent)" class="shrink-0">✓</span> {feat}
              </div>
            {/each}
          </div>
        </div>

        <p class="text-xs text-center" style="color:var(--ws-muted)">{$t('wizardVisionCta')}</p>

      {:else if step === 1}
        <div>
          <h3 class="text-sm font-bold mb-1" style="color:var(--ws-text)">⚙️ {$t('wizardStep1Title')}</h3>
          <p class="text-xs mb-4" style="color:var(--ws-muted)">{$t('wizardStep1Desc')}</p>
        </div>

        <div>
          <label class="text-xs font-bold uppercase tracking-wider block mb-1" style="color:var(--ws-muted)">{$t('settingsBackendUrl')}</label>
          <input type="url" bind:value={urlInput} placeholder="http://192.168.1.51:8765" class={inputCls} style={inputStyle}/>
          <div class="flex items-center gap-2 mt-2">
            <button onclick={testConnection} disabled={testing}
              class="px-4 py-1.5 rounded-xl text-xs border transition-opacity hover:opacity-70 disabled:opacity-40"
              style="border-color:var(--ws-border);color:var(--ws-muted)">
              {testing ? $t('settingsTesting') : $t('settingsConnect')}
            </button>
            {#if testOk === true}<span class="text-xs font-medium" style="color:var(--ws-green)">{$t('settingsConnected')}</span>{/if}
            {#if testOk === false}<span class="text-xs font-medium" style="color:#dc2626">{$t('settingsNotReachable')}</span>{/if}
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
              class="px-3 py-2 rounded-xl text-xs border font-semibold hover:opacity-70 disabled:opacity-40"
              style="border-color:var(--ws-border);color:var(--ws-accent);background:var(--ws-surface2)">
              {homeSearching ? '⏳' : '🔍'}
            </button>
          </div>
          {#if homeSearchErr}<p class="text-xs mt-1" style="color:#dc2626">{homeSearchErr}</p>{/if}
          {#if homeResults.length}
            <div class="mt-1 rounded-xl border overflow-hidden shadow-lg" style="background:var(--ws-surface);border-color:var(--ws-border)">
              {#each homeResults as r}
                <button onclick={() => selectHome(r)}
                  class="w-full text-left px-4 py-2.5 text-xs hover:opacity-80 border-b last:border-b-0"
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
        <div>
          <h3 class="text-sm font-bold mb-1" style="color:var(--ws-text)">🧳 {$t('wizardStep3Title')}</h3>
          <p class="text-xs mb-4" style="color:var(--ws-muted)">{$t('wizardStep3Desc')}</p>
        </div>

        <!-- Akkordeon 1: Logistik -->
        <div class="rounded-2xl border overflow-hidden" style="border-color:var(--ws-border)">
          <button onclick={() => openLogistik = !openLogistik}
            class="w-full flex items-center justify-between px-4 py-3 text-left hover:opacity-80"
            style="background:var(--ws-surface2)">
            <div class="flex items-center gap-2">
              <span>🧳</span>
              <span class="text-sm font-bold" style="color:var(--ws-text)">{$t('defaultsAccLogistikTitle')}</span>
              <span class="text-xs px-2 py-0.5 rounded-full" style="background:rgba(196,98,45,.1);color:var(--ws-accent)">{$t('defaultsAccLogistikSub')}</span>
            </div>
            <span class="text-xs" style="color:var(--ws-muted);transform:{openLogistik?'rotate(180deg)':'none'}">▼</span>
          </button>
          {#if openLogistik}
            <div class="px-4 py-4 space-y-4 border-t" style="border-color:var(--ws-border)">
              <div>
                <div class="text-xs font-bold uppercase tracking-wider mb-3" style="color:var(--ws-muted)">👥 {$t('defaultsTravelers')}</div>
                <div class="grid grid-cols-3 gap-3">
                  {#each [[defAdults, v => defAdults = v, 1, 9, $t('wwAdults')], [defChildren, v => defChildren = v, 0, 8, $t('wwChildren')]] as [val, setter, min, max, label]}
                    <div class="rounded-xl border p-3 flex flex-col items-center gap-2" style="background:var(--ws-surface);border-color:var(--ws-border)">
                      <div class="text-xs font-semibold" style="color:var(--ws-muted)">{label}</div>
                      <div class="flex items-center gap-2">
                        <button onclick={() => setter(Math.max(min, val - 1))} class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center" style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)">−</button>
                        <span class="text-sm font-bold w-5 text-center" style="color:var(--ws-text)">{val}</span>
                        <button onclick={() => setter(Math.min(max, val + 1))} class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center" style="background:var(--ws-accent);color:#fff">+</button>
                      </div>
                    </div>
                  {/each}
                  <div class="rounded-xl border p-3 flex flex-col gap-1" style="background:var(--ws-surface);border-color:var(--ws-border)">
                    <div class="text-xs font-semibold" style="color:var(--ws-muted)">{$t('wwHomeAirportShort')}</div>
                    <input bind:value={homeAirport} maxlength="3" placeholder="BGY"
                      class="w-full px-2 py-1 rounded-lg border text-sm font-mono uppercase text-center focus:outline-none" style={inputStyle}/>
                  </div>
                </div>
              </div>
            </div>
          {/if}
        </div>

        <!-- Akkordeon 2: Persönlichkeit -->
        <div class="rounded-2xl border overflow-hidden" style="border-color:var(--ws-border)">
          <button onclick={() => openPersonality = !openPersonality}
            class="w-full flex items-center justify-between px-4 py-3 text-left hover:opacity-80"
            style="background:var(--ws-surface2)">
            <div class="flex items-center gap-2">
              <span>🧭</span>
              <span class="text-sm font-bold" style="color:var(--ws-text)">{$t('defaultsAccPersonalityTitle')}</span>
              <span class="text-xs px-2 py-0.5 rounded-full" style="background:rgba(196,98,45,.1);color:var(--ws-accent)">{$t('defaultsAccPersonalitySub')}</span>
            </div>
            <span class="text-xs" style="color:var(--ws-muted);transform:{openPersonality?'rotate(180deg)':'none'}">▼</span>
          </button>
          {#if openPersonality}
            <div class="px-4 py-4 space-y-4 border-t" style="border-color:var(--ws-border)">
              {#each [
                [$t('defaultsTravelStyle'), travelStyle, v => travelStyle = v, [['adventure','🏔️ Abenteuer'],['relaxation','🏖️ Entspannung'],['culture','🏛️ Kultur'],['nature','🌿 Natur'],['city','🌆 City']]],
                [$t('defaultsClimate'), climatePref, v => climatePref = v, [['warm','☀️ Warm'],['mild','🌤️ Mild'],['cold','❄️ Kalt'],['any','🌍 Egal']]],
                [$t('defaultsCompanions'), companions, v => companions = v, [['solo','🧍 Solo'],['couple','👫 Pärchen'],['family','👨‍👩‍👧 Familie'],['friends','👯 Freunde']]],
              ] as [lbl, cur, setter, opts]}
                <div>
                  <div class="text-xs font-semibold mb-2" style="color:var(--ws-text)">{lbl}</div>
                  <div class="flex flex-wrap gap-2">
                    {#each opts as [val, optlbl]}
                      <button onclick={() => setter(cur === val ? '' : val)}
                        class="px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all"
                        style={cur === val
                          ? 'background:var(--ws-accent);border-color:var(--ws-accent);color:#fff5ec'
                          : 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)'}>
                        {optlbl}
                      </button>
                    {/each}
                  </div>
                </div>
              {/each}
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
        <div>
          <h3 class="text-sm font-bold mb-1" style="color:var(--ws-text)">🤖 {$t('wizardStep4Title')}</h3>
          <p class="text-xs mb-4" style="color:var(--ws-muted)">{$t('wizardStep4Desc')}</p>
        </div>
        {#each [
          { icon: '🧠', name: 'OpenAI', bind: openaiKey, setter: v => openaiKey = v, ph: 'sk-proj-…', hint: 'fgOpenAiDesc', url: 'platform.openai.com/api-keys', urlHint: 'wizardOpenAiHint', keyHint: 'settingsOpenaiHint' },
          { icon: '✨', name: 'Google Gemini', bind: geminiKey, setter: v => geminiKey = v, ph: 'AIza…', hint: 'fgGeminiDesc', url: 'aistudio.google.com/app/apikey', urlHint: 'wizardGeminiHint', keyHint: 'settingsGeminiHint' },
          { icon: '🔍', name: 'SerpAPI', bind: serpApiKey, setter: v => serpApiKey = v, ph: '…', hint: 'fgSerpApiDesc', url: 'serpapi.com/manage-api-key', urlHint: 'wizardSerpApiHint', keyHint: 'settingsSerpHint' },
        ] as k, i}
          {#if i > 0}<hr style="border-color:var(--ws-border)"/>{/if}
          <div class="space-y-2">
            <div class="flex items-center gap-2"><span class="text-base">{k.icon}</span><span class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">{k.name}</span></div>
            <div class="text-xs rounded-xl px-3 py-2.5 border" style="background:rgba(var(--ws-accent-rgb,211,95,57),.06);border-color:var(--ws-border);color:var(--ws-muted)">
              💡 {$t(k.urlHint)} → <a href="https://{k.url}" target="_blank" rel="noopener" style="color:var(--ws-accent);text-decoration:underline">{k.url} ↗</a>
            </div>
            <input value={k.bind} oninput={(e) => k.setter(e.currentTarget.value)} type="password" placeholder={k.ph} class={inputCls} style={inputStyle}/>
            <p class="text-[10px]" style="color:var(--ws-muted)">{$t(k.keyHint)}</p>
          </div>
        {/each}

      {:else if step === 5}
        <!-- Step 5: Success + Confetti -->
        <style>
          @keyframes ws-confetti-fall {
            0%   { transform: translateY(-20px) rotate(0deg);   opacity: 1; }
            100% { transform: translateY(340px) rotate(720deg); opacity: 0; }
          }
          .ws-confetti-piece { position: absolute; width: 10px; height: 10px; border-radius: 2px; animation: ws-confetti-fall linear forwards; }
        </style>
        <div class="relative flex flex-col items-center justify-center gap-6 py-10 overflow-hidden">
          {#each [{l:'12%',d:'.1s',dur:'1.8s',c:'var(--ws-accent)'},{l:'25%',d:'.3s',dur:'2.1s',c:'var(--ws-green)'},{l:'38%',d:'0s',dur:'1.6s',c:'#f59e0b'},{l:'52%',d:'.5s',dur:'2.3s',c:'var(--ws-accent)'},{l:'65%',d:'.2s',dur:'1.9s',c:'#8b5cf6'},{l:'78%',d:'.4s',dur:'2.0s',c:'var(--ws-green)'},{l:'88%',d:'.1s',dur:'1.7s',c:'#ef4444'},{l:'20%',d:'.6s',dur:'2.2s',c:'#f59e0b'},{l:'45%',d:'.35s',dur:'1.5s',c:'var(--ws-accent)'},{l:'70%',d:'.15s',dur:'2.4s',c:'#8b5cf6'},{l:'5%',d:'.7s',dur:'1.8s',c:'var(--ws-green)'},{l:'92%',d:'.25s',dur:'2.1s',c:'#ef4444'}] as p}
            <div class="ws-confetti-piece pointer-events-none" style="left:{p.l};top:-10px;background:{p.c};animation-delay:{p.d};animation-duration:{p.dur}"></div>
          {/each}
          <div class="relative z-10 flex flex-col items-center gap-4 text-center max-w-sm">
            <div class="w-20 h-20 rounded-full flex items-center justify-center text-4xl"
              style="background:linear-gradient(135deg,var(--ws-accent),#b84928);box-shadow:0 4px 24px rgba(196,98,45,.35)">✓</div>
            <h2 class="text-xl font-bold" style="color:var(--ws-text);font-family:var(--ws-serif)">{$t('wizardSuccessTitle')}</h2>
            <p class="text-sm leading-relaxed" style="color:var(--ws-muted)">{$t('wizardSuccessDesc')}</p>
            <div class="flex flex-wrap gap-2 justify-center mt-2">
              {#if $apiUrl}<span class="text-xs px-3 py-1.5 rounded-full font-semibold" style="background:color-mix(in srgb,var(--ws-green) 12%,var(--ws-surface));border:1px solid color-mix(in srgb,var(--ws-green) 30%,var(--ws-border));color:var(--ws-green)">✓ {$t('wizardSuccessBackend')}</span>{/if}
              {#if homeName}<span class="text-xs px-3 py-1.5 rounded-full font-semibold" style="background:color-mix(in srgb,var(--ws-accent) 10%,var(--ws-surface));border:1px solid color-mix(in srgb,var(--ws-accent) 25%,var(--ws-border));color:var(--ws-accent)">🏠 {homeName}</span>{/if}
              {#if dawarichUrl}<span class="text-xs px-3 py-1.5 rounded-full font-semibold" style="background:color-mix(in srgb,var(--ws-accent) 10%,var(--ws-surface));border:1px solid color-mix(in srgb,var(--ws-accent) 25%,var(--ws-border));color:var(--ws-accent)">📡 Dawarich</span>{/if}
              {#if geminiKey || openaiKey}<span class="text-xs px-3 py-1.5 rounded-full font-semibold" style="background:color-mix(in srgb,var(--ws-accent) 10%,var(--ws-surface));border:1px solid color-mix(in srgb,var(--ws-accent) 25%,var(--ws-border));color:var(--ws-accent)">🤖 {$t('wizardSuccessAi')}</span>{/if}
            </div>
            <p class="text-xs mt-1" style="color:var(--ws-muted)">{$t('wizardSuccessHint')}</p>
          </div>
        </div>
      {/if}

    </div>

    <!-- Footer -->
    <div class="p-5 border-t shrink-0 flex items-center justify-between gap-3" style="border-color:var(--ws-border)">
      <button
        onclick={() => step > 0 ? step -= 1 : (open = false)}
        class="px-4 py-2.5 rounded-xl text-sm border font-semibold transition-opacity hover:opacity-70"
        style="border-color:var(--ws-border);color:var(--ws-muted);background:var(--ws-surface2)">
        {step > 0 ? $t('wwBtnBack') : $t('wizardClose')}
      </button>

      <div class="flex items-center gap-2">
        {#if step > 0 && step < 5}
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
          {:else if step === 0}
            {$t('wizardVisionCta')} →
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

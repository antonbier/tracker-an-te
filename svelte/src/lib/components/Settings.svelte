<script>
  import { apiUrl, theme, appStatus, isAdmin, currentUser } from '$lib/stores.js';
  import { toast } from '$lib/toast.js';
  import { t } from '$lib/i18n.js';
  import { checkApiStatus, api } from '$lib/api.js';
  import { browser } from '$app/environment';

  import BasicTab         from './settings/BasicTab.svelte';
  import IntegrationsTab  from './settings/IntegrationsTab.svelte';
  import NotificationsTab from './settings/NotificationsTab.svelte';
  import MyspaceTab       from './settings/MyspaceTab.svelte';
  import AccountTab       from './settings/AccountTab.svelte';
  import AdminTab         from './settings/AdminTab.svelte';
  import SchedulerTab     from './settings/SchedulerTab.svelte';

  let { open = $bindable(false) } = $props();

  function ls(key, fallback = '') { return browser ? (localStorage.getItem(key) || fallback) : fallback; }

  // ── Tab state ─────────────────────────────────────────────────────────────
  let activeTab = $state('basic');

  const TAB_IDS_NOAUTH = ['basic', 'integrations', 'notifications', 'scheduler'];
  const TAB_IDS_AUTH   = ['basic', 'notifications', 'myspace', 'account', 'scheduler'];
  const TAB_IDS_ADMIN  = ['basic', 'notifications', 'myspace', 'account', 'admin', 'scheduler'];

  const authEnabled = $derived(!!$appStatus?.auth_enabled);

  const tabIds = $derived(
    ($isAdmin && authEnabled) ? TAB_IDS_ADMIN :
    authEnabled ? TAB_IDS_AUTH :
    TAB_IDS_NOAUTH
  );

  const tabLabels = $derived({
    basic:         $t('settingsBasic'),
    integrations:  $t('settingsIntegrations'),
    notifications: $t('settingsNotifications'),
    myspace:       $t('settingsMyspace'),
    account:       $t('settingsAccount'),
    admin:         $t('settingsAdmin'),
    scheduler:     '⏰ ' + ($t('settingsScheduler') || 'Scheduler'),
  });

  // ── Basic tab state ───────────────────────────────────────────────────────
  let urlInput      = $state('');
  let testing       = $state(false);
  let testOk        = $state(null);
  let appTimezone   = $state('Europe/Rome');
  let appDateFormat = $state('DD.MM.YYYY');
  // Heimatort (global) — now lives here, not in IntegrationsTab
  let homeLat       = $state('');
  let homeLon       = $state('');
  let homeName      = $state('');

  // ── Integrations tab state ────────────────────────────────────────────────
  let dawarichUrl   = $state('');
  let dawarichToken = $state('');
  let actualUrl     = $state('');
  let actualToken   = $state('');
  let actualFile    = $state('');
  let travelCats    = $state('');

  // ── Notifications tab state ───────────────────────────────────────────────
  let telegramToken = $state('');
  let telegramChat  = $state('');
  let gotifyUrl     = $state('');
  let gotifyToken   = $state('');

  // ── API keys ──────────────────────────────────────────────────────────────
  let serpApiKey = $state('');
  let geminiKey  = $state('');
  let openaiKey  = $state('');

  // ── Providers ─────────────────────────────────────────────────────────────
  let providers        = $state([]);
  let providerKeys     = $state({});
  let providersLoading = $state(false);
  let providersSaving  = $state(false);

  // ── Myspace tab state ──────────────────────────────────────────────────────
  let myDawarichUrl    = $state('');
  let myDawarichToken  = $state('');
  let myActualUrl      = $state('');
  let myActualToken    = $state('');
  let myActualFile     = $state('');
  let myHomeLat        = $state('');
  let myHomeLon        = $state('');
  let myTravelCats     = $state('');
  let myTimezone       = $state('');
  let myDateFormat     = $state('');
  let mySettingsSaving = $state(false);
  let myImmichUrl     = $state('');
  let myImmichKey     = $state('');
  let myImmichGeoSync = $state(false);
  let defAdults   = $state(2);
  let defChildren = $state(0);
  let homeAirport = $state('');
  let lugS10 = $state(0); let lugS20 = $state(0); let lugS23 = $state(0);
  let lugL10 = $state(0); let lugL20 = $state(1); let lugL23 = $state(0);
  let fDepMin = $state(''); let fDepMax = $state('');
  let fArrMin = $state(''); let fArrMax = $state('');
  let travelStyle = $state(''); let climatePref = $state('');
  let landscapePref = $state(''); let companions = $state('');
  let wishText = $state(''); let unsplashKey = $state('');
  let travelMode = $state('flight'); let maxTravelTime = $state('any');
  let historyMode = $state('blacklist');

  // ── Load ──────────────────────────────────────────────────────────────────
  async function loadUserSettings() {
    if (!$apiUrl) return;
    try {
      const us = await api('/api/settings/user');
      myDawarichUrl   = us.dawarich_url        || '';
      myDawarichToken = us.dawarich_token       ? '••••••••' : '';
      myActualUrl     = us.actual_url           || '';
      myActualToken   = us.actual_token         ? '••••••••' : '';
      myActualFile    = us.actual_file          || '';
      myHomeLat       = us.home_lat             || ls('s-homeLat');
      myHomeLon       = us.home_lon             || ls('s-homeLon');
      myTravelCats    = us.travel_categories    || ls('s-travelCategories');
      myTimezone      = us.timezone || '';
      myDateFormat    = us.date_format || '';
      myImmichUrl     = us.immich_url     || '';
      myImmichKey     = us.immich_api_key ? '••••••••' : '';
      myImmichGeoSync = us.immich_geo_sync === 'true' || us.immich_geo_sync === true;
      defAdults   = parseInt(us.ww_adults)   || 2;
      defChildren = parseInt(us.ww_children) || 0;
      homeAirport = us.ww_home_airport || '';
      lugS10 = parseInt(us.ww_lug_s10) || 0; lugS20 = parseInt(us.ww_lug_s20) || 0;
      lugS23 = parseInt(us.ww_lug_s23) || 0; lugL10 = parseInt(us.ww_lug_l10) || 0;
      lugL20 = parseInt(us.ww_lug_l20) || 1; lugL23 = parseInt(us.ww_lug_l23) || 0;
      fDepMin = us.ww_dep_min || ''; fDepMax = us.ww_dep_max || '';
      fArrMin = us.ww_arr_min || ''; fArrMax = us.ww_arr_max || '';
      travelStyle = us.travel_style || ''; climatePref = us.climate_pref || '';
      landscapePref = us.landscape_pref || ''; companions = us.companions || '';
      wishText = us.wish_text || ''; unsplashKey = us.unsplash_key ? '••••••••' : '';
      travelMode = us.travel_mode || 'flight'; maxTravelTime = us.max_travel_time || 'any';
      historyMode = us.history_mode || 'blacklist';
    } catch {}
  }

  async function loadProviders() {
    if (!$apiUrl) return;
    providersLoading = true;
    try {
      const data = await api('/api/settings/providers');
      providers = data || [];
      providerKeys = Object.fromEntries(providers.map(p => [p.name, '']));
    } catch {}
    providersLoading = false;
  }

  $effect(() => {
    if (open) {
      urlInput      = $apiUrl;
      // Credentials werden aus Backend-DB geladen (loadUserSettings)
      // kein localStorage-Fallback für Secrets
      loadUserSettings();
      if ($apiUrl) {
        (async () => {
          try {
            const gs = await api('/api/settings');
            serpApiKey    = gs.serpapi_key          ? '••••••••' : '';
            geminiKey     = gs.gemini_key           ? '••••••••' : '';
            openaiKey     = gs.openai_key           ? '••••••••' : '';
            telegramToken = gs.telegram_bot_token   ? '••••••••' : '';
            telegramChat  = gs.telegram_chat_id     || '';
            gotifyUrl     = gs.gotify_url           || '';
            gotifyToken   = gs.gotify_token         ? '••••••••' : '';
            appTimezone   = gs.timezone             || 'Europe/Rome';
            appDateFormat = gs.date_format          || 'DD.MM.YYYY';
            homeLat       = gs.home_lat             || ls('s-homeLat');
            homeLon       = gs.home_lon             || ls('s-homeLon');
            homeName      = gs.home_name            || ls('s-homeName') || '';
          } catch {}
        })();
      } else {
        // Credentials nur aus Backend-DB — kein localStorage-Fallback
        // Wenn keine API-URL: leere Felder, User muss URL zuerst setzen
        homeLat  = ls('s-homeLat');  // UI-Präferenz, kein Secret
        homeLon  = ls('s-homeLon');
        homeName = ls('s-homeName');
      }
      loadProviders();
    }
  });

  async function testConnection() {
    testing = true; testOk = null;
    testOk = await checkApiStatus(urlInput);
    testing = false;
  }

  async function save() {
    if (!browser) return;
    apiUrl.set(urlInput.trim().replace(/\/$/, ''));
    // Credentials werden ausschließlich an Backend-API gespeichert (Fernet-verschlüsselt).
    // Kein localStorage für Secrets — nur UI-Präferenzen bleiben im Browser.
    localStorage.setItem('ws-date-format',     appDateFormat || 'DD.MM.YYYY');
    localStorage.setItem('ws-timezone',        appTimezone   || 'Europe/Rome');
    if (homeLat)   localStorage.setItem('s-homeLat',   homeLat);
    if (homeLon)   localStorage.setItem('s-homeLon',   homeLon);
    if (homeName)  localStorage.setItem('s-homeName',  homeName);
    if ($apiUrl) {
      try {
        await api('/api/settings', {
          method: 'POST',
          body: JSON.stringify({
            serpapi_key:        (serpApiKey    && serpApiKey    !== '••••••••') ? serpApiKey    : null,
            gemini_key:         (geminiKey     && geminiKey     !== '••••••••') ? geminiKey     : null,
            openai_key:         (openaiKey     && openaiKey     !== '••••••••') ? openaiKey     : null,
            telegram_bot_token: (telegramToken && telegramToken !== '••••••••') ? telegramToken : null,
            telegram_chat_id:   telegramChat  || null,
            gotify_url:         gotifyUrl     || null,
            gotify_token:       (gotifyToken   && gotifyToken   !== '••••••••') ? gotifyToken   : null,
            timezone:           appTimezone   || null,
            date_format:        appDateFormat || null,
            home_lat:           homeLat       || null,
            home_lon:           homeLon       || null,
            home_name:          homeName      || null,
          }),
        });
      } catch {}
    }
    toast($t('toastSaved'), 'success');
    open = false;
  }

  async function saveUserSettings() {
    mySettingsSaving = true;
    try {
      const payload = {};
      if (myDawarichUrl   && myDawarichUrl   !== '••••••••') payload.dawarich_url   = myDawarichUrl;
      if (myDawarichToken && myDawarichToken !== '••••••••') payload.dawarich_token = myDawarichToken;
      if (myActualUrl     && myActualUrl     !== '••••••••') payload.actual_url     = myActualUrl;
      if (myActualToken   && myActualToken   !== '••••••••') payload.actual_token   = myActualToken;
      if (myActualFile)   payload.actual_file       = myActualFile;
      if (myHomeLat)      payload.home_lat          = myHomeLat;
      if (myHomeLon)      payload.home_lon          = myHomeLon;
      if (myTravelCats)   payload.travel_categories = myTravelCats;
      if (myTimezone)     payload.timezone          = myTimezone;
      if (myDateFormat)   payload.date_format       = myDateFormat;
      if (myImmichUrl && myImmichUrl !== '••••••••') payload.immich_url     = myImmichUrl;
      if (myImmichKey && myImmichKey !== '••••••••') payload.immich_api_key = myImmichKey;
      payload.immich_geo_sync = myImmichGeoSync;
      payload.ww_adults = defAdults; payload.ww_children = defChildren;
      payload.ww_home_airport = homeAirport || null;
      payload.ww_lug_s10 = lugS10; payload.ww_lug_s20 = lugS20; payload.ww_lug_s23 = lugS23;
      payload.ww_lug_l10 = lugL10; payload.ww_lug_l20 = lugL20; payload.ww_lug_l23 = lugL23;
      payload.ww_dep_min = fDepMin || null; payload.ww_dep_max = fDepMax || null;
      payload.ww_arr_min = fArrMin || null; payload.ww_arr_max = fArrMax || null;
      if (travelStyle)   payload.travel_style   = travelStyle;
      if (climatePref)   payload.climate_pref   = climatePref;
      if (landscapePref) payload.landscape_pref = landscapePref;
      if (companions)    payload.companions      = companions;
      payload.wish_text = wishText || null;
      if (unsplashKey && unsplashKey !== '••••••••') payload.unsplash_key = unsplashKey;
      payload.travel_mode     = travelMode     || 'flight';
      payload.max_travel_time = maxTravelTime  || 'any';
      payload.history_mode    = historyMode    || 'blacklist';
      // Keine localStorage-Writes für Credentials — nur Backend-DB (Fernet)
      // UI-Präferenzen (date-format, timezone) werden vom Backend zurückgelesen
      await api('/api/settings/user', { method: 'POST', body: JSON.stringify(payload) });
      const apiKeyPayload = {};
      if (serpApiKey && serpApiKey !== '••••••••') apiKeyPayload.serpapi_key = serpApiKey;
      if (openaiKey  && openaiKey  !== '••••••••') apiKeyPayload.openai_key  = openaiKey;
      if (geminiKey  && geminiKey  !== '••••••••') apiKeyPayload.gemini_key  = geminiKey;
      if (Object.keys(apiKeyPayload).length > 0) {
        await api('/api/settings', { method: 'POST', body: JSON.stringify(apiKeyPayload) });
      }
      // Provider-Konfiguration mitspecial speichern (enabled/disabled + Keys)
      if (providers.length > 0) {
        const providerPayload = providers.map(p => ({
          name: p.name, enabled: p.enabled,
          api_key: (providerKeys[p.name] && providerKeys[p.name] !== '••••••••')
                   ? providerKeys[p.name] : null,
          test_mode: p.test_mode,
        }));
        await api('/api/settings/providers', {
          method: 'PUT',
          body: JSON.stringify({ providers: providerPayload }),
        });
        // SerpAPI Key auch in global settings speichern (wird vom Scheduler genutzt)
        const gfKey = providerKeys['google_flights'];
        if (gfKey && gfKey !== '••••••••') {
          await api('/api/settings', {
            method: 'POST',
            body: JSON.stringify({ serpapi_key: gfKey }),
          });
        }
        await loadProviders();
      }
      toast($t('toastSaved'), 'success');
    } catch (e) { toast('Fehler: ' + e.message, 'error'); }
    mySettingsSaving = false;
  }

  async function saveProviders() {
    if (!$apiUrl) { toast('Kein Backend konfiguriert', 'warning'); return; }
    providersSaving = true;
    try {
      const payload = providers.map(p => ({
        name: p.name, enabled: p.enabled,
        api_key: providerKeys[p.name] || null, test_mode: p.test_mode,
      }));
      await api('/api/settings/providers', { method: 'PUT', body: JSON.stringify({ providers: payload }) });
      const gfKey = providerKeys['google_flights'];
      if (gfKey && gfKey !== '••••••••') {
        serpApiKey = gfKey;
        await api('/api/settings', { method: 'POST', body: JSON.stringify({ serpapi_key: gfKey }) });
        // s-serpApiKey nicht in localStorage — Key liegt in Backend-DB
      }
      toast($t('toastSaved'), 'success');
      await loadProviders();
    } catch (e) { toast(e.message, 'error'); }
    providersSaving = false;
  }
</script>

{#if open}
  <div class="fixed inset-0 z-40 bg-black/40" onclick={() => open = false}
    onkeydown={(e) => e.key === 'Escape' && (open = false)}
    role="button" tabindex="-1" aria-label={$t('settingsClose') || 'Schließen'}>
  </div>

  <div class="fixed inset-0 md:inset-[5vh_10vw] md:rounded-2xl z-50 flex flex-col shadow-2xl overflow-hidden"
    style="background:var(--ws-surface)">

    <div class="flex items-center justify-between px-5 py-4 border-b" style="border-color:var(--ws-border)">
      <h2 class="font-semibold text-lg">{$t('settings')}</h2>
      <button onclick={() => open = false} class="p-1.5 rounded-lg hover:opacity-60">✕</button>
    </div>

    <div class="flex border-b px-2 gap-0.5 pt-2 overflow-x-auto shrink-0" style="border-color:var(--ws-border)">
      {#each tabIds as tabId (tabId)}
        <button
          onclick={() => { activeTab = tabId; }}
          class="px-3 py-2 text-xs rounded-t-lg font-medium whitespace-nowrap transition-colors shrink-0"
          style={activeTab === tabId
            ? 'color:var(--ws-accent);border-bottom:2px solid var(--ws-accent)'
            : 'color:var(--ws-muted)'}>
          {tabLabels[tabId] ?? tabId}
        </button>
      {/each}
    </div>

    <div class="flex-1 overflow-y-auto p-5 space-y-4">

      {#if activeTab === 'basic'}
        <BasicTab
          bind:urlInput
          bind:appTimezone
          bind:appDateFormat
          bind:homeLat
          bind:homeLon
          bind:homeName
          {testing}
          {testOk}
          ontestconnection={testConnection}
        />

      {:else if activeTab === 'integrations'}
        <IntegrationsTab
          bind:dawarichUrl bind:dawarichToken
          bind:actualUrl bind:actualToken bind:actualFile bind:travelCats
          {authEnabled}
          onswitchtomyspace={() => activeTab = 'myspace'}
        />

      {:else if activeTab === 'notifications'}
        <NotificationsTab
          bind:telegramToken
          bind:telegramChat
          bind:gotifyUrl
          bind:gotifyToken
        />

      {:else if activeTab === 'myspace'}
        <MyspaceTab
          {authEnabled}
          bind:myDawarichUrl bind:myDawarichToken
          bind:myHomeLat bind:myHomeLon
          bind:myActualUrl bind:myActualToken bind:myActualFile bind:myTravelCats
          bind:myTimezone bind:myDateFormat
          bind:myImmichUrl bind:myImmichKey bind:myImmichGeoSync
          bind:defAdults bind:defChildren bind:homeAirport
          bind:lugS10 bind:lugS20 bind:lugS23
          bind:lugL10 bind:lugL20 bind:lugL23
          bind:fDepMin bind:fDepMax bind:fArrMin bind:fArrMax
          bind:travelStyle bind:climatePref bind:landscapePref
          bind:companions bind:wishText bind:unsplashKey
          bind:travelMode bind:maxTravelTime bind:historyMode
          bind:serpApiKey bind:openaiKey bind:geminiKey
          bind:providers bind:providerKeys
          {providersLoading} {providersSaving} {mySettingsSaving}
          onsave={saveUserSettings}
          onsaveproviders={saveProviders}
          onswitchtointegrations={() => activeTab = 'integrations'}
        />

      {:else if activeTab === 'account'}
        <AccountTab
          userId={$currentUser?.id}
          userEmail={$currentUser?.email}
          userRole={$currentUser?.role}
        />

      {:else if activeTab === 'admin'}
        <AdminTab currentUserId={$currentUser?.id} />

      {:else if activeTab === 'scheduler'}
        <SchedulerTab />

      {/if}
    </div>

    {#if activeTab !== 'account' && activeTab !== 'admin' && activeTab !== 'myspace' && activeTab !== 'scheduler'}
      <div class="p-4 border-t shrink-0" style="border-color:var(--ws-border)">
        <button onclick={save}
          class="w-full py-2.5 rounded-xl text-sm font-semibold transition-opacity hover:opacity-80"
          style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
          {$t('settingsSave')}
        </button>
      </div>
    {/if}

  </div>
{/if}

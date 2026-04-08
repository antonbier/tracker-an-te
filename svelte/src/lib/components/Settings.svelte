<script>
  import { apiUrl, theme, isDark, lang, currentUser, jwtToken, appStatus, isAdmin, logout } from '$lib/stores.js';
  import { toast } from '$lib/toast.js';
  import { t } from '$lib/i18n.js';
  import { checkApiStatus, api } from '$lib/api.js';
  import { browser } from '$app/environment';
  import PasskeyManager from './PasskeyManager.svelte';

  let { open = $bindable(false) } = $props();

  let activeTab = $state('basic');
  let urlInput  = $state('');
  let testing   = $state(false);
  let testOk    = $state(null);

  function ls(key, fallback = '') { return browser ? (localStorage.getItem(key) || fallback) : fallback; }

  let dawarichUrl   = $state('');
  let dawarichToken = $state('');
  let actualUrl     = $state('');
  let actualToken   = $state('');
  let actualFile    = $state('');
  let homeLat       = $state('');
  let homeLon       = $state('');
  let travelCats    = $state('');
  let serpApiKey    = $state('');
  let geminiKey     = $state('');
  let openaiKey     = $state('');
  let telegramToken = $state('');
  let telegramChat  = $state('');
  let gotifyUrl     = $state('');
  let gotifyToken   = $state('');

  // Timezone & date format
  let appTimezone   = $state('Europe/Rome');
  let appDateFormat = $state('DD.MM.YYYY');
  let myTimezone    = $state('');
  let myDateFormat  = $state('');

  // Per-user settings (Dawarich, ActualBudget, Home coords)
  let myDawarichUrl   = $state('');
  let myDawarichToken = $state('');
  let myActualUrl     = $state('');
  let myActualToken   = $state('');
  let myActualFile    = $state('');
  let myHomeLat       = $state('');
  let myHomeLon       = $state('');
  let myTravelCats    = $state('');
  let mySettingsSaving = $state(false);
  let myHomeSearch  = $state('');
  let myGeoLoading  = $state(false);
  let myGeoResult   = $state('');

  async function geocodeHome() {
    const q = myHomeSearch.trim();
    if (!q) return;
    myGeoLoading = true; myGeoResult = '';
    try {
      // Use backend proxy to avoid CORS/HTTPS issues with Nominatim
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

  // Account tab
  let pwCurrent  = $state('');
  let pwNew      = $state('');
  let pwNew2     = $state('');
  let pwLoading  = $state(false);
  let pwError    = $state('');
  let pwOk       = $state(false);

  // Admin tab
  let adminUsers   = $state([]);
  let adminLoading = $state(false);
  let newEmail     = $state('');
  let newPassword  = $state('');
  let newRole      = $state('user');
  let adminError   = $state('');

  // Scheduler tab state
  let schedInterval   = $state(24);
  let schedPriceDrop  = $state(true);
  let schedDaily      = $state(false);
  let schedLastRun    = $state('');
  let schedSaving     = $state(false);
  let schedRunning    = $state(false);

  async function loadSchedulerSettings() {
    if (!$apiUrl) return;
    try {
      const s = await api('/api/scheduler/settings');
      schedInterval  = s.update_interval_hours ?? 24;
      schedPriceDrop = s.notify_price_drop ?? true;
      schedDaily     = s.notify_daily_summary ?? false;
      schedLastRun   = s.last_run_at || '';
    } catch {}
  }

  async function saveSchedulerSettings() {
    schedSaving = true;
    try {
      await api('/api/scheduler/settings', {
        method: 'PUT',
        body: JSON.stringify({
          update_interval_hours: schedInterval,
          notify_price_drop: schedPriceDrop,
          notify_daily_summary: schedDaily,
        })
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

  async function loadUserSettings() {
    if (!$apiUrl) return;
    try {
      const us = await api('/api/settings/user');
      myDawarichUrl   = us.dawarich_url        || ls('s-dawarichUrl');
      myDawarichToken = us.dawarich_token       ? '••••••••' : '';
      myActualUrl     = us.actual_url           || ls('s-actualUrl');
      myActualToken   = us.actual_token         ? '••••••••' : '';
      myActualFile    = us.actual_file          || ls('s-actualFile');
      myHomeLat       = us.home_lat             || ls('s-homeLat');
      myHomeLon       = us.home_lon             || ls('s-homeLon');
      myTravelCats    = us.travel_categories    || ls('s-travelCategories');
      myTimezone      = us.timezone || '';
      myDateFormat    = us.date_format || '';
    } catch {}
  }

  $effect(() => {
    if (open) {
      urlInput      = $apiUrl;
      dawarichUrl   = ls('s-dawarichUrl');
      dawarichToken = ls('s-dawarichToken');
      actualUrl     = ls('s-actualUrl');
      actualToken   = ls('s-actualPassword');
      actualFile    = ls('s-actualFile');
      homeLat       = ls('s-homeLat');
      homeLon       = ls('s-homeLon');
      travelCats    = ls('s-travelCategories');
      // Load per-user settings async (non-blocking)
      loadUserSettings();
      // Load API keys from DB (not localStorage — needed for scheduler)
      if ($apiUrl) {
        try {
          const gs = await api('/api/settings');
          serpApiKey    = gs.serpapi_key    ? '••••••••' : '';
          geminiKey     = gs.gemini_key     ? '••••••••' : '';
          openaiKey     = gs.openai_key     ? '••••••••' : '';
          telegramToken = gs.telegram_bot_token ? '••••••••' : '';
          telegramChat  = gs.telegram_chat_id   || '';
          gotifyUrl     = gs.gotify_url     || '';
          gotifyToken   = gs.gotify_token   ? '••••••••' : '';
          appTimezone   = gs.timezone       || 'Europe/Rome';
          appDateFormat = gs.date_format    || 'DD.MM.YYYY';
        } catch { /* offline */ }
      } else {
        serpApiKey    = ls('s-serpApiKey');
        geminiKey     = ls('s-geminiKey');
        openaiKey     = ls('s-openaiKey');
        telegramToken = ls('s-telegramToken');
        telegramChat  = ls('s-telegramChat');
        gotifyUrl     = ls('s-gotifyUrl');
        gotifyToken   = ls('s-gotifyToken');
      }
      pwCurrent = pwNew = pwNew2 = pwError = '';
      pwOk = false;
      if ($isAdmin && $appStatus?.auth_enabled) loadAdminUsers();
      loadSchedulerSettings();
    }
  });

  // Dynamic tabs:
  // - auth_enabled=true  → "Mein Bereich" statt "Integrationen" (Dawarich/ActualBudget per-user)
  // - auth_enabled=false → "Integrationen" (global, kein User-Kontext nötig)
  const authEnabled = $derived(!!$appStatus?.auth_enabled);
  const tabs = $derived([
    { id: 'basic',         label: $t('settingsBasic') },
    // Integrationen nur wenn auth deaktiviert (single-user mode)
    ...(!authEnabled ? [{ id: 'integrations', label: $t('settingsIntegrations') }] : []),
    { id: 'apis',          label: $t('settingsApis') },
    { id: 'notifications', label: $t('settingsNotifications') },
    // Mein Bereich nur wenn auth aktiviert (pro User konfigurierbar)
    ...(authEnabled ? [{ id: 'myspace', label: $t('settingsMyspace') }] : []),
    ...(authEnabled ? [{ id: 'account', label: $t('settingsAccount') }] : []),
    ...($isAdmin && authEnabled ? [{ id: 'admin', label: $t('settingsAdmin') }] : []),
    { id: 'scheduler', label: '⏰ ' + ($t('settingsScheduler') || 'Scheduler') },
  ]);

  async function testConnection() {
    testing = true; testOk = null;
    testOk = await checkApiStatus(urlInput);
    testing = false;
  }

  async function saveUserSettings() {
    mySettingsSaving = true;
    try {
      const payload = {};
      if (myDawarichUrl && myDawarichUrl !== '••••••••')   payload.dawarich_url   = myDawarichUrl;
      if (myDawarichToken && myDawarichToken !== '••••••••') payload.dawarich_token = myDawarichToken;
      if (myActualUrl && myActualUrl !== '••••••••')         payload.actual_url     = myActualUrl;
      if (myActualToken && myActualToken !== '••••••••')     payload.actual_token   = myActualToken;
      if (myActualFile)   payload.actual_file        = myActualFile;
      if (myHomeLat)      payload.home_lat           = myHomeLat;
      if (myHomeLon)      payload.home_lon           = myHomeLon;
      if (myTravelCats)   payload.travel_categories  = myTravelCats;
      if (myTimezone)     payload.timezone           = myTimezone;
      if (myDateFormat)   payload.date_format        = myDateFormat;
      // Also cache in localStorage as fallback
      if (myDawarichUrl)  localStorage.setItem('s-dawarichUrl',      myDawarichUrl);
      if (myHomeLat)      localStorage.setItem('s-homeLat',          myHomeLat);
      if (myHomeLon)      localStorage.setItem('s-homeLon',          myHomeLon);
      if (myActualFile)   localStorage.setItem('s-actualFile',       myActualFile);
      if (myTravelCats)   localStorage.setItem('s-travelCategories', myTravelCats);
      // Update localStorage for date format if per-user override set
      if (myDateFormat) localStorage.setItem('ws-date-format', myDateFormat);
      await api('/api/settings/user', { method: 'POST', body: JSON.stringify(payload) });
      toast('Mein Bereich gespeichert ✓', 'success');
    } catch(e) { toast('Fehler: ' + e.message, 'error'); }
    mySettingsSaving = false;
  }

  async function save() {
    if (!browser) return;
    apiUrl.set(urlInput.trim().replace(/\/$/, ''));
    localStorage.setItem('s-dawarichUrl',       dawarichUrl);
    localStorage.setItem('s-dawarichToken',     dawarichToken);
    localStorage.setItem('s-actualUrl',         actualUrl);
    localStorage.setItem('s-actualPassword',    actualToken);
    localStorage.setItem('s-actualFile',        actualFile);
    localStorage.setItem('s-homeLat',           homeLat);
    localStorage.setItem('s-homeLon',           homeLon);
    localStorage.setItem('s-travelCategories',  travelCats);
    localStorage.setItem('s-serpApiKey',        serpApiKey);
    localStorage.setItem('s-geminiKey',         geminiKey);
    localStorage.setItem('s-openaiKey',         openaiKey);
    localStorage.setItem('s-telegramToken',     telegramToken);
    localStorage.setItem('s-telegramChat',      telegramChat);
    localStorage.setItem('s-gotifyUrl',         gotifyUrl);
    localStorage.setItem('s-gotifyToken',       gotifyToken);
    if ($apiUrl) {
      try {
        // Persist date format for frontend components
        localStorage.setItem('ws-date-format', appDateFormat || 'DD.MM.YYYY');
        const globalPayload = {
          serpapi_key: (serpApiKey && serpApiKey !== '••••••••') ? serpApiKey : null,
          gemini_key: (geminiKey && geminiKey !== '••••••••') ? geminiKey : null,
          openai_key: (openaiKey && openaiKey !== '••••••••') ? openaiKey : null,
          telegram_bot_token: (telegramToken && telegramToken !== '••••••••') ? telegramToken : null,
          telegram_chat_id: telegramChat||null,
          gotify_url: gotifyUrl||null,
          gotify_token: (gotifyToken && gotifyToken !== '••••••••') ? gotifyToken : null,
          timezone: appTimezone||null,
          date_format: appDateFormat||null,
        };
        await api('/api/settings', { method: 'POST', body: JSON.stringify(globalPayload)});
      } catch { /* offline */ }
    }
    toast('Einstellungen gespeichert ✓', 'success');
    open = false;
  }

  async function changePassword() {
    if (!pwCurrent || !pwNew) { pwError = 'Alle Felder ausfüllen.'; return; }
    if (pwNew.length < 8)     { pwError = 'Neues Passwort mind. 8 Zeichen.'; return; }
    if (pwNew !== pwNew2)     { pwError = 'Passwörter stimmen nicht überein.'; return; }
    pwLoading = true; pwError = ''; pwOk = false;
    try {
      await api('/api/auth/change-password', {
        method: 'POST',
        body: JSON.stringify({ current_password: pwCurrent, new_password: pwNew }),
      });
      pwOk = true;
      pwCurrent = pwNew = pwNew2 = '';
      toast('Passwort geändert ✓', 'success');
    } catch (e) {
      pwError = e.message.includes('401') ? 'Aktuelles Passwort falsch.' : e.message;
    }
    pwLoading = false;
  }

  async function loadAdminUsers() {
    adminLoading = true;
    try { adminUsers = await api('/api/admin/users'); }
    catch { adminUsers = []; }
    adminLoading = false;
  }

  async function createUser() {
    if (!newEmail || !newPassword) { adminError = 'E-Mail und Passwort eingeben.'; return; }
    adminError = '';
    try {
      await api('/api/admin/users', {
        method: 'POST',
        body: JSON.stringify({ email: newEmail, password: newPassword, role: newRole }),
      });
      newEmail = newPassword = ''; newRole = 'user';
      toast('User erstellt ✓', 'success');
      await loadAdminUsers();
    } catch (e) { adminError = e.message; }
  }

  async function deleteUser(id, email) {
    if (!confirm(`User ${email} löschen?`)) return;
    try {
      await api(`/api/admin/users/${id}`, { method: 'DELETE' });
      toast('User gelöscht', 'success');
      await loadAdminUsers();
    } catch (e) { toast(e.message, 'error'); }
  }
</script>

{#if open}
  <div class="fixed inset-0 z-40 bg-black/40" onclick={() => open = false}
    onkeydown={(e) => e.key === 'Escape' && (open = false)}
    role="button" tabindex="-1" aria-label="Schließen">
  </div>

  <div class="fixed inset-0 md:inset-[5vh_auto] md:left-1/2 md:-translate-x-1/2 md:w-full md:max-w-2xl md:max-h-[90vh] md:rounded-2xl z-50 flex flex-col shadow-2xl overflow-hidden"
    style="background:var(--ws-surface)">

    <div class="flex items-center justify-between px-5 py-4 border-b" style="border-color:var(--ws-border)">
      <h2 class="font-semibold text-lg">{$t('settings')}</h2>
      <button onclick={() => open = false} class="p-1.5 rounded-lg hover:opacity-60">✕</button>
    </div>

    <div class="flex border-b px-2 gap-0.5 pt-2 overflow-x-auto shrink-0" style="border-color:var(--ws-border)">
      {#each tabs as tab}
        <button onclick={() => activeTab = tab.id}
          class="px-3 py-2 text-xs rounded-t-lg font-medium whitespace-nowrap transition-colors shrink-0"
          style={activeTab === tab.id
            ? 'color:var(--ws-accent);border-bottom:2px solid var(--ws-accent)'
            : 'color:var(--ws-muted)'}>
          {tab.label}
        </button>
      {/each}
    </div>

    <div class="flex-1 overflow-y-auto p-5 space-y-4">

      {#if activeTab === 'basic'}
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

        <!-- Timezone & Date Format -->
        <div>
          <label class="text-xs font-bold uppercase tracking-wider block mb-2" style="color:var(--ws-muted)">🌍 {$t('settingsTimezone') || 'Zeitzone'}</label>
          <select bind:value={appTimezone}
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)">
            {#each ['Europe/Rome','Europe/Berlin','Europe/Vienna','Europe/Zurich','Europe/London','Europe/Paris','America/New_York','America/Chicago','America/Los_Angeles','Asia/Tokyo','Asia/Singapore','Australia/Sydney','UTC'] as tz}
              <option value={tz}>{tz}</option>
            {/each}
          </select>
        </div>
        <div>
          <label class="text-xs font-bold uppercase tracking-wider block mb-2" style="color:var(--ws-muted)">📅 {$t('settingsDateFormat') || 'Datumsformat'}</label>
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

      {:else if activeTab === 'integrations'}
        {#if $appStatus?.auth_enabled}
          <!-- Auth aktiv: Benutzer soll "Mein Bereich" verwenden -->
          <div class="rounded-xl p-4 border" style="background:rgba(196,98,45,.06);border-color:var(--ws-border)">
            <div class="text-sm font-semibold mb-1" style="color:var(--ws-accent)">🔐 Auth ist aktiv</div>
            <p class="text-xs" style="color:var(--ws-muted)">
              Da die Authentifizierung aktiviert ist, werden Dawarich und ActualBudget
              pro Benutzer konfiguriert. Bitte wechsle in den Tab
              <button onclick={() => activeTab='myspace'} class="underline font-semibold" style="color:var(--ws-accent)">🏠 Mein Bereich</button>
              um deine persönlichen Integrationen einzustellen.
            </p>
            <p class="text-xs mt-2" style="color:var(--ws-muted)">
              Die globalen Integrationsfelder hier gelten als Fallback für alle Benutzer ohne eigene Konfiguration.
            </p>
          </div>
          <hr style="border-color:var(--ws-border)"/>
        {/if}
        <div class="space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Dawarich</div>
          <input bind:value={dawarichUrl} placeholder="https://dawarich.example.com"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <input bind:value={dawarichToken} type="password" placeholder="API Token"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <div class="grid grid-cols-2 gap-2">
            <input bind:value={homeLat} placeholder="Lat: 46.7987" class="px-3 py-2 rounded-xl border text-sm"
              style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
            <input bind:value={homeLon} placeholder="Lon: 11.7188" class="px-3 py-2 rounded-xl border text-sm"
              style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          </div>
          <div class="text-xs" style="color:var(--ws-muted)">{$t('settingsHomeCoordsHint')}</div>
        </div>
        <hr style="border-color:var(--ws-border)"/>
        <div class="space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">ActualBudget</div>
          <input bind:value={actualUrl} placeholder="https://actual.example.com"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <input bind:value={actualToken} type="password" placeholder="Server Password"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <input bind:value={actualFile} placeholder="Budget-Dateiname (z.B. My-Finances-abc123)"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <div class="text-xs" style="color:var(--ws-muted)">💡 Dateiname: ActualBudget → Budget-Name oben links anklicken → ID aus der URL entnehmen</div>
          <input bind:value={travelCats} placeholder="Kategorien: Holiday, Flights, Hotel"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
        </div>

      {:else if activeTab === 'apis'}
        <div class="space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">SerpAPI</div>
          <input bind:value={serpApiKey} type="password" placeholder="API Key"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <div class="text-xs" style="color:var(--ws-muted)">Für Google Flights + Booking</div>
        </div>
        <hr style="border-color:var(--ws-border)"/>
        <div class="space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Google Gemini</div>
          <input bind:value={geminiKey} type="password" placeholder="AIzaSy…"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
        </div>
        <hr style="border-color:var(--ws-border)"/>
        <div class="space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">OpenAI</div>
          <input bind:value={openaiKey} type="password" placeholder="sk-…"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
        </div>

      {:else if activeTab === 'notifications'}
        <div class="space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Telegram</div>
          <input bind:value={telegramToken} type="password" placeholder="Bot Token"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <input bind:value={telegramChat} placeholder="Chat ID"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
        </div>
        <hr style="border-color:var(--ws-border)"/>
        <div class="space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Gotify</div>
          <input bind:value={gotifyUrl} placeholder="https://gotify.example.com"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <input bind:value={gotifyToken} type="password" placeholder="App Token"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
        </div>

      {:else if activeTab === 'myspace'}
        {#if !$appStatus?.auth_enabled}
          <!-- Auth deaktiviert: globale Integrationen werden genutzt -->
          <div class="rounded-xl p-4 border" style="background:rgba(42,92,69,.06);border-color:var(--ws-border)">
            <div class="text-sm font-semibold mb-1" style="color:var(--ws-green)">ℹ️ Auth ist deaktiviert</div>
            <p class="text-xs" style="color:var(--ws-muted)">
              Die Einstellungen hier gelten nur wenn Authentifizierung aktiv ist.
              Im Gast-Modus werden die globalen Werte aus dem Tab
              <button onclick={() => activeTab='integrations'} class="underline font-semibold" style="color:var(--ws-accent)">🔗 Integrationen</button>
              verwendet.
            </p>
          </div>
          <hr style="border-color:var(--ws-border)"/>
        {/if}
        <!-- Per-user settings: Dawarich + ActualBudget + Home coords -->
        <div class="space-y-2">
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
        <!-- Save button inline for myspace tab -->
        <button onclick={saveUserSettings} disabled={mySettingsSaving}
          class="w-full py-2.5 rounded-xl text-sm font-semibold transition-opacity hover:opacity-80 disabled:opacity-50"
          style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
          {mySettingsSaving ? '⏳ Speichern…' : '💾 ' + $t('settingsSave')}
        </button>

      {:else if activeTab === 'account'}
        <div class="space-y-1 mb-4">
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('settingsLoggedInAs')}</div>
          <div class="px-3 py-2 rounded-xl text-sm font-medium" style="background:var(--ws-surface2);color:var(--ws-text)">
            {$currentUser?.email} <span class="text-xs ml-1" style="color:var(--ws-muted)">({$currentUser?.role})</span>
          </div>
        </div>
        <hr style="border-color:var(--ws-border)"/>
        <div class="space-y-3">
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('settingsChangePassword')}</div>
          <input type="password" bind:value={pwCurrent} placeholder="Aktuelles Passwort"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <input type="password" bind:value={pwNew} placeholder="Neues Passwort (mind. 8)"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <input type="password" bind:value={pwNew2} placeholder="Bestätigen"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          {#if pwError}
            <p class="text-xs px-3 py-2 rounded-lg" style="background:rgba(220,38,38,.1);color:#dc2626">{pwError}</p>
          {/if}
          {#if pwOk}
            <p class="text-xs px-3 py-2 rounded-lg" style="background:rgba(42,92,69,.1);color:var(--ws-green)">✓ Passwort geändert</p>
          {/if}
          <button onclick={changePassword} disabled={pwLoading}
            class="w-full py-2.5 rounded-xl text-sm font-semibold border transition-opacity disabled:opacity-50"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)">
            {pwLoading ? '⏳…' : $t('settingsChangePasswordBtn')}
          </button>
        </div>

      <!-- Passkeys -->
      <hr style="border-color:var(--ws-border)"/>
      <PasskeyManager userId={$currentUser?.id} />

      {:else if activeTab === 'admin'}
        <!-- User list -->
        <div class="space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('settingsUsers')}</div>
          {#if adminLoading}
            <p class="text-xs" style="color:var(--ws-muted)">Lade…</p>
          {:else}
            {#each adminUsers as u}
              <div class="flex items-center gap-2 px-3 py-2 rounded-xl border text-sm"
                style="background:var(--ws-surface2);border-color:var(--ws-border)">
                <span class="flex-1 truncate" style="color:var(--ws-text)">{u.email}</span>
                <span class="text-xs px-2 py-0.5 rounded-full"
                  style="background:{u.role==='admin'?'rgba(196,98,45,.15)':'rgba(42,92,69,.1)'};color:{u.role==='admin'?'var(--ws-accent)':'var(--ws-green)'}">
                  {u.role}
                </span>
                {#if u.id !== $currentUser?.id}
                  <button onclick={() => deleteUser(u.id, u.email)}
                    class="text-xs px-2 py-0.5 rounded-lg border"
                    style="border-color:var(--ws-border);color:var(--ws-muted)">✕</button>
                {/if}
              </div>
            {/each}
          {/if}
        </div>
        <hr style="border-color:var(--ws-border)"/>
        <!-- Create user -->
        <div class="space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('settingsCreateUser')}</div>
          <input bind:value={newEmail} type="email" placeholder="E-Mail"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <input bind:value={newPassword} type="password" placeholder="Passwort (mind. 8)"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <div class="flex gap-2">
            {#each ['user','admin'] as r}
              <button onclick={() => newRole = r}
                class="flex-1 py-1.5 rounded-xl text-xs border font-medium transition-all"
                style={newRole === r
                  ? 'background:var(--ws-accent);color:#fff;border-color:var(--ws-accent)'
                  : 'background:var(--ws-surface2);color:var(--ws-muted);border-color:var(--ws-border)'}>
                {r}
              </button>
            {/each}
          </div>
          {#if adminError}
            <p class="text-xs px-3 py-2 rounded-lg" style="background:rgba(220,38,38,.1);color:#dc2626">{adminError}</p>
          {/if}
          <button onclick={createUser}
            class="w-full py-2.5 rounded-xl text-sm font-semibold transition-opacity hover:opacity-80"
            style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
            {$t('settingsCreateUserBtn')}
          </button>
        </div>
      {:else if activeTab === 'scheduler'}
        <!-- ── Scheduler Tab ── -->
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
              Letzter Lauf: {schedLastRun.slice(0,16).replace('T',' ')} UTC
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

      {/if}

    </div>

    <!-- Footer: Speichern-Button (nur für Basic / Integrationen / APIs / Notifications) -->
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

<script>
  import { apiUrl, theme, isDark, lang, currentUser, jwtToken, appStatus, isAdmin, logout } from '$lib/stores.js';
  import { toast } from '$lib/toast.js';
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
      serpApiKey    = ls('s-serpApiKey');
      geminiKey     = ls('s-geminiKey');
      openaiKey     = ls('s-openaiKey');
      telegramToken = ls('s-telegramToken');
      telegramChat  = ls('s-telegramChat');
      gotifyUrl     = ls('s-gotifyUrl');
      gotifyToken   = ls('s-gotifyToken');
      pwCurrent = pwNew = pwNew2 = pwError = '';
      pwOk = false;
      if ($isAdmin && $appStatus?.auth_enabled) loadAdminUsers();
    }
  });

  // Dynamic tabs — show account/admin only when auth is enabled
  const tabs = $derived([
    { id: 'basic',         label: '⚙️ Allgemein' },
    { id: 'integrations',  label: '🔗 Integrationen' },
    { id: 'apis',          label: '🤖 APIs & KI' },
    { id: 'notifications', label: '🔔 Alerts' },
    { id: 'myspace',       label: '🏠 Mein Bereich' },
    ...($appStatus?.auth_enabled ? [{ id: 'account', label: '👤 Account' }] : []),
    ...($isAdmin && $appStatus?.auth_enabled ? [{ id: 'admin', label: '🛡️ Admin' }] : []),
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
      // Also cache in localStorage as fallback
      if (myDawarichUrl)  localStorage.setItem('s-dawarichUrl',      myDawarichUrl);
      if (myHomeLat)      localStorage.setItem('s-homeLat',          myHomeLat);
      if (myHomeLon)      localStorage.setItem('s-homeLon',          myHomeLon);
      if (myActualFile)   localStorage.setItem('s-actualFile',       myActualFile);
      if (myTravelCats)   localStorage.setItem('s-travelCategories', myTravelCats);
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
        await api('/api/settings', { method: 'POST', body: JSON.stringify({
          serpapi_key: serpApiKey||null, gemini_key: geminiKey||null, openai_key: openaiKey||null,
          dawarich_url: dawarichUrl||null, dawarich_token: dawarichToken||null,
          actual_url: actualUrl||null, actual_token: actualToken||null,
          home_lat: homeLat||null, home_lon: homeLon||null,
          travel_categories: travelCats||null,
          telegram_bot_token: telegramToken||null, telegram_chat_id: telegramChat||null,
          gotify_url: gotifyUrl||null, gotify_token: gotifyToken||null,
        })});
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

  <div class="fixed inset-y-0 right-0 z-50 w-full max-w-md flex flex-col shadow-2xl"
    style="background:var(--ws-surface)">

    <div class="flex items-center justify-between px-5 py-4 border-b" style="border-color:var(--ws-border)">
      <h2 class="font-semibold text-lg">Einstellungen</h2>
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
          <label class="text-xs font-bold uppercase tracking-wider block mb-1" style="color:var(--ws-muted)">Backend URL</label>
          <input type="url" bind:value={urlInput} placeholder="http://192.168.1.51:8765"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <div class="flex items-center gap-2 mt-2">
            <button onclick={testConnection} disabled={testing}
              class="px-4 py-1.5 rounded-xl text-xs border transition-opacity hover:opacity-70 disabled:opacity-40"
              style="border-color:var(--ws-border);color:var(--ws-muted)">
              {testing ? '⏳ Testen…' : '🔗 Verbinden'}
            </button>
            {#if testOk === true}
              <span class="text-xs font-medium" style="color:var(--ws-green)">✓ Verbunden</span>
            {:else if testOk === false}
              <span class="text-xs font-medium" style="color:#dc2626">✗ Nicht erreichbar</span>
            {/if}
          </div>
        </div>
        <div>
          <label class="text-xs font-bold uppercase tracking-wider block mb-2" style="color:var(--ws-muted)">Darstellung</label>
          <div class="flex gap-2">
            {#each [{ val: '', label: '☀️ Hell' }, { val: 'dark', label: '🌙 Dunkel' }] as opt}
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

      {:else if activeTab === 'integrations'}
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
          <div class="text-xs" style="color:var(--ws-muted)">Home-Koordinaten für Trip-Erkennung (>50km)</div>
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
          <input bind:value={actualFile} placeholder="Budget-Dateiname"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
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
        <!-- Per-user settings: Dawarich + ActualBudget + Home coords -->
        <div class="space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">🧭 Dawarich</div>
          <input bind:value={myDawarichUrl} placeholder="https://dawarich.example.com"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <input bind:value={myDawarichToken} type="password" placeholder="API Token"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <div class="grid grid-cols-2 gap-2">
            <input bind:value={myHomeLat} placeholder="Lat: 46.7987" class="px-3 py-2 rounded-xl border text-sm"
              style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
            <input bind:value={myHomeLon} placeholder="Lon: 11.7188" class="px-3 py-2 rounded-xl border text-sm"
              style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          </div>
          <div class="text-xs" style="color:var(--ws-muted)">Home-Koordinaten für Trip-Erkennung (>50km)</div>
        </div>
        <hr style="border-color:var(--ws-border)"/>
        <div class="space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">💶 ActualBudget</div>
          <input bind:value={myActualUrl} placeholder="https://actual.example.com"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <input bind:value={myActualToken} type="password" placeholder="Server Password"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <input bind:value={myActualFile} placeholder="Budget-Dateiname"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <input bind:value={myTravelCats} placeholder="Kategorien: Holiday, Flights, Hotel"
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
        </div>
        <!-- Save button inline for myspace tab -->
        <button onclick={saveUserSettings} disabled={mySettingsSaving}
          class="w-full py-2.5 rounded-xl text-sm font-semibold transition-opacity hover:opacity-80 disabled:opacity-50"
          style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
          {mySettingsSaving ? '⏳ Speichern…' : '💾 Mein Bereich speichern'}
        </button>

      {:else if activeTab === 'account'}
        <div class="space-y-1 mb-4">
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Angemeldet als</div>
          <div class="px-3 py-2 rounded-xl text-sm font-medium" style="background:var(--ws-surface2);color:var(--ws-text)">
            {$currentUser?.email} <span class="text-xs ml-1" style="color:var(--ws-muted)">({$currentUser?.role})</span>
          </div>
        </div>
        <hr style="border-color:var(--ws-border)"/>
        <div class="space-y-3">
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Passwort ändern</div>
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
            {pwLoading ? '⏳…' : '🔑 Passwort ändern'}
          </button>
        </div>

      <!-- Passkeys -->
      <hr style="border-color:var(--ws-border)"/>
      <PasskeyManager userId={$currentUser?.id} />

      {:else if activeTab === 'admin'}
        <!-- User list -->
        <div class="space-y-2">
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Benutzer</div>
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
          <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Neuen User erstellen</div>
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
            + User erstellen
          </button>
        </div>
      {/if}

    </div>

    <!-- Save button — only for non-auth tabs -->
    {#if activeTab !== 'account' && activeTab !== 'admin' && activeTab !== 'myspace'}
      <div class="p-4 border-t shrink-0" style="border-color:var(--ws-border)">
        <button onclick={save}
          class="w-full py-2.5 rounded-xl text-sm font-semibold transition-opacity hover:opacity-80"
          style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
          Speichern
        </button>
      </div>
    {/if}

  </div>
{/if}

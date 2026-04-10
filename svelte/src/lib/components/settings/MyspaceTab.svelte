<script>
  import { appStatus } from '$lib/stores.js';
  import { t } from '$lib/i18n.js';
  import MyspaceConnections from './MyspaceConnections.svelte';
  import MyspaceProviders   from './MyspaceProviders.svelte';
  import MyspaceAI          from './MyspaceAI.svelte';
  import MyspaceDefaults    from './MyspaceDefaults.svelte';

  let {
    authEnabled,
    myDawarichUrl   = $bindable(),
    myDawarichToken = $bindable(),
    myHomeLat       = $bindable(),
    myHomeLon       = $bindable(),
    myActualUrl     = $bindable(),
    myActualToken   = $bindable(),
    myActualFile    = $bindable(),
    myTravelCats    = $bindable(),
    myTimezone      = $bindable(),
    myDateFormat    = $bindable(),
    myImmichUrl     = $bindable(),
    myImmichKey     = $bindable(),
    myImmichGeoSync = $bindable(),
    defAdults       = $bindable(),
    defChildren     = $bindable(),
    homeAirport     = $bindable(),
    lugS10          = $bindable(),
    lugS20          = $bindable(),
    lugS23          = $bindable(),
    lugL10          = $bindable(),
    lugL20          = $bindable(),
    lugL23          = $bindable(),
    fDepMin         = $bindable(),
    fDepMax         = $bindable(),
    fArrMin         = $bindable(),
    fArrMax         = $bindable(),
    travelStyle     = $bindable(),
    climatePref     = $bindable(),
    landscapePref   = $bindable(),
    companions      = $bindable(),
    wishText        = $bindable(),
    unsplashKey     = $bindable(),
    serpApiKey      = $bindable(),
    openaiKey       = $bindable(),
    geminiKey       = $bindable(),
    providers       = $bindable(),
    providerKeys    = $bindable(),
    providersLoading,
    providersSaving,
    mySettingsSaving,
    onsave,
    onsaveproviders,
    onswitchtointegrations,
  } = $props();

  let myspaceTab   = $state('connections');
  let myHomeSearch = $state('');
</script>

{#if !$appStatus?.auth_enabled}
  <div class="rounded-xl p-4 border" style="background:rgba(42,92,69,.06);border-color:var(--ws-border)">
    <div class="text-sm font-semibold mb-1" style="color:var(--ws-green)">ℹ️ Auth ist deaktiviert</div>
    <p class="text-xs" style="color:var(--ws-muted)">
      Die Einstellungen hier gelten nur wenn Authentifizierung aktiv ist.
      Im Gast-Modus werden die globalen Werte aus dem Tab
      <button onclick={onswitchtointegrations} class="underline font-semibold" style="color:var(--ws-accent)">🔗 Integrationen</button>
      verwendet.
    </p>
  </div>
  <hr style="border-color:var(--ws-border)"/>
{/if}

<!-- Sub-Tab-Navigation -->
<div class="flex gap-1 p-1 rounded-xl overflow-x-auto" style="background:var(--ws-surface2)">
  {#each [
    { id: 'connections',  icon: '🔌', label: 'Anbindungen' },
    { id: 'defaults',     icon: '🧳', label: 'Reise-Defaults' },
    { id: 'integrations', icon: '🔍', label: 'Such-Engines' },
    { id: 'ai',           icon: '✨', label: 'KI' },
  ] as st}
    <button onclick={() => myspaceTab = st.id}
      class="flex-1 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap shrink-0"
      style={myspaceTab === st.id
        ? 'background:var(--ws-accent);color:#fff5ec'
        : 'color:var(--ws-muted)'}>
      {st.icon} {st.label}
    </button>
  {/each}
</div>

<!-- Sub-Tab-Inhalte -->
{#if myspaceTab === 'connections'}
  <MyspaceConnections
    bind:myDawarichUrl bind:myDawarichToken
    bind:myHomeLat bind:myHomeLon bind:myHomeSearch
    bind:myActualUrl bind:myActualToken bind:myActualFile bind:myTravelCats
    bind:myImmichUrl bind:myImmichKey bind:myImmichGeoSync
    bind:unsplashKey
  />

{:else if myspaceTab === 'defaults'}
  <MyspaceDefaults
    bind:defAdults bind:defChildren bind:homeAirport
    bind:lugS10 bind:lugS20 bind:lugS23
    bind:lugL10 bind:lugL20 bind:lugL23
    bind:fDepMin bind:fDepMax bind:fArrMin bind:fArrMax
    bind:travelStyle bind:climatePref bind:landscapePref
    bind:companions bind:wishText
  />

{:else if myspaceTab === 'integrations'}
  <MyspaceProviders
    bind:providers bind:providerKeys
    {providersLoading} {providersSaving}
    onsave={onsaveproviders}
  />

{:else if myspaceTab === 'ai'}
  <MyspaceAI bind:openaiKey bind:geminiKey />
{/if}

<!-- Save button -->
<button onclick={onsave} disabled={mySettingsSaving}
  class="w-full py-2.5 rounded-xl text-sm font-semibold transition-opacity hover:opacity-80 disabled:opacity-50 mt-2"
  style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
  {mySettingsSaving ? '⏳ Speichern…' : '💾 ' + $t('settingsSave')}
</button>

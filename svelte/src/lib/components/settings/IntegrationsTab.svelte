<script>
  import { t } from '$lib/i18n.js';

  let {
    dawarichUrl   = $bindable(),
    dawarichToken = $bindable(),
    homeLat       = $bindable(),
    homeLon       = $bindable(),
    actualUrl     = $bindable(),
    actualToken   = $bindable(),
    actualFile    = $bindable(),
    travelCats    = $bindable(),
    authEnabled,
    onswitchtomyspace,
  } = $props();
</script>

{#if authEnabled}
  <div class="rounded-xl p-4 border" style="background:rgba(196,98,45,.06);border-color:var(--ws-border)">
    <div class="text-sm font-semibold mb-1" style="color:var(--ws-accent)">🔐 Auth ist aktiv</div>
    <p class="text-xs" style="color:var(--ws-muted)">
      Da die Authentifizierung aktiviert ist, werden Dawarich und ActualBudget
      pro Benutzer konfiguriert. Bitte wechsle in den Tab
      <button onclick={onswitchtomyspace} class="underline font-semibold" style="color:var(--ws-accent)">🏠 Mein Bereich</button>
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

<script>
  import { t } from '$lib/i18n.js';

  let {
    dawarichUrl   = $bindable(),
    dawarichToken = $bindable(),
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
    <div class="text-sm font-semibold mb-1" style="color:var(--ws-accent)">🔐 {$t('integrationsAuthActive')}</div>
    <p class="text-xs" style="color:var(--ws-muted)">
      {$t('integrationsAuthDesc')}
      <button onclick={onswitchtomyspace} class="underline font-semibold" style="color:var(--ws-accent)">{$t('settingsMyspace')}</button>
      {$t('integrationsAuthDesc2')}
    </p>
    <p class="text-xs mt-2" style="color:var(--ws-muted)">
      {$t('integrationsAuthFallback')}
    </p>
  </div>
  <hr style="border-color:var(--ws-border)"/>
{/if}

<!-- Dawarich -->
<div class="space-y-2">
  <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Dawarich</div>
  <div class="text-xs rounded-lg px-3 py-2" style="background:rgba(var(--ws-accent-rgb,211,95,57),.06);color:var(--ws-muted)">
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

<!-- ActualBudget -->
<div class="space-y-2">
  <div class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">ActualBudget</div>
  <div class="text-xs rounded-lg px-3 py-2" style="background:rgba(var(--ws-accent-rgb,211,95,57),.06);color:var(--ws-muted)">
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

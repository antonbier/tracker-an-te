<script>
  import { theme } from '$lib/stores.js';
  import { t } from '$lib/i18n.js';

  let {
    urlInput      = $bindable(),
    appTimezone   = $bindable(),
    appDateFormat = $bindable(),
    testing,
    testOk,
    ontestconnection,
  } = $props();
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
  <label class="text-xs font-bold uppercase tracking-wider block mb-2" style="color:var(--ws-muted)">🌍 {$t('settingsTimezone') || 'Zeitzone'}</label>
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

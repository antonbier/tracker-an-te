<script>
  import { t } from '$lib/i18n.js';

  let { activeCategory = $bindable(), oncategorychange } = $props();
</script>

<div class="flex border-b overflow-x-auto" style="border-color:var(--ws-border)">
  {#each [
    { id: 'flights', icon: '✈️', label: $t('radarFlights') },
    { id: 'hotels',  icon: '🏨', label: $t('radarHotels') },
    { id: 'camping', icon: '⛺', label: $t('radarCamping') },
    { id: 'rentals', icon: '🚗', label: $t('radarRentals') },
  ] as tab}
    <button
      onclick={() => { activeCategory = tab.id; oncategorychange?.(tab.id); }}
      class="px-4 py-2.5 text-xs font-semibold whitespace-nowrap shrink-0 transition-colors border-b-2"
      style={activeCategory === tab.id
        ? 'border-color:var(--ws-accent);color:var(--ws-accent)'
        : 'border-color:transparent;color:var(--ws-muted)'}>
      {tab.icon} {tab.label}
    </button>
  {/each}
</div>

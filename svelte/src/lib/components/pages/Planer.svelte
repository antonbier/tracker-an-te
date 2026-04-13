<script>
  /**
   * Planer.svelte — Reiseplaner als Full-Page (Route: 'planer')
   * Rendert den WanderWizzard dauerhaft offen als eigenständige Seite.
   */
  import { onMount } from 'svelte';
  import { t } from '$lib/i18n.js';
  import { api } from '$lib/api.js';
  import { apiUrl } from '$lib/stores.js';
  import WanderWizzard from '$lib/components/WanderWizzard.svelte';

  // WanderWizzard defaults from user settings
  let wwAdults      = $state(2);
  let wwChildren    = $state(0);
  let wwHomeAirport = $state('');
  let wwBudget      = $state(0);

  let open = $state(true);  // always open on this page

  // Re-open if user somehow closes (shouldn't happen but safety net)
  $effect(() => { if (!open) open = true; });

  onMount(async () => {
    if (!$apiUrl) return;
    try {
      const us = await api('/api/settings/user');
      wwAdults      = parseInt(us.ww_adults)       || 2;
      wwChildren    = parseInt(us.ww_children)     || 0;
      wwHomeAirport = us.ww_home_airport            || '';
    } catch {}
  });
</script>

<!--
  Full-page wrapper: centers the WanderWizzard modal visually
  but it's actually rendered inline as the page content.
-->
<div class="min-h-[80vh] flex items-start justify-center pt-4">
  <WanderWizzard
    bind:open
    adults={wwAdults}
    children={wwChildren}
    homeAirport={wwHomeAirport}
    budget={wwBudget}
  />
</div>

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

  let wwAdults      = $state(2);
  let wwChildren    = $state(0);
  let wwHomeAirport = $state('');
  let wwBudget      = $state(0);

  // Always reset to open when this page mounts/remounts
  let open = $state(true);

  // If WanderWizzard closes itself (after trip creation), reset it
  // so the planer page is always usable on re-navigation
  $effect(() => {
    if (!open) {
      // small delay so TripHub navigation can happen first
      setTimeout(() => { open = true; }, 50);
    }
  });

  onMount(async () => {
    open = true; // ensure open on mount
    if (!$apiUrl) return;
    try {
      const us = await api('/api/settings/user');
      wwAdults      = parseInt(us.ww_adults)   || 2;
      wwChildren    = parseInt(us.ww_children) || 0;
      wwHomeAirport = us.ww_home_airport        || '';
    } catch {}
  });
</script>

<div class="min-h-[80vh] flex items-start justify-center pt-4">
  <WanderWizzard
    bind:open
    embedded={true}
    adults={wwAdults}
    children={wwChildren}
    homeAirport={wwHomeAirport}
    budget={wwBudget}
  />
</div>

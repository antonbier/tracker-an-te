<script>
  import { currentPage } from '$lib/stores.js';
  import Dashboard  from '$lib/components/pages/Dashboard.svelte';
  import PriceRadar from '$lib/components/pages/PriceRadar.svelte';
  import MyTrips    from '$lib/components/pages/MyTrips.svelte';
  import Discover   from '$lib/components/pages/Discover.svelte';
  import TripHub    from '$lib/components/pages/TripHub.svelte';
  import Planer     from '$lib/components/pages/Planer.svelte';
</script>

{#if $currentPage === 'home'}
  <Dashboard />
{:else if $currentPage === 'priceradar'}
  <PriceRadar />
{:else if $currentPage === 'mytrips'}
  <MyTrips />
{:else if $currentPage === 'discover'}
  <Discover />
{:else if $currentPage === 'triphub'}
  <TripHub />
{:else if $currentPage === 'planer'}
  <Planer />
{/if}

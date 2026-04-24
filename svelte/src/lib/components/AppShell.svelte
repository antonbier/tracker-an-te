<script>
  import { currentPage, isDark, theme, settingsOpen, wizardOpen, apiUrl, jwtToken } from '$lib/stores.js';
  import { getTripPhase } from '$lib/utils.js';
  import { api }          from '$lib/api.js';
  import Header      from './Header.svelte';
  import Sidebar     from './Sidebar.svelte';
  import BottomNav   from './BottomNav.svelte';
  import FieldGuide  from './FieldGuide.svelte';
  import Settings    from './Settings.svelte';
  import SetupWizard from './SetupWizard.svelte';

  let { children } = $props();

  let fieldGuideOpen = $state(false);
  let _settingsOpen  = $state(false);
  let _wizardOpen    = $state(false);

  // Sync global stores → local state
  $effect(() => { if ($settingsOpen) { _settingsOpen = true; settingsOpen.set(false); } });
  $effect(() => { if ($wizardOpen)   { _wizardOpen   = true; wizardOpen.set(false);   } });

  function toggleDark() {
    theme.set($isDark ? '' : 'dark');
  }

  // ── OnTour-Badge: aktive Reisen zählen ───────────────────────────────────
  let _wsTrips = $state([]);
  const activeTripsCount = $derived(
    _wsTrips.filter(t => getTripPhase(t) === 'active').length
  );

  $effect(() => {
    if ($apiUrl && $jwtToken) {
      api('/api/ws-trips').then(r => { _wsTrips = r || []; }).catch(() => {});
    }
  });
</script>

<div class="flex h-screen overflow-hidden" style="background:var(--ws-bg);color:var(--ws-text)">
  <Sidebar onSettings={() => _settingsOpen = true} />
  <div class="flex flex-col flex-1 min-w-0 overflow-hidden">
    <Header
      onFieldGuide={() => fieldGuideOpen = true}
      onSettings={() => _settingsOpen = true}
      onWizard={() => _wizardOpen = true}
      onToggleDark={toggleDark}
    />
    <main class="flex-1 overflow-y-auto p-4 md:p-6">
      {@render children()}
    </main>
    <BottomNav onSettings={() => _settingsOpen = true} {activeTripsCount} />
  </div>
</div>

<FieldGuide bind:open={fieldGuideOpen} />
<Settings   bind:open={_settingsOpen} />
<SetupWizard bind:open={_wizardOpen} />

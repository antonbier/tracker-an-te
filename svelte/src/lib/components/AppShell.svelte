<script>
  import { currentPage, isDark, theme, settingsOpen } from '$lib/stores.js';
  import Header from './Header.svelte';
  import Sidebar from './Sidebar.svelte';
  import BottomNav from './BottomNav.svelte';
  import FieldGuide from './FieldGuide.svelte';
  import Settings from './Settings.svelte';

  let { children } = $props();

  let fieldGuideOpen = $state(false);
  // settingsOpen store: sync local state with global store
  let _settingsOpen = $state(false);
  $effect(() => { if ($settingsOpen) { _settingsOpen = true; settingsOpen.set(false); } });

  function toggleDark() {
    theme.set($isDark ? '' : 'dark');
  }
</script>

<div class="flex h-screen overflow-hidden" style="background:var(--ws-bg);color:var(--ws-text)">
  <!-- Sidebar (desktop only) -->
  <Sidebar onSettings={() => _settingsOpen = true} />

  <!-- Main area -->
  <div class="flex flex-col flex-1 min-w-0 overflow-hidden">
    <Header
      onFieldGuide={() => fieldGuideOpen = true}
      onSettings={() => _settingsOpen = true}
      onToggleDark={toggleDark}
    />
    <!-- Main scroll area: pb-0 on desktop, content-area handles its own scroll -->
    <main class="flex-1 overflow-y-auto p-4 md:p-6">
      {@render children()}
    </main>
    <!-- BottomNav renders fixed + its own spacer div -->
    <BottomNav onSettings={() => _settingsOpen = true} />
  </div>
</div>

<!-- Modals — rendered at AppShell root, outside any stacking context -->
<FieldGuide bind:open={fieldGuideOpen} />
<Settings bind:open={_settingsOpen} />

<script>
  import '../app.css';
  import { onMount } from 'svelte';
  import { theme, isDark, apiUrl, onboardingDone, jwtToken, currentUser, appStatus, logout } from '$lib/stores.js';
  import { loadLocale } from '$lib/i18n.js';
  import { lang } from '$lib/stores.js';
  import { api } from '$lib/api.js';
  import Toast    from '$lib/components/Toast.svelte';
  import AppShell from '$lib/components/AppShell.svelte';
  import Onboarding from '$lib/components/Onboarding.svelte';
  import Login    from '$lib/components/Login.svelte';
  import Setup    from '$lib/components/Setup.svelte';

  let { children } = $props();

  let statusLoading = $state(true);

  // Apply dark mode to <html>
  $effect(() => {
    if ($isDark) document.documentElement.classList.add('dark');
    else document.documentElement.classList.remove('dark');
  });

  onMount(async () => {
    await loadLocale($lang);
    await checkStatus();
  });

  $effect(() => { loadLocale($lang); });

  async function checkStatus() {
    statusLoading = true;
    if (!$apiUrl) { statusLoading = false; return; }
    try {
      const s = await api('/api/status');
      appStatus.set(s);
      // If auth disabled or user already has valid token → stay logged in
      // If token exists but backend says auth disabled → clear token (cleanup)
      if (!s.auth_enabled && $jwtToken) {
        // keep token for potential future re-enable, but don't require it
      }
    } catch {
      // Backend unreachable — proceed without auth check
      appStatus.set({ auth_enabled: false, needs_setup: false });
    }
    statusLoading = false;
  }

  // Recheck status when apiUrl changes (e.g. after onboarding)
  $effect(() => {
    if ($apiUrl && $onboardingDone) checkStatus();
  });

  // Gate logic
  const needsOnboarding = $derived(!$onboardingDone || !$apiUrl);
  const needsSetup      = $derived(!needsOnboarding && $appStatus?.needs_setup === true);
  const needsLogin      = $derived(
    !needsOnboarding &&
    !needsSetup &&
    $appStatus?.auth_enabled === true &&
    !$jwtToken
  );
  const showApp = $derived(!needsOnboarding && !needsSetup && !needsLogin && !statusLoading);
</script>

{#if needsOnboarding}
  <Onboarding onDone={checkStatus} />
{:else if statusLoading}
  <!-- Minimal loading screen while checking /api/status -->
  <div class="fixed inset-0 flex items-center justify-center" style="background:var(--ws-bg)">
    <div class="text-center">
      <div class="text-4xl mb-3">🧭</div>
      <p class="text-sm" style="color:var(--ws-muted)">Verbinde…</p>
    </div>
  </div>
{:else if needsSetup}
  <Setup onDone={checkStatus} />
{:else if needsLogin}
  <Login onDone={checkStatus} />
{:else if showApp}
  <AppShell>
    {@render children()}
  </AppShell>
{/if}

<Toast />

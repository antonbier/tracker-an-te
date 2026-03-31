<script>
  import '../app.css';
  import { onMount } from 'svelte';
  import { theme, isDark, apiUrl, onboardingDone, jwtToken,
           appStatus, loadSettingsFromBackend } from '$lib/stores.js';
  import { loadLocale } from '$lib/i18n.js';
  import { lang } from '$lib/stores.js';
  import { api } from '$lib/api.js';
  import Toast      from '$lib/components/Toast.svelte';
  import AppShell   from '$lib/components/AppShell.svelte';
  import Onboarding from '$lib/components/Onboarding.svelte';
  import Login      from '$lib/components/Login.svelte';
  import Setup      from '$lib/components/Setup.svelte';

  let { children } = $props();

  // No statusLoading screen — avoids invisible overlay blocking clicks
  // Status is checked silently in background after onboarding
  let ready = $state(false);

  $effect(() => {
    if ($isDark) document.documentElement.classList.add('dark');
    else document.documentElement.classList.remove('dark');
  });

  onMount(async () => {
    await loadLocale($lang);
    if ($apiUrl && $onboardingDone) {
      await checkStatus();
    }
    ready = true;
  });

  $effect(() => { loadLocale($lang); });

  async function checkStatus() {
    if (!$apiUrl) { ready = true; return; }
    try {
      const s = await api('/api/status');
      appStatus.set(s);
    } catch {
      appStatus.set({ auth_enabled: false, needs_setup: false });
    } finally {
      try { await loadSettingsFromBackend($apiUrl); } catch {}
    }
  }

  const needsOnboarding = $derived(!$onboardingDone || !$apiUrl);
  const needsSetup  = $derived(!needsOnboarding && $appStatus?.needs_setup === true);
  const needsLogin  = $derived(
    !needsOnboarding && !needsSetup &&
    $appStatus?.auth_enabled === true && !$jwtToken
  );
  const showApp = $derived(ready && !needsOnboarding && !needsSetup && !needsLogin);
</script>

{#if needsOnboarding}
  <Onboarding onDone={async () => { await checkStatus(); ready = true; }} />
{:else if needsSetup}
  <Setup onDone={async () => { await checkStatus(); ready = true; }} />
{:else if needsLogin}
  <Login onDone={async () => { await checkStatus(); ready = true; }} />
{:else if showApp}
  <AppShell>
    {@render children()}
  </AppShell>
{/if}

<Toast />

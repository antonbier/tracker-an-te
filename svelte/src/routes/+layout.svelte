<script>
  import '../app.css';
  import { onMount } from 'svelte';
  import { theme, isDark, apiUrl, onboardingDone, jwtToken, currentUser,
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
  let statusLoading = $state(false);

  $effect(() => {
    if ($isDark) document.documentElement.classList.add('dark');
    else document.documentElement.classList.remove('dark');
  });

  onMount(async () => {
    await loadLocale($lang);
    // Only check status if backend is configured AND onboarding is done
    if ($apiUrl && $onboardingDone) {
      await checkStatus();
    }
  });

  $effect(() => { loadLocale($lang); });

  async function checkStatus() {
    // Guard: never call without apiUrl
    if (!$apiUrl) return;
    statusLoading = true;
    try {
      const s = await api('/api/status');
      appStatus.set(s);
    } catch {
      appStatus.set({ auth_enabled: false, needs_setup: false });
    } finally {
      // Always reset — even if loadSettingsFromBackend throws
      try { await loadSettingsFromBackend($apiUrl); } catch {}
      statusLoading = false;
    }
  }

  // Reactive: re-check when apiUrl changes AFTER onboarding
  // But ONLY when both apiUrl and onboardingDone are set
  $effect(() => {
    const url = $apiUrl;
    const done = $onboardingDone;
    if (url && done) checkStatus();
  });

  const needsOnboarding = $derived(!$onboardingDone || !$apiUrl);
  const needsSetup  = $derived(!needsOnboarding && $appStatus?.needs_setup === true);
  const needsLogin  = $derived(
    !needsOnboarding && !needsSetup &&
    $appStatus?.auth_enabled === true && !$jwtToken
  );
  const showApp = $derived(!needsOnboarding && !needsSetup && !needsLogin && !statusLoading);
</script>

{#if needsOnboarding}
  <Onboarding onDone={checkStatus} />
{:else if statusLoading}
  <div style="position:fixed;inset:0;display:flex;align-items:center;justify-content:center;background:var(--ws-bg)">
    <div style="text-align:center">
      <div style="font-size:2.5rem;margin-bottom:0.75rem">🧭</div>
      <p style="font-size:0.875rem;color:var(--ws-muted)">Verbinde…</p>
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

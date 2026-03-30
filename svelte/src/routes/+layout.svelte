<script>
  import '../app.css';
  import { onMount } from 'svelte';
  import { theme, isDark, apiUrl, onboardingDone, jwtToken, currentUser,
           appStatus, logout, loadSettingsFromBackend } from '$lib/stores.js';
  import { loadLocale, setLang } from '$lib/i18n.js';
  import { lang } from '$lib/stores.js';
  import { api } from '$lib/api.js';
  import Toast      from '$lib/components/Toast.svelte';
  import AppShell   from '$lib/components/AppShell.svelte';
  import Onboarding from '$lib/components/Onboarding.svelte';
  import Login      from '$lib/components/Login.svelte';
  import Setup      from '$lib/components/Setup.svelte';

  let { children } = $props();
  let statusLoading = $state(true);

  $effect(() => {
    if ($isDark) document.documentElement.classList.add('dark');
    else document.documentElement.classList.remove('dark');
  });

  onMount(async () => {
    await loadLocale($lang);
    await checkStatus();
  });

  // Reaktiv: Sprache wechsel
  $effect(() => { loadLocale($lang); });

  async function checkStatus() {
    statusLoading = true;
    if (!$apiUrl) { statusLoading = false; return; }
    try {
      const s = await api('/api/status');
      appStatus.set(s);
    } catch {
      appStatus.set({ auth_enabled: false, needs_setup: false });
    }
    // Load settings + version from backend
    await loadSettingsFromBackend($apiUrl);
    statusLoading = false;
  }

  $effect(() => {
    if ($apiUrl && $onboardingDone) checkStatus();
  });

  const needsOnboarding = $derived(!$onboardingDone || !$apiUrl);
  const needsSetup      = $derived(!needsOnboarding && $appStatus?.needs_setup === true);
  const needsLogin      = $derived(
    !needsOnboarding && !needsSetup &&
    $appStatus?.auth_enabled === true && !$jwtToken
  );
  const showApp = $derived(!needsOnboarding && !needsSetup && !needsLogin && !statusLoading);
</script>

{#if needsOnboarding}
  <Onboarding onDone={checkStatus} />
{:else if statusLoading}
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

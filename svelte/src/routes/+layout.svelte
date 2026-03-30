<script>
  import '../app.css';
  import { onMount } from 'svelte';
  import { theme, isDark, apiUrl, onboardingDone } from '$lib/stores.js';
  import { loadLocale } from '$lib/i18n.js';
  import { lang } from '$lib/stores.js';
  import Toast from '$lib/components/Toast.svelte';
  import AppShell from '$lib/components/AppShell.svelte';
  import Onboarding from '$lib/components/Onboarding.svelte';

  let { children } = $props();

  // Apply dark mode to <html>
  $effect(() => {
    if ($isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  });

  onMount(async () => {
    await loadLocale($lang);
  });
</script>

{#if !$onboardingDone && !$apiUrl}
  <Onboarding />
{:else}
  <AppShell>
    {@render children()}
  </AppShell>
{/if}

<Toast />

<script>
  /**
   * WeatherWidget.svelte
   * Shows current weather for the trip destination.
   * Visible only when phase === 'active' OR daysUntilStart <= 7.
   */
  import { onMount } from 'svelte';
  import { wmoIcon } from './helpers.js';

  let { destination = '', phase = 'planning', daysUntilStart = 999 } = $props();

  let weather    = $state(null);
  let loading    = $state(false);
  let error      = $state(false);

  const shouldShow = $derived(phase === 'active' || daysUntilStart <= 7);

  let fetched = false;

  onMount(() => {
    if (shouldShow && destination && !fetched) {
      fetched = true;
      fetchWeather();
    }
  });

  async function fetchWeather() {
    if (!destination || loading) return;
    loading = true; error = false;
    try {
      const geoRes  = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(destination)}&count=1&language=de&format=json`);
      const geoData = await geoRes.json();
      const loc = geoData.results?.[0];
      if (!loc) { loading = false; return; }
      const wRes  = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${loc.latitude}&longitude=${loc.longitude}&current_weather=true&timezone=auto`);
      const wData = await wRes.json();
      const cw = wData.current_weather;
      if (cw) weather = { temp: Math.round(cw.temperature), wind: Math.round(cw.windspeed), icon: wmoIcon(cw.weathercode), city: loc.name };
    } catch { error = true; }
    loading = false;
  }
</script>

{#if shouldShow}
  <div class="rounded-2xl border p-4 flex items-center gap-4"
    style="background:var(--ws-surface2);border-color:var(--ws-border)">
    {#if loading}
      <div class="w-10 h-10 rounded-full animate-pulse" style="background:var(--ws-border)"></div>
      <div class="space-y-1.5">
        <div class="h-3 w-24 rounded animate-pulse" style="background:var(--ws-border)"></div>
        <div class="h-3 w-16 rounded animate-pulse" style="background:var(--ws-border)"></div>
      </div>
    {:else if weather}
      <span class="text-4xl leading-none">{weather.icon}</span>
      <div class="flex-1 min-w-0">
        <div class="text-2xl font-bold font-mono" style="color:var(--ws-text)">{weather.temp}°C</div>
        <div class="text-xs" style="color:var(--ws-muted)">🌬️ {weather.wind} km/h · {weather.city}</div>
      </div>
      <div class="text-[10px] px-2 py-0.5 rounded-full font-semibold"
        style="background:color-mix(in srgb,var(--ws-accent) 12%,var(--ws-surface));color:var(--ws-accent)">
        Live
      </div>
    {:else if !error}
      <span class="text-2xl">🌡️</span>
      <span class="text-sm" style="color:var(--ws-muted)">Wetter nicht verfügbar</span>
    {/if}
  </div>
{/if}

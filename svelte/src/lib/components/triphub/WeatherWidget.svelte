<script>
  /**
   * WeatherWidget.svelte — 3-day forecast via backend proxy.
   * Direct Open-Meteo calls are blocked by CORS on HTTPS deployments.
   * Uses /api/settings/geocode-weather?q=<destination> backend proxy instead.
   */
  import { onMount } from 'svelte';
  import { apiUrl } from '$lib/stores.js';
  import { get } from 'svelte/store';
  import { wmoIcon } from './helpers.js';

  let { destination = '', phase = 'planning', daysUntilStart = 999 } = $props();

  let days    = $state([]);
  let loading = $state(false);
  let errMsg  = $state('');

  const shouldShow = $derived(phase === 'active' || daysUntilStart <= 7);

  onMount(() => {
    if ((phase === 'active' || daysUntilStart <= 7) && destination.trim()) {
      fetchForecast();
    }
  });

  async function fetchForecast() {
    if (loading || days.length > 0) return;
    loading = true;
    errMsg  = '';
    try {
      // Use backend proxy to avoid CORS — same pattern as geocoding
      const base = get(apiUrl) || '';
      const url  = `${base}/api/settings/geocode-weather?q=${encodeURIComponent(destination.trim())}`;
      const res  = await fetch(url);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      const d    = data.daily;
      if (!d?.time?.length) throw new Error('Keine Wetterdaten erhalten');

      days = d.time.slice(0, 3).map((date, i) => ({
        date,
        tempMax: Math.round(d.temperature_2m_max[i]),
        tempMin: Math.round(d.temperature_2m_min[i]),
        icon:    wmoIcon(d.weather_code[i]),
        precip:  Math.round((d.precipitation_sum?.[i] ?? 0) * 10) / 10,
        city:    i === 0 ? data.city : '',
      }));
    } catch (e) {
      console.warn('[WeatherWidget]', e.message);
      errMsg = e.message;
    }
    loading = false;
  }

  const DAY_LABELS = ['Heute', 'Morgen', 'Übermorgen'];
</script>

{#if shouldShow && destination.trim()}
  <div class="rounded-2xl border overflow-hidden"
    style="background:var(--ws-surface2);border-color:var(--ws-border)">

    {#if loading}
      <div class="flex gap-3 p-4">
        {#each [1,2,3] as _}
          <div class="flex-1 h-20 rounded-xl animate-pulse" style="background:var(--ws-border)"></div>
        {/each}
      </div>

    {:else if days.length > 0}
      <div class="flex items-center gap-2 px-4 pt-3 pb-1">
        <span class="text-xs font-semibold" style="color:var(--ws-muted)">🌡️ {days[0].city}</span>
        <span class="text-[10px] px-2 py-0.5 rounded-full font-semibold ml-auto"
          style="background:color-mix(in srgb,var(--ws-accent) 12%,var(--ws-surface));color:var(--ws-accent)">
          Live
        </span>
      </div>
      <div class="grid grid-cols-3 divide-x" style="border-color:var(--ws-border)">
        {#each days as day, i}
          <div class="flex flex-col items-center gap-1 px-3 py-3">
            <span class="text-[11px] font-semibold"
              style="color:{i === 0 ? 'var(--ws-accent)' : 'var(--ws-muted)'}">
              {DAY_LABELS[i]}
            </span>
            <span class="text-3xl leading-none">{day.icon}</span>
            <div class="flex items-baseline gap-1 mt-0.5">
              <span class="text-sm font-bold" style="color:var(--ws-text)">{day.tempMax}°</span>
              <span class="text-xs" style="color:var(--ws-muted)">{day.tempMin}°</span>
            </div>
            {#if day.precip > 0}
              <span class="text-[10px]" style="color:#60a5fa">💧 {day.precip}mm</span>
            {/if}
          </div>
        {/each}
      </div>

    {:else}
      <div class="flex items-center justify-between px-4 py-4">
        <div class="flex items-center gap-3">
          <span class="text-2xl">🌡️</span>
          <div>
            <span class="text-sm block" style="color:var(--ws-muted)">Wetterdaten nicht verfügbar</span>
            {#if errMsg}
              <span class="text-[10px]" style="color:var(--ws-muted)">{errMsg}</span>
            {/if}
          </div>
        </div>
        <button onclick={() => { errMsg=''; days=[]; fetchForecast(); }}
          class="text-xs px-2 py-1 rounded-lg border hover:opacity-70 shrink-0"
          style="border-color:var(--ws-border);color:var(--ws-muted)">↺</button>
      </div>
    {/if}
  </div>
{/if}

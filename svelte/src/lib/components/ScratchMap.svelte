<script>
  import { onMount } from 'svelte';
  import { bucketlist } from '$lib/stores.js';

  let { journalTrips = [], plannedTrips = [], selectedYear = new Date().getFullYear() } = $props();

  let mapEl   = $state(null);
  let loading = $state(true);
  let loadErr = $state('');
  let map     = null;

  const COLORS = { visited: '#2d6a4f', planned: '#2563eb', bucket: '#c4622d' };

  const DEMO_VISITED = [
    { lat: 47.81, lng: 13.05, name: 'Salzburg', type: 'visited' },
    { lat: 41.90, lng: 12.50, name: 'Rom',       type: 'visited' },
    { lat: 48.86, lng:  2.35, name: 'Paris',     type: 'visited' },
  ];
  const DEMO_PLANNED = [{ lat: 51.51, lng: -0.13, name: 'London (geplant)', type: 'planned' }];
  const DEMO_BUCKET  = [
    { lat: 35.68,  lng: 139.65, name: 'Tokyo',        type: 'bucket' },
    { lat: -13.16, lng: -72.54, name: 'Machu Picchu',  type: 'bucket' },
  ];

  onMount(async () => {
    let destroyed = false;
    await new Promise(r => setTimeout(r, 120));
    if (!mapEl || destroyed) { loading = false; return; }

    try {
      // Lokale Imports — kein CDN, kein Netzwerk-Fehler möglich
      const { default: jsVectorMap } = await import('jsvectormap');
      await import('jsvectormap/dist/maps/world.js');

      if (destroyed) return;

      const yr = String(selectedYear);

      const visited = journalTrips
        .filter(t => t.lat && t.lon && (t.start_date || '').slice(0, 4) === yr)
        .map(t => ({ lat: +t.lat, lng: +t.lon, type: 'visited',
          name: [t.location_name, t.country].filter(Boolean).join(', ') || `${t.lat},${t.lon}` }));

      const planned = plannedTrips
        .filter(t => t.lat && t.lon && (t.dateStart || t.date || '').slice(0, 4) === yr)
        .map(t => ({ lat: +t.lat, lng: +t.lon, type: 'planned', name: t.name }));

      const bucket = ($bucketlist ?? [])
        .filter(b => !b.done && b.lat && b.lon)
        .map(b => ({ lat: +b.lat, lng: +b.lon, type: 'bucket',
          name: b.item + (b.dest ? ` (${b.dest})` : '') }));

      const vList = visited.length ? visited : DEMO_VISITED;
      const pList = planned.length ? planned : DEMO_PLANNED;
      const bList = bucket.length  ? bucket  : DEMO_BUCKET;
      const allMarkers = [...vList, ...pList, ...bList];

      map = new jsVectorMap({
        selector: mapEl,
        map: 'world',
        zoomOnScroll: false,
        zoomButtons: true,
        backgroundColor: 'transparent',
        regionStyle: {
          initial: { fill: '#e8ddd0', stroke: '#d4c4b0', strokeWidth: 0.4 },
          hover:   { fill: '#c4622d', fillOpacity: 0.35 },
        },
        markers: allMarkers.map(m => ({ name: m.name, coords: [m.lat, m.lng] })),
        markerStyle: {
          initial: { r: 5, stroke: '#fff', strokeWidth: 1.5, fill: '#aaa' },
          hover:   { r: 7 },
        },
        onMarkerTooltipShow(evt, tooltip, idx) {
          tooltip.text(allMarkers[idx]?.name ?? '');
        },
      });

      // Marker-Farben per DOM patchen (zuverlässiger als style-Prop)
      setTimeout(() => {
        if (destroyed) return;
        mapEl.querySelectorAll('.jvm-markers circle, .jvm-marker').forEach((c, i) => {
          c.setAttribute('fill', COLORS[allMarkers[i]?.type ?? 'visited']);
        });
      }, 250);

      loading = false;
    } catch (e) {
      console.error('[ScratchMap]', e);
      loadErr = 'Karte konnte nicht initialisiert werden: ' + e.message;
      loading = false;
    }

    return () => {
      destroyed = true;
      try { map?.destroy?.(); } catch {}
      map = null;
    };
  });
</script>

<svelte:head>
  <style>@import 'jsvectormap/dist/css/jsvectormap.min.css';</style>
</svelte:head>

<div class="relative w-full rounded-xl overflow-hidden border border-stone-200 bg-stone-50" style="height:300px">
  <div bind:this={mapEl} class="w-full h-full" style="min-height:300px"></div>

  {#if loading && !loadErr}
    <div class="absolute inset-0 flex items-center justify-center bg-stone-50/90 pointer-events-none">
      <div class="text-center">
        <div class="text-2xl mb-1 animate-pulse">🗺️</div>
        <span class="text-stone-400 text-xs">Karte lädt…</span>
      </div>
    </div>
  {/if}

  {#if loadErr}
    <div class="absolute inset-0 flex flex-col items-center justify-center bg-stone-50 gap-2 p-4">
      <div class="text-2xl">⚠️</div>
      <span class="text-stone-500 text-xs text-center">{loadErr}</span>
    </div>
  {/if}

  {#if !loading && !loadErr}
    <div class="absolute bottom-2 left-2 flex gap-2.5 bg-white/90 backdrop-blur-sm
                border border-stone-200 rounded-lg px-3 py-1.5 text-xs shadow-sm pointer-events-none">
      <span class="flex items-center gap-1.5 text-stone-600">
        <span class="w-2.5 h-2.5 rounded-full inline-block" style="background:#2d6a4f"></span>Besucht
      </span>
      <span class="flex items-center gap-1.5 text-stone-600">
        <span class="w-2.5 h-2.5 rounded-full inline-block" style="background:#2563eb"></span>Geplant
      </span>
      <span class="flex items-center gap-1.5 text-stone-600">
        <span class="w-2.5 h-2.5 rounded-full inline-block" style="background:#c4622d"></span>Wunschziel
      </span>
    </div>
  {/if}
</div>

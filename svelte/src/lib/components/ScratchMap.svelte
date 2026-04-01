<script>
  import { onMount, onDestroy } from 'svelte';
  import { bucketlist } from '$lib/stores.js';

  let { journalTrips = [], plannedTrips = [], selectedYear = new Date().getFullYear() } = $props();

  let mapEl     = $state(null);
  let loading   = $state(true);
  let loadErr   = $state('');
  let geocoding = $state(false);
  let map       = null;
  let jsVMClass = null;   // jsvectormap Klasse — einmal laden, dann wiederverwenden
  let initTimer = null;

  const COLORS = { visited: '#2d6a4f', planned: '#2563eb', bucket: '#c4622d' };

  // ── Geocoding-Cache (sessionStorage) ───────────────────────────────────────
  function getCached(name) {
    try { const v = sessionStorage.getItem(`ws-geo:${name}`); return v ? JSON.parse(v) : null; }
    catch { return null; }
  }
  function setCached(name, c) {
    try { sessionStorage.setItem(`ws-geo:${name}`, JSON.stringify(c)); } catch {}
  }
  async function geocode(name) {
    if (!name?.trim()) return null;
    const cached = getCached(name);
    if (cached) return cached;
    await new Promise(r => setTimeout(r, 1100)); // Nominatim: 1 req/s
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(name)}&format=json&limit=1`,
        { headers: { 'Accept-Language': 'de', 'User-Agent': 'WanderSuite/1.0' } }
      );
      const data = await res.json();
      if (data.length > 0) {
        const c = { lat: parseFloat(data[0].lat), lng: parseFloat(data[0].lon) };
        setCached(name, c);
        return c;
      }
    } catch {}
    return null;
  }

  // ── Karte aufbauen ─────────────────────────────────────────────────────────
  async function initMap() {
    if (!mapEl) return;

    // Alte Karte zerstören
    try { map?.destroy?.(); } catch {}
    map = null;

    // jsvectormap nur einmal laden
    if (!jsVMClass) {
      const mod = await import('jsvectormap');
      jsVMClass = mod.default;
      await import('jsvectormap/dist/maps/world.js');
      await new Promise(r => setTimeout(r, 80)); // world.js registrieren lassen
    }

    const yr = String(selectedYear);

    // ── Visited: Dawarich-Trips mit lat/lon ───────────────────────────────
    const visited = journalTrips
      .filter(t => t.lat && t.lon && (t.start_date || '').slice(0, 4) === yr)
      .map(t => ({
        lat: +t.lat, lng: +t.lon, type: 'visited',
        name: [t.location_name, t.country].filter(Boolean).join(', ') || `${t.lat},${t.lon}`,
      }));

    // ── Planned: geplante Trips — Ortsname geocodieren ────────────────────
    const plannedBase = plannedTrips
      .filter(t => (t.dateStart || t.date || '').slice(0, 4) === yr);

    const planned = plannedBase.filter(t => t.lat && t.lng)
      .map(t => ({ lat: +t.lat, lng: +t.lng, type: 'planned', name: t.name }));

    const plannedNeedGeo = plannedBase.filter(t => !t.lat || !t.lng);

    // ── Bucket: Wunschziele ───────────────────────────────────────────────
    const bucketBase = ($bucketlist ?? []).filter(b => !b.done);
    const bucket = bucketBase.filter(b => b.lat && (b.lng || b.lon))
      .map(b => ({ lat: +b.lat, lng: +(b.lng || b.lon), type: 'bucket', name: b.dest || b.item }));

    const bucketNeedGeo = bucketBase.filter(b => !b.lat || !(b.lng || b.lon));

    // Geocoding wenn nötig
    if (plannedNeedGeo.length || bucketNeedGeo.length) {
      geocoding = true;
      for (const t of plannedNeedGeo) {
        const c = await geocode(t.name);
        if (c) planned.push({ ...c, type: 'planned', name: t.name });
      }
      for (const b of bucketNeedGeo) {
        const name = b.dest || b.item;
        const c = await geocode(name);
        if (c) bucket.push({ ...c, type: 'bucket', name });
      }
      geocoding = false;
    }

    const allMarkers = [...visited, ...planned, ...bucket];

    // Karte bauen (auch wenn keine Marker — zeigt wenigstens die Weltkarte)
    map = new jsVMClass({
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

    // Marker-Farben patchen
    setTimeout(() => {
      mapEl?.querySelectorAll('.jvm-markers circle, .jvm-marker').forEach((c, i) => {
        c.setAttribute('fill', COLORS[allMarkers[i]?.type ?? 'visited']);
      });
    }, 250);

    loading = false;
  }

  // ── $effect: neu zeichnen wenn Props sich ändern ──────────────────────────
  // journalTrips.length als Trigger — ändert sich wenn Daten geladen werden
  $effect(() => {
    // Abhängigkeiten registrieren
    const _jt = journalTrips.length;
    const _pt = plannedTrips.length;
    const _bl = $bucketlist.length;
    const _yr = selectedYear;
    const _el = mapEl;

    if (!_el) return; // Container noch nicht im DOM

    // Debounce: kurz warten damit nicht bei jedem Rendering-Tick neu gezeichnet wird
    clearTimeout(initTimer);
    initTimer = setTimeout(() => {
      initMap().catch(e => {
        console.error('[ScratchMap]', e);
        loadErr = e.message;
        loading = false;
      });
    }, 200);
  });

  onDestroy(() => {
    clearTimeout(initTimer);
    try { map?.destroy?.(); } catch {}
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

  {#if geocoding}
    <div class="absolute top-2 right-2 bg-white/90 border border-stone-200 rounded-lg
                px-2.5 py-1.5 text-xs text-stone-500 shadow-sm flex items-center gap-1.5">
      <span class="animate-pulse">📍</span> Orte werden geocodiert…
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

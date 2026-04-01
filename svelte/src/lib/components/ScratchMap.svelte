<script>
  import { onMount } from 'svelte';
  import { bucketlist } from '$lib/stores.js';

  let { journalTrips = [], plannedTrips = [], selectedYear = new Date().getFullYear() } = $props();

  let mapEl    = $state(null);
  let loading  = $state(true);
  let loadErr  = $state('');
  let geocoding = $state(false);
  let map      = null;

  const COLORS = { visited: '#2d6a4f', planned: '#2563eb', bucket: '#c4622d' };

  // Nominatim-Geocode-Cache (sessionStorage damit kein redundanter Traffic)
  function geoKey(name) { return `ws-geo:${name.toLowerCase().trim()}`; }

  function getCached(name) {
    try {
      const v = sessionStorage.getItem(geoKey(name));
      return v ? JSON.parse(v) : null;
    } catch { return null; }
  }

  function setCached(name, coords) {
    try { sessionStorage.setItem(geoKey(name), JSON.stringify(coords)); } catch {}
  }

  async function geocode(name) {
    if (!name?.trim()) return null;
    const cached = getCached(name);
    if (cached) return cached;

    // Rate-limit: 1 Request/s laut Nominatim-Policy
    await new Promise(r => setTimeout(r, 1100));
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(name)}&format=json&limit=1`,
        { headers: { 'Accept-Language': 'de', 'User-Agent': 'WanderSuite/1.0' } }
      );
      const data = await res.json();
      if (data.length > 0) {
        const coords = { lat: parseFloat(data[0].lat), lng: parseFloat(data[0].lon) };
        setCached(name, coords);
        return coords;
      }
    } catch {}
    return null;
  }

  // Alle Einträge ohne Koordinaten geocodieren
  async function enrichWithCoords(items, nameKey) {
    const results = [];
    for (const item of items) {
      if (item.lat && item.lng) { results.push(item); continue; }
      if (item.lat && item.lon) { results.push({ ...item, lng: item.lon }); continue; }
      const name = item[nameKey] || item.name || '';
      if (!name) continue;
      const coords = await geocode(name);
      if (coords) results.push({ ...item, ...coords });
    }
    return results;
  }

  onMount(async () => {
    let destroyed = false;
    await new Promise(r => setTimeout(r, 120));
    if (!mapEl || destroyed) { loading = false; return; }

    try {
      const { default: jsVectorMap } = await import('jsvectormap');
      await import('jsvectormap/dist/maps/world.js');
      if (destroyed) return;

      const yr = String(selectedYear);

      // ── Visited: Dawarich-Trips mit lat/lon ──────────────────────────────
      const visitedRaw = journalTrips
        .filter(t => t.lat && t.lon && (t.start_date || '').slice(0, 4) === yr)
        .map(t => ({
          lat: +t.lat, lng: +t.lon, type: 'visited',
          name: [t.location_name, t.country].filter(Boolean).join(', ') || `${t.lat},${t.lon}`,
        }));

      // ── Planned: geplante Trips — geocodieren wenn nötig ─────────────────
      const plannedRaw = plannedTrips
        .filter(t => (t.dateStart || t.date || '').slice(0, 4) === yr)
        .map(t => ({ lat: t.lat, lng: t.lon, type: 'planned', name: t.name }));

      // ── Bucket: Wunschziele — geocodieren wenn nötig ─────────────────────
      const bucketRaw = ($bucketlist ?? [])
        .filter(b => !b.done)
        .map(b => ({ lat: b.lat, lng: b.lon, type: 'bucket',
          name: b.dest || b.item }));

      // Geocoding nur wenn nötig (Einträge ohne Koordinaten vorhanden)
      const needsGeo = [
        ...plannedRaw.filter(t => !t.lat || !t.lng),
        ...bucketRaw.filter(b => !b.lat || !b.lng),
      ].length > 0;

      let visited = visitedRaw;
      let planned = plannedRaw.filter(t => t.lat && t.lng);
      let bucket  = bucketRaw.filter(b => b.lat && b.lng);

      if (needsGeo) {
        geocoding = true;
        // Planned geocodieren
        const plannedNeedGeo = plannedRaw.filter(t => !t.lat || !t.lng);
        for (const t of plannedNeedGeo) {
          if (destroyed) break;
          const c = await geocode(t.name);
          if (c) planned.push({ ...t, ...c });
        }
        // Bucket geocodieren
        const bucketNeedGeo = bucketRaw.filter(b => !b.lat || !b.lng);
        for (const b of bucketNeedGeo) {
          if (destroyed) break;
          const c = await geocode(b.name);
          if (c) bucket.push({ ...b, ...c });
        }
        geocoding = false;
      }

      if (destroyed) return;

      // Keine Demo-Daten mehr — nur echte Daten oder leere Karte
      const allMarkers = [...visited, ...planned, ...bucket];

      // Karte initialisieren
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

      // Marker-Farben per DOM patchen
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

  <!-- Laden -->
  {#if loading && !loadErr}
    <div class="absolute inset-0 flex items-center justify-center bg-stone-50/90 pointer-events-none">
      <div class="text-center">
        <div class="text-2xl mb-1 animate-pulse">🗺️</div>
        <span class="text-stone-400 text-xs">Karte lädt…</span>
      </div>
    </div>
  {/if}

  <!-- Geocoding läuft -->
  {#if geocoding}
    <div class="absolute top-2 right-2 bg-white/90 border border-stone-200 rounded-lg px-2.5 py-1.5 text-xs text-stone-500 shadow-sm flex items-center gap-1.5">
      <span class="animate-pulse">📍</span> Orte werden geocodiert…
    </div>
  {/if}

  <!-- Fehler -->
  {#if loadErr}
    <div class="absolute inset-0 flex flex-col items-center justify-center bg-stone-50 gap-2 p-4">
      <div class="text-2xl">⚠️</div>
      <span class="text-stone-500 text-xs text-center">{loadErr}</span>
    </div>
  {/if}

  <!-- Legende -->
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

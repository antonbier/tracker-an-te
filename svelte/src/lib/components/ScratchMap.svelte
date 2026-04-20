<script>
  import { onMount, onDestroy } from 'svelte';
  import { bucketlist, apiUrl } from '$lib/stores.js';
  import { api } from '$lib/api.js';

  let { journalTrips = [], plannedTrips = [], selectedYear = new Date().getFullYear(), refreshKey = 0 } = $props();

  let mapEl      = $state(null);
  let loading    = $state(true);
  let loadErr    = $state('');
  let geocoding  = $state(false);
  let debugInfo  = $state('');
  let map        = null;
  let jsVMClass  = null;
  let initTimer  = null;

  const COLORS = { visited: '#2d6a4f', planned: '#2563eb', bucket: '#c4622d' };

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
    await new Promise(r => setTimeout(r, 600));
    try {
      // Use api() helper — sendet automatisch JWT-Token
      const data = await api(`/api/settings/geocode?q=${encodeURIComponent(name)}`);
      if (Array.isArray(data) && data.length > 0) {
        const c = { lat: parseFloat(data[0].lat), lng: parseFloat(data[0].lon) };
        setCached(name, c);
        return c;
      }
    } catch {}
    return null;
  }

  // BUG 8: jsvectormap+world.js einmalig vorladen (außerhalb von initMap),
  // damit "world" Map immer registriert ist wenn die Karte gerendert wird.
  let libReady = false;
  async function ensureLib() {
    if (libReady) return;
    const mod = await import('jsvectormap');
    jsVMClass  = mod.default;
    await import('jsvectormap/dist/maps/world.js');
    // Kurz warten bis die Map-Registry den world-Eintrag verarbeitet hat
    await new Promise(r => setTimeout(r, 150));
    libReady = true;
  }

  async function initMap() {
    if (!mapEl) return;
    try { map?.destroy?.(); } catch {}
    map = null;
    loading = true;
    loadErr = '';

    // Bibliothek laden (idempotent) — bevor mapEl benutzt wird
    await ensureLib();

    // ── Visited: GPS-Koordinaten aus journalTrips (Dawarich + manuell mit Geocoding) ─
    // Jahresfilter: nur Reisen des im Header gewaehlten Jahres.
    const visited = journalTrips
      .filter(t =>
        (t.start_date || '').slice(0, 4) === String(selectedYear) &&
        t.lat && t.lon
      )
      .map(t => ({
        lat: +t.lat,
        lng: +t.lon,
        type: 'visited',
        name: [t.location_name, t.country].filter(Boolean).join(', ') || t.name || `${t.lat},${t.lon}`
      }));

    // ── Planned: werden auf der Karte nicht mehr angezeigt ───────────────────
    // Nur besuchte Orte (Dawarich GPS) sind relevant — geplante Reisen ohne
    // verifizierte GPS-Daten werden ignoriert.
    const planned = [];

    // ── Bucket: alle Wunschziele ──────────────────────────────────────────────
    const bucket = [];
    for (const b of ($bucketlist ?? []).filter(b => !b.done)) {
      if (b.lat && (b.lng || b.lon)) {
        bucket.push({ lat: +b.lat, lng: +(b.lng||b.lon), type: 'bucket', name: b.dest||b.item });
      } else {
        const name = b.dest || b.item;
        if (name) {
          geocoding = true;
          const c = await geocode(name);
          if (c) bucket.push({ ...c, type: 'bucket', name });
        }
      }
    }
    geocoding = false;

    const allMarkers = [...visited, ...planned, ...bucket];
    debugInfo = `${visited.length} besucht`;

    map = new jsVMClass({
      selector: mapEl,
      map: 'world',
      zoomOnScroll: false,
      zoomButtons: true,
      backgroundColor: 'transparent',
      regionStyle: {
        initial: {
          fill: document.documentElement.classList.contains('dark') ? '#2a2a2a' : '#e8ddd0',
          stroke: document.documentElement.classList.contains('dark') ? '#3a3a3a' : '#d4c4b0',
          strokeWidth: 0.4
        },
        hover: { fill: '#c4622d', fillOpacity: 0.35 },
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

    setTimeout(() => {
      mapEl?.querySelectorAll('.jvm-markers circle, .jvm-marker').forEach((c, i) => {
        c.setAttribute('fill', COLORS[allMarkers[i]?.type ?? 'visited']);
      });
    }, 250);

    loading = false;
  }

  $effect(() => {
    // Reaktive Abhängigkeiten — refreshKey triggert sofortige Neu-Initialisierung
    // auch wenn journalTrips.length sich nicht ändert (erster Tab-Öffnen-Fix).
    const _jt = JSON.stringify(journalTrips.map(t => t.id ?? t.start_date));
    const _pt = plannedTrips.length;
    const _yr = selectedYear;
    const _rk = refreshKey;   // ändert sich bei Tab-Wechsel → erzwingt Redraw
    const _el = mapEl;
    if (!_el) return;

    // Sofort starten (kein Debounce beim ersten Render) wenn refreshKey sich ändert
    clearTimeout(initTimer);
    const delay = _rk ? 50 : 300;  // erste Init schneller
    initTimer = setTimeout(() => {
      initMap().catch(e => {
        console.error('[ScratchMap]', e);
        loadErr = e.message;
        loading = false;
      });
    }, delay);
  });

  onDestroy(() => {
    clearTimeout(initTimer);
    try { map?.destroy?.(); } catch {}
  });
</script>

<svelte:head>
  <style>@import 'jsvectormap/dist/css/jsvectormap.min.css';</style>
</svelte:head>

<div class="relative w-full rounded-xl overflow-hidden" style="height:300px;background:var(--ws-surface2);border:1px solid var(--ws-border)">
  <div bind:this={mapEl} class="w-full h-full" style="min-height:300px"></div>

  {#if loading && !loadErr}
    <div class="absolute inset-0 flex items-center justify-center pointer-events-none" style="background:color-mix(in srgb,var(--ws-surface2) 90%,transparent)">
      <div class="text-center">
        <div class="text-2xl mb-1 animate-pulse">🗺️</div>
        <span class="text-xs" style="color:var(--ws-muted)">Karte lädt…</span>
      </div>
    </div>
  {/if}

  {#if geocoding}
    <div class="absolute top-2 right-2 rounded-lg px-2.5 py-1.5 text-xs shadow-sm flex items-center gap-1.5"
         style="background:var(--ws-surface);border:1px solid var(--ws-border);color:var(--ws-muted)">
      <span class="animate-pulse">📍</span> Orte geocodieren…
    </div>
  {/if}

  {#if loadErr}
    <div class="absolute inset-0 flex flex-col items-center justify-center gap-2 p-4" style="background:var(--ws-surface2)">
      <div class="text-2xl">⚠️</div>
      <span class="text-xs text-center" style="color:var(--ws-muted)">{loadErr}</span>
    </div>
  {/if}

  {#if !loading && !loadErr}
    <div class="absolute bottom-2 left-2 flex gap-2.5 rounded-lg px-3 py-1.5 text-xs shadow-sm pointer-events-none"
         style="background:color-mix(in srgb,var(--ws-surface) 92%,transparent);border:1px solid var(--ws-border);backdrop-filter:blur(4px)">
      <span class="flex items-center gap-1.5" style="color:var(--ws-text)">
        <span class="w-2.5 h-2.5 rounded-full inline-block" style="background:#2d6a4f"></span>Besucht
      </span>

    </div>
  {/if}
</div>

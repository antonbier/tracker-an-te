<script>
  import { onMount } from 'svelte';
  import { bucketlist } from '$lib/stores.js';

  let { journalTrips = [], plannedTrips = [], selectedYear = new Date().getFullYear() } = $props();

  let mapEl   = $state(null);
  let loading = $state(true);
  let loadErr = $state('');
  let map     = null;

  // ── Marker-Farben & Beschriftungen ───────────────────────────────────────
  // visited  → grün  #2d6a4f  (✓)
  // planned  → blau  #2563eb  (✈)
  // bucketlist → orange #c4622d (★)

  const COLORS = { visited: '#2d6a4f', planned: '#2563eb', bucket: '#c4622d' };

  // Demo-Daten falls noch nichts vorhanden
  const DEMO_VISITED  = [
    { lat: 47.81, lng: 13.05, name: 'Salzburg' },
    { lat: 41.90, lng: 12.50, name: 'Rom'      },
    { lat: 48.86, lng:  2.35, name: 'Paris'    },
  ];
  const DEMO_PLANNED  = [{ lat: 51.51, lng: -0.13, name: 'London (geplant)' }];
  const DEMO_BUCKET   = [
    { lat: 35.68, lng: 139.65, name: 'Tokyo'       },
    { lat: -13.16, lng: -72.54, name: 'Machu Picchu' },
  ];

  function loadScript(src) {
    return new Promise((res, rej) => {
      if (document.querySelector(`script[src="${src}"]`)) { setTimeout(res, 80); return; }
      const s = document.createElement('script');
      s.src = src;
      s.onload = () => setTimeout(res, 80);
      s.onerror = rej;
      document.head.appendChild(s);
    });
  }
  function loadStyle(href) {
    return new Promise(res => {
      if (document.querySelector(`link[href="${href}"]`)) { res(); return; }
      const l = document.createElement('link');
      l.rel = 'stylesheet'; l.href = href; l.onload = res;
      document.head.appendChild(l);
    });
  }

  onMount(() => {
    const timer = setTimeout(async () => {
      if (!mapEl) { loadErr = 'Container fehlt.'; loading = false; return; }
      try {
        await loadStyle('https://cdn.jsdelivr.net/npm/jsvectormap@1.5.3/dist/css/jsvectormap.min.css');
        await loadScript('https://cdn.jsdelivr.net/npm/jsvectormap@1.5.3/dist/js/jsvectormap.min.js');
        await loadScript('https://cdn.jsdelivr.net/npm/jsvectormap@1.5.3/dist/maps/world.js');
        if (!window.jsVectorMap) throw new Error('jsVectorMap fehlt');

        // Visited: Chronik-Trips des gewählten Jahres mit Koordinaten
        const visitedRaw = journalTrips.filter(t =>
          t.lat && t.lon &&
          String((t.start_date || '').slice(0, 4)) === String(selectedYear)
        ).map(t => ({
          lat: +t.lat, lng: +t.lon,
          name: [t.location_name, t.country].filter(Boolean).join(', ') || `${t.lat},${t.lon}`,
          type: 'visited',
        }));

        // Planned: geplante Trips des Jahres (localStorage-Trips haben selten Koordinaten,
        // wir zeigen sie als Named-Marker ohne Koordinaten falls keine vorhanden → skip)
        // Planned nur wenn lat/lon vorhanden (kann später erweitert werden)
        const plannedRaw = plannedTrips.filter(t =>
          t.lat && t.lon &&
          String((t.dateStart || t.date || '').slice(0, 4)) === String(selectedYear)
        ).map(t => ({
          lat: +t.lat, lng: +t.lon,
          name: t.name,
          type: 'planned',
        }));

        // Bucket list: immer, keine Jahresfilterung (keine Jahreszuordnung)
        const bucketRaw = ($bucketlist ?? []).filter(b => !b.done && b.lat && b.lon).map(b => ({
          lat: +b.lat, lng: +b.lon,
          name: b.item + (b.dest ? ` (${b.dest})` : ''),
          type: 'bucket',
        }));

        // Fallback auf Demos
        const vList = visitedRaw.length ? visitedRaw : DEMO_VISITED.map(m => ({ ...m, type: 'visited' }));
        const pList = plannedRaw.length ? plannedRaw : DEMO_PLANNED.map(m => ({ ...m, type: 'planned' }));
        const bList = bucketRaw.length  ? bucketRaw  : DEMO_BUCKET.map(m => ({  ...m, type: 'bucket'  }));

        // Alle Marker kombiniert — Reihenfolge bestimmt Farb-Index
        const allMarkers = [...vList, ...pList, ...bList];

        const markers = allMarkers.map(m => ({
          name:   m.name,
          coords: [m.lat, m.lng],
          // jsVectorMap erlaubt style pro Marker
          style:  { fill: COLORS[m.type], stroke: '#fff', strokeWidth: 1.5, r: 5 },
        }));

        map = new window.jsVectorMap({
          selector: mapEl,
          map: 'world',
          zoomOnScroll: false,
          zoomButtons: true,
          backgroundColor: 'transparent',
          regionStyle: {
            initial: { fill: '#e8ddd0', stroke: '#d4c4b0', strokeWidth: 0.4 },
            hover:   { fill: '#c4622d', fillOpacity: 0.35 },
          },
          markers,
          markerStyle: {
            initial: { r: 5, stroke: '#fff', strokeWidth: 1.5, fill: '#c4622d' },
            hover:   { r: 7 },
          },
          // Per-Marker fill via onMarkerTooltipShow (Farbe wird unten per DOM gesetzt)
          onMarkerTooltipShow(evt, tooltip, idx) {
            tooltip.text(allMarkers[idx]?.name ?? '');
          },
        });

        // Marker-Farbe per DOM setzen (jsvectormap ignoriert style.fill im marker array
        // bei einigen Versionen — direktes SVG-Patching ist zuverlässiger)
        setTimeout(() => {
          const circles = mapEl.querySelectorAll('.jvm-markers circle, circle.jvm-marker');
          circles.forEach((c, i) => {
            const type = allMarkers[i]?.type ?? 'visited';
            c.setAttribute('fill', COLORS[type]);
            c.setAttribute('r', '5');
          });
        }, 250);

        loading = false;
      } catch (e) {
        console.error('[ScratchMap]', e);
        loadErr = 'Karte konnte nicht geladen werden.';
        loading = false;
      }
    }, 120);

    return () => {
      clearTimeout(timer);
      try { map?.destroy?.(); } catch {}
      map = null;
    };
  });
</script>

<div class="relative w-full rounded-xl overflow-hidden border border-stone-200 bg-stone-50" style="height:300px">
  <div bind:this={mapEl} class="w-full h-full" style="min-height:300px"></div>

  {#if loading && !loadErr}
    <div class="absolute inset-0 flex items-center justify-center bg-stone-50 pointer-events-none">
      <span class="text-stone-400 text-sm animate-pulse">🗺️ Karte lädt…</span>
    </div>
  {/if}
  {#if loadErr}
    <div class="absolute inset-0 flex items-center justify-center bg-stone-50">
      <span class="text-stone-400 text-sm">⚠️ {loadErr}</span>
    </div>
  {/if}

  {#if !loading && !loadErr}
    <div class="absolute bottom-2 left-2 flex gap-2.5 bg-white/90 backdrop-blur-sm
                border border-stone-200 rounded-lg px-3 py-1.5 text-xs shadow-sm pointer-events-none">
      <span class="flex items-center gap-1.5 text-stone-600">
        <span class="w-2.5 h-2.5 rounded-full" style="background:#2d6a4f;display:inline-block"></span>Besucht
      </span>
      <span class="flex items-center gap-1.5 text-stone-600">
        <span class="w-2.5 h-2.5 rounded-full" style="background:#2563eb;display:inline-block"></span>Geplant
      </span>
      <span class="flex items-center gap-1.5 text-stone-600">
        <span class="w-2.5 h-2.5 rounded-full" style="background:#c4622d;display:inline-block"></span>Wunschziel
      </span>
    </div>
  {/if}
</div>

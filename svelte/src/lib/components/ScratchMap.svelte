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

  function injectScript(src) {
    return new Promise((res, rej) => {
      // Bereits geladen?
      if (document.querySelector(`script[src="${src}"]`)) { res(); return; }
      const s = document.createElement('script');
      s.src = src;
      s.crossOrigin = 'anonymous';
      s.onload  = res;
      s.onerror = () => rej(new Error(`Konnte nicht laden: ${src}`));
      document.head.appendChild(s);
    });
  }

  function injectStyle(href) {
    return new Promise(res => {
      if (document.querySelector(`link[href="${href}"]`)) { res(); return; }
      const l = document.createElement('link');
      l.rel = 'stylesheet'; l.href = href; l.crossOrigin = 'anonymous';
      l.onload = res; l.onerror = res; // style-Fehler ignorieren
      document.head.appendChild(l);
    });
  }

  // Warten bis window.jsVectorMap verfügbar ist (max 3s)
  function waitForJsVM(ms = 3000) {
    return new Promise((res, rej) => {
      if (window.jsVectorMap) { res(); return; }
      const start = Date.now();
      const check = setInterval(() => {
        if (window.jsVectorMap) { clearInterval(check); res(); }
        else if (Date.now() - start > ms) { clearInterval(check); rej(new Error('jsVectorMap Timeout')); }
      }, 100);
    });
  }

  onMount(() => {
    let destroyed = false;
    const timer = setTimeout(async () => {
      if (!mapEl || destroyed) return;
      try {
        // Sequenziell laden: erst CSS, dann core, dann world map
        await injectStyle('https://cdn.jsdelivr.net/npm/jsvectormap@1.5.3/dist/css/jsvectormap.min.css');
        await injectScript('https://cdn.jsdelivr.net/npm/jsvectormap@1.5.3/dist/js/jsvectormap.min.js');
        await waitForJsVM(2000);
        await injectScript('https://cdn.jsdelivr.net/npm/jsvectormap@1.5.3/dist/maps/world.js');
        // Kurze Pause damit world.js sich registriert
        await new Promise(r => setTimeout(r, 150));

        if (destroyed) return;
        if (!window.jsVectorMap) throw new Error('jsVectorMap konnte nicht geladen werden');

        // ── Marker zusammenstellen ──────────────────────────────────────────
        const yr = String(selectedYear);

        const visited = journalTrips
          .filter(t => t.lat && t.lon && (t.start_date||'').slice(0,4) === yr)
          .map(t => ({ lat:+t.lat, lng:+t.lon, type:'visited',
            name: [t.location_name, t.country].filter(Boolean).join(', ') || `${t.lat},${t.lon}` }));

        const planned = plannedTrips
          .filter(t => t.lat && t.lon && (t.dateStart||t.date||'').slice(0,4) === yr)
          .map(t => ({ lat:+t.lat, lng:+t.lon, type:'planned', name: t.name }));

        const bucket = ($bucketlist??[])
          .filter(b => !b.done && b.lat && b.lon)
          .map(b => ({ lat:+b.lat, lng:+b.lon, type:'bucket',
            name: b.item + (b.dest ? ` (${b.dest})` : '') }));

        // Fallback auf Demos wenn keine echten Daten
        const vList = visited.length ? visited : DEMO_VISITED;
        const pList = planned.length ? planned : DEMO_PLANNED;
        const bList = bucket.length  ? bucket  : DEMO_BUCKET;

        const allMarkers = [...vList, ...pList, ...bList];
        const markers = allMarkers.map(m => ({
          name: m.name, coords: [m.lat, m.lng],
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
            initial: { r: 5, stroke: '#fff', strokeWidth: 1.5, fill: '#888' },
            hover:   { r: 7 },
          },
          onMarkerTooltipShow(evt, tooltip, idx) {
            tooltip.text(allMarkers[idx]?.name ?? '');
          },
        });

        // Marker-Farben per DOM setzen (zuverlässiger als style-Prop)
        setTimeout(() => {
          if (destroyed) return;
          const circles = mapEl.querySelectorAll('.jvm-markers circle, .jvm-marker');
          circles.forEach((c, i) => {
            const type = allMarkers[i]?.type ?? 'visited';
            c.setAttribute('fill', COLORS[type]);
          });
        }, 300);

        loading = false;
      } catch (e) {
        console.error('[ScratchMap]', e);
        loadErr = e.message || 'Karte konnte nicht geladen werden';
        loading = false;
      }
    }, 150);

    return () => {
      destroyed = true;
      clearTimeout(timer);
      try { map?.destroy?.(); } catch {}
      map = null;
    };
  });
</script>

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
      <span class="text-stone-400 text-xs text-center">Prüfe ob cdn.jsdelivr.net erreichbar ist</span>
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

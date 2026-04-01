<script>
  import { onMount } from 'svelte';
  import { bucketlist } from '$lib/stores.js';

  let { journalTrips = [] } = $props();

  // Container ist immer im DOM — kein conditional rendering
  let mapEl    = $state(null);
  let loading  = $state(true);
  let loadErr  = $state('');
  let map      = null;

  const demoVisited = [
    { lat: 47.81, lng: 13.05,   name: 'Salzburg' },
    { lat: 41.90, lng: 12.50,   name: 'Rom'      },
    { lat: 48.86, lng:  2.35,   name: 'Paris'    },
  ];
  const demoWish = [
    { lat: 35.68, lng: 139.65,  name: 'Tokyo'       },
    { lat: -13.16, lng: -72.54, name: 'Machu Picchu' },
  ];

  function seq(...fns) {
    return fns.reduce((p, fn) => p.then(fn), Promise.resolve());
  }

  function loadScript(src) {
    return new Promise((res, rej) => {
      if (window[src] || document.querySelector(`script[src="${src}"]`)) { setTimeout(res, 50); return; }
      const s = document.createElement('script');
      s.src = src; s.onload = () => setTimeout(res, 50); s.onerror = rej;
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
    // Kleines Timeout damit der Container wirklich im DOM und mit richtiger Größe ist
    const timer = setTimeout(async () => {
      if (!mapEl) { loadErr = 'Container nicht gefunden.'; loading = false; return; }

      try {
        await loadStyle('https://cdn.jsdelivr.net/npm/jsvectormap@1.5.3/dist/css/jsvectormap.min.css');
        await loadScript('https://cdn.jsdelivr.net/npm/jsvectormap@1.5.3/dist/js/jsvectormap.min.js');
        await loadScript('https://cdn.jsdelivr.net/npm/jsvectormap@1.5.3/dist/maps/world.js');

        if (!window.jsVectorMap) throw new Error('jsVectorMap nicht geladen');

        const visited = journalTrips
          .filter(t => t.lat && t.lon)
          .map(t => ({ lat: +t.lat, lng: +t.lon, name: [t.location_name, t.country].filter(Boolean).join(', ') || `${t.lat},${t.lon}` }));

        const wish = ($bucketlist ?? [])
          .filter(b => !b.done && b.lat && b.lon)
          .map(b => ({ lat: +b.lat, lng: +b.lon, name: b.item }));

        const vList = visited.length ? visited : demoVisited;
        const wList = wish.length    ? wish    : demoWish;

        const markers = [
          ...vList.map(m => ({ name: m.name, coords: [m.lat, m.lng] })),
          ...wList.map(m => ({ name: m.name, coords: [m.lat, m.lng] })),
        ];

        map = new window.jsVectorMap({
          selector: mapEl,
          map: 'world',
          zoomOnScroll: false,
          zoomButtons: true,
          backgroundColor: 'transparent',
          regionStyle: {
            initial: { fill: '#e8ddd0', stroke: '#d4c4b0', strokeWidth: 0.4 },
            hover:   { fill: '#c4622d', fillOpacity: 0.4 },
          },
          markers,
          markerStyle: {
            initial: { r: 5, stroke: '#fff', strokeWidth: 1.5 },
            hover:   { r: 7 },
          },
          // Besuchte grün, Wunschziele orange — per Index
          onMarkerTooltipShow(event, tooltip, index) {
            tooltip.text(markers[index]?.name ?? '');
          },
        });

        // Marker kolorieren nach Index
        setTimeout(() => {
          const circles = mapEl.querySelectorAll('circle.jvm-marker, .jvm-marker circle, .jvm-markers circle');
          circles.forEach((c, i) => {
            c.setAttribute('fill', i < vList.length ? '#2d6a4f' : '#c4622d');
          });
        }, 200);

        loading = false;
      } catch (e) {
        console.error('[ScratchMap]', e);
        loadErr = 'Karte konnte nicht geladen werden.';
        loading = false;
      }
    }, 100);

    return () => {
      clearTimeout(timer);
      try { map?.destroy?.(); } catch {}
      map = null;
    };
  });
</script>

<!-- Container ist IMMER im DOM, nie conditional -->
<div class="relative w-full rounded-xl overflow-hidden border border-stone-200 bg-stone-50" style="height:320px">

  <!-- Karte — immer sichtbar, Overlay liegt obendrüber -->
  <div bind:this={mapEl} class="w-full h-full" style="min-height:320px"></div>

  <!-- Lade-Overlay -->
  {#if loading && !loadErr}
    <div class="absolute inset-0 flex items-center justify-center bg-stone-50 pointer-events-none">
      <span class="text-stone-400 text-sm animate-pulse">🗺️ Karte lädt…</span>
    </div>
  {/if}

  <!-- Fehler -->
  {#if loadErr}
    <div class="absolute inset-0 flex items-center justify-center bg-stone-50">
      <span class="text-stone-400 text-sm">⚠️ {loadErr}</span>
    </div>
  {/if}

  <!-- Legende -->
  {#if !loading}
    <div class="absolute bottom-2 left-2 flex gap-3 bg-white/90 backdrop-blur-sm
                border border-stone-200 rounded-lg px-3 py-1.5 text-xs shadow-sm pointer-events-none">
      <span class="flex items-center gap-1.5 text-stone-600">
        <span class="w-2.5 h-2.5 rounded-full inline-block" style="background:#2d6a4f"></span>Besucht
      </span>
      <span class="flex items-center gap-1.5 text-stone-600">
        <span class="w-2.5 h-2.5 rounded-full inline-block" style="background:#c4622d"></span>Wunschziel
      </span>
    </div>
  {/if}
</div>

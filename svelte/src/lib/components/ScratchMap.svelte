<script>
  import { onMount } from 'svelte';
  import { bucketlist } from '$lib/stores.js';

  let { journalTrips = [] } = $props();

  let mapContainer = $state(null);
  let mapReady     = $state(false);
  let map          = null;

  const demoVisited = [
    { lat: 47.8095, lng: 13.0550, name: 'Salzburg, Österreich', type: 'visited' },
    { lat: 41.9028, lng: 12.4964, name: 'Rom, Italien',         type: 'visited' },
    { lat: 48.8566, lng:  2.3522, name: 'Paris, Frankreich',    type: 'visited' },
  ];
  const demoWish = [
    { lat: 35.6762, lng: 139.6503, name: 'Tokyo, Japan',        type: 'wish' },
    { lat: -13.163, lng: -72.5450, name: 'Machu Picchu, Peru',  type: 'wish' },
  ];

  function svgPin(color, char) {
    const s = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 32">` +
      `<path d="M12 0C5.37 0 0 5.37 0 12c0 8.5 12 20 12 20S24 20.5 24 12C24 5.37 18.63 0 12 0z"` +
      ` fill="${color}" stroke="white" stroke-width="1.5"/>` +
      `<text x="12" y="15" text-anchor="middle" dominant-baseline="middle"` +
      ` font-size="11" fill="white" font-family="sans-serif">${char}</text></svg>`;
    return 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(s)));
  }

  function loadScript(src) {
    return new Promise((res, rej) => {
      if (document.querySelector(`script[src="${src}"]`)) { res(); return; }
      const el = document.createElement('script');
      el.src = src; el.onload = res; el.onerror = rej;
      document.head.appendChild(el);
    });
  }
  function loadStyle(href) {
    return new Promise(res => {
      if (document.querySelector(`link[href="${href}"]`)) { res(); return; }
      const el = document.createElement('link');
      el.rel = 'stylesheet'; el.href = href; el.onload = res;
      document.head.appendChild(el);
    });
  }

  onMount(async () => {
    if (!mapContainer) return;

    // CSS first, then jsvectormap core, then world map (depends on window.jsVectorMap)
    await loadStyle('https://cdn.jsdelivr.net/npm/jsvectormap@1.5.3/dist/css/jsvectormap.min.css');
    await loadScript('https://cdn.jsdelivr.net/npm/jsvectormap@1.5.3/dist/js/jsvectormap.min.js');
    await loadScript('https://cdn.jsdelivr.net/npm/jsvectormap@1.5.3/dist/maps/world.js');

    const visited = journalTrips.filter(t => t.lat && t.lon).map(t => ({
      lat: parseFloat(t.lat), lng: parseFloat(t.lon),
      name: [t.location_name, t.country].filter(Boolean).join(', ') || `${t.lat},${t.lon}`,
      type: 'visited',
    }));
    const wish = $bucketlist.filter(b => !b.done && b.lat).map(b => ({
      lat: b.lat, lng: b.lon,
      name: b.item + (b.dest ? ` (${b.dest})` : ''),
      type: 'wish',
    }));

    const allVisited = visited.length ? visited : demoVisited;
    const allWish    = wish.length    ? wish    : demoWish;

    const markers = [
      ...allVisited.map(m => ({ name: m.name, coords: [m.lat, m.lng], style: { fill: '#2d6a4f', stroke: '#fff', r: 6 } })),
      ...allWish.map(m    => ({ name: m.name, coords: [m.lat, m.lng], style: { fill: '#c4622d', stroke: '#fff', r: 6 } })),
    ];

    map = new window.jsVectorMap({
      selector: mapContainer,
      map: 'world',
      zoomOnScroll: false,
      zoomButtons: true,
      backgroundColor: 'transparent',
      regionStyle: {
        initial: { fill: '#e8ddd0', stroke: '#d4c4b0', strokeWidth: 0.4 },
        hover:   { fill: '#c4622d', fillOpacity: 0.5 },
      },
      markers,
      markerStyle: {
        initial: { fill: '#c4622d', stroke: '#fff', strokeWidth: 1.5, r: 6 },
        hover:   { fill: '#a03820', r: 7 },
      },
      markerLabelStyle: {
        initial: { fontFamily: 'DM Sans, sans-serif', fontSize: 10, fill: '#555' },
      },
    });

    // SVG-Pin-Icons über DOM nachrüsten
    setTimeout(() => {
      const els = mapContainer.querySelectorAll('circle.jvm-marker');
      els.forEach((el, i) => {
        const type  = i < allVisited.length ? 'visited' : 'wish';
        const color = type === 'visited' ? '#2d6a4f' : '#c4622d';
        const char  = type === 'visited' ? '✓' : '★';
        const img   = document.createElement('img');
        img.src     = svgPin(color, char);
        const cx    = parseFloat(el.getAttribute('cx') || 0);
        const cy    = parseFloat(el.getAttribute('cy') || 0);
        img.style.cssText = `position:absolute;left:${cx}px;top:${cy}px;` +
          `transform:translate(-50%,-100%);width:22px;height:30px;` +
          `pointer-events:none;filter:drop-shadow(0 1px 2px rgba(0,0,0,.4))`;
        mapContainer.querySelector('svg')?.parentElement?.appendChild(img);
      });
    }, 400);

    mapReady = true;
    return () => { try { map?.destroy?.(); } catch {} map = null; };
  });
</script>

<div class="relative w-full rounded-xl overflow-hidden border border-stone-200 bg-stone-50"
     style="height:320px">
  {#if !mapReady}
    <div class="absolute inset-0 flex items-center justify-center">
      <div class="text-stone-400 text-sm animate-pulse">🗺️ Karte lädt…</div>
    </div>
  {/if}
  <div bind:this={mapContainer} class="w-full h-full"></div>

  <!-- Legende -->
  <div class="absolute bottom-2 left-2 flex gap-3 bg-white/90 backdrop-blur-sm
              border border-stone-200 rounded-lg px-3 py-1.5 text-xs shadow-sm pointer-events-none">
    <span class="flex items-center gap-1.5 text-stone-600">
      <span class="w-2.5 h-2.5 rounded-full inline-block" style="background:#2d6a4f"></span>Besucht
    </span>
    <span class="flex items-center gap-1.5 text-stone-600">
      <span class="w-2.5 h-2.5 rounded-full inline-block" style="background:#c4622d"></span>Wunschziel
    </span>
  </div>
</div>

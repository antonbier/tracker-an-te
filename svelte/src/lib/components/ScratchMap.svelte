<script>
  import { onMount, onDestroy } from 'svelte';
  import { bucketlist } from '$lib/stores.js';

  let { journalTrips = [] } = $props();

  let mapContainer = $state(null);
  let map = null;

  // Visited: echte Dawarich-Trips → lat/lon
  const visitedMarkers = $derived(
    journalTrips
      .filter(t => t.lat && t.lon)
      .map(t => ({
        lat: parseFloat(t.lat),
        lng: parseFloat(t.lon),
        name: [t.location_name, t.country].filter(Boolean).join(', ') || `${t.lat}, ${t.lon}`,
        type: 'visited',
      }))
  );

  // Wunschziele: Bucket List mit coords (dest als Freitext → demo coords als Fallback)
  const wishMarkers = $derived(
    $bucketlist
      .filter(b => !b.done && (b.lat || b.demoLat))
      .map(b => ({
        lat:  b.lat  ?? b.demoLat,
        lng:  b.lon  ?? b.demoLon,
        name: b.item + (b.dest ? ` (${b.dest})` : ''),
        type: 'wish',
      }))
  );

  // Demo-Markers damit die Karte nicht leer bleibt beim ersten Laden
  const demoVisited = [
    { lat: 47.8095, lng: 13.0550, name: 'Salzburg, Österreich',   type: 'visited' },
    { lat: 41.9028, lng: 12.4964, name: 'Rom, Italien',            type: 'visited' },
    { lat: 48.8566, lng: 2.3522,  name: 'Paris, Frankreich',       type: 'visited' },
  ];
  const demoWish = [
    { lat: 35.6762, lng: 139.6503, name: 'Tokyo, Japan',      type: 'wish' },
    { lat: -13.1631, lng: -72.5450, name: 'Machu Picchu, Peru', type: 'wish' },
  ];

  const allVisited = $derived(visitedMarkers.length ? visitedMarkers : demoVisited);
  const allWish    = $derived(wishMarkers.length    ? wishMarkers    : demoWish);

  function svgPin(color, inner) {
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 32" width="24" height="32">
      <path d="M12 0C5.373 0 0 5.373 0 12c0 8.5 12 20 12 20S24 20.5 24 12C24 5.373 18.627 0 12 0z"
        fill="${color}" stroke="white" stroke-width="1.5"/>
      <text x="12" y="16" text-anchor="middle" dominant-baseline="middle"
        font-size="11" fill="white">${inner}</text>
    </svg>`;
  }

  function markerToDataUrl(svgStr) {
    return 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgStr)));
  }

  onMount(async () => {
    if (!mapContainer) return;

    // jsvectormap dynamisch laden (CDN)
    await Promise.all([
      loadScript('https://cdn.jsdelivr.net/npm/jsvectormap@1.5.3/dist/js/jsvectormap.min.js'),
      loadScript('https://cdn.jsdelivr.net/npm/jsvectormap@1.5.3/dist/maps/world.js'),
      loadStyle('https://cdn.jsdelivr.net/npm/jsvectormap@1.5.3/dist/css/jsvectormap.min.css'),
    ]);

    // Marker-Objekte
    const markers = [
      ...allVisited.map(m => ({ name: m.name, coords: [m.lat, m.lng], _type: 'visited' })),
      ...allWish.map(m    => ({ name: m.name, coords: [m.lat, m.lng], _type: 'wish' })),
    ];

    const markerStyle = {
      initial: { fill: '#c4622d', stroke: '#fff', r: 5 },
    };

    map = new window.jsVectorMap({
      selector: mapContainer,
      map: 'world',
      zoomOnScroll: true,
      zoomButtons: true,
      backgroundColor: 'transparent',
      regionStyle: {
        initial:  { fill: '#e8ddd0', stroke: '#d4c4b0', strokeWidth: 0.5 },
        hover:    { fill: '#d4722d', fillOpacity: 0.6 },
        selected: { fill: '#c4622d' },
      },
      markers,
      markerStyle,
      // Custom marker rendering via labels
      labels: {
        markers: {
          render(marker, index) {
            return marker.name;
          },
        },
      },
    });

    // Custom SVG-Pins über DOM nachrüsten
    setTimeout(() => {
      const markerEls = mapContainer.querySelectorAll('.jvm-marker');
      markerEls.forEach((el, i) => {
        const type  = markers[i]?._type;
        const color = type === 'visited' ? '#2d6a4f' : '#c4622d';
        const icon  = type === 'visited' ? '✓' : '★';
        const svg   = svgPin(color, icon);
        const img   = document.createElement('img');
        img.src     = markerToDataUrl(svg);
        img.style.cssText = 'position:absolute;transform:translate(-50%,-100%);width:24px;height:32px;pointer-events:none;filter:drop-shadow(0 1px 3px rgba(0,0,0,.35))';
        const parent = el.parentElement;
        if (parent) parent.appendChild(img);
      });
    }, 300);

    return () => { map?.destroy?.(); map = null; };
  });

  function loadScript(src) {
    return new Promise((res, rej) => {
      if (document.querySelector(`script[src="${src}"]`)) { res(); return; }
      const s = document.createElement('script'); s.src = src; s.onload = res; s.onerror = rej;
      document.head.appendChild(s);
    });
  }
  function loadStyle(href) {
    return new Promise((res) => {
      if (document.querySelector(`link[href="${href}"]`)) { res(); return; }
      const l = document.createElement('link'); l.rel = 'stylesheet'; l.href = href; l.onload = res;
      document.head.appendChild(l);
    });
  }
</script>

<div class="relative w-full rounded-xl overflow-hidden border border-stone-200 bg-stone-50"
     style="height: 340px;">
  <div bind:this={mapContainer} class="w-full h-full"></div>

  <!-- Legende -->
  <div class="absolute bottom-3 left-3 flex gap-3 bg-white/90 backdrop-blur-sm
              border border-stone-200 rounded-lg px-3 py-2 text-xs shadow-sm">
    <span class="flex items-center gap-1.5">
      <span class="inline-block w-3 h-3 rounded-full" style="background:#2d6a4f"></span>
      Besucht
    </span>
    <span class="flex items-center gap-1.5">
      <span class="inline-block w-3 h-3 rounded-full" style="background:#c4622d"></span>
      Wunschziel
    </span>
  </div>
</div>

<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';
  import { get } from 'svelte/store';
  import { apiUrl } from '$lib/stores.js';
  import { toast } from '$lib/toast.js';
  import { t } from '$lib/i18n.js';

  import CategoryTabs       from '$lib/components/priceradar/CategoryTabs.svelte';
  import FlightSearchForm   from '$lib/components/priceradar/FlightSearchForm.svelte';
  import HotelSearchForm    from '$lib/components/priceradar/HotelSearchForm.svelte';
  import CampingSearchForm  from '$lib/components/priceradar/CampingSearchForm.svelte';
  import SearchResults      from '$lib/components/priceradar/SearchResults.svelte';
  import TrackerGrid        from '$lib/components/priceradar/TrackerGrid.svelte';

  import { TRACKER_TYPES_BY_CAT } from '$lib/components/priceradar/constants.js';

  // ── Category state ────────────────────────────────────────────────────────
  let activeCategory = $state('flights');

  // ── Search state ──────────────────────────────────────────────────────────
  let searching         = $state(false);
  let searchResults     = $state([]);
  let savingTracker     = $state(null);

  // ── Tracker state ─────────────────────────────────────────────────────────
  let allTrackers     = $state([]);
  let trackersLoading = $state(true);
  let isRefreshing    = $state(false);
  let chartState      = $state({});
  let wishState       = $state({});
  let stopsOpen       = $state({});

  const visibleTrackers = $derived(
    allTrackers.filter(tr => (TRACKER_TYPES_BY_CAT[activeCategory] || []).includes(tr._type))
  );

  // ── Search ────────────────────────────────────────────────────────────────
  async function doSearch(payload) {
    if (!get(apiUrl)) { toast(get(t)('radarNoBackend'), 'warning'); return; }
    searching = true;
    searchResults = [];
    const endpointMap = { flights: '/api/search/flights', hotels: '/api/search/hotels', camping: '/api/search/camping' };
    try {
      const res = await api(endpointMap[activeCategory], { method: 'POST', body: JSON.stringify(payload) });
      searchResults = res.results || [];
      if (res.missing_api_keys?.length > 0) {
        toast(`⚠️ API Key für ${res.missing_api_keys.join(', ')} fehlt in den Einstellungen.`, 'error');
      }
      if (searchResults.length === 0 && !res.missing_api_keys?.length) toast(get(t)('radarNoResults'), 'warning');
    } catch (e) {
      const detail = e.detail || {};
      if (detail.error === 'missing_api_key') {
        toast(`⚠️ API Key für ${detail.provider} fehlt in den Einstellungen.`, 'error');
      } else {
        toast(e.message || 'Suche fehlgeschlagen', 'error');
      }
    }
    searching = false;
  }

  // ── Save as tracker ───────────────────────────────────────────────────────
  async function saveAsTracker(result) {
    if (!get(apiUrl)) { toast(get(t)('radarNoBackend'), 'warning'); return; }
    savingTracker = result.id;
    try {
      if (result._test_mode) {
        toast('🧪 Testpreise können nicht als Tracker gespeichert werden.', 'warning');
        savingTracker = null;
        return;
      }
      const d = result.detail || {};
      let endpoint, payload;

      if (result._tracker_type === 'flight') {
        endpoint = '/api/trackers';
        const bagList = [];
        if (d.baggage_10kg > 0) { for (let i=0; i<d.baggage_10kg; i++) bagList.push({ type: '10kg', per_person: false }); }
        else if (d.baggage === '10kg') bagList.push({ type: '10kg', per_person: true });
        if (d.baggage_20kg > 0) { for (let i=0; i<d.baggage_20kg; i++) bagList.push({ type: '20kg', per_person: false }); }
        else if (d.baggage === '20kg' && !d.baggage_10kg) bagList.push({ type: '20kg', per_person: true });
        if (d.baggage_23kg > 0) { for (let i=0; i<d.baggage_23kg; i++) bagList.push({ type: '23kg', per_person: false }); }
        payload = {
          origin:        d.origin,
          destination:   d.destination,
          outbound_date: d.outbound_date,
          return_date:   d.return_date || null,
          adults:        d.adults || 1,
          children:      d.children || 0,
          baggage:       bagList,
          seat_cost:     d.seat_cost ?? (d.seat ? 8.99 : 0.0),
        };
      } else if (result._tracker_type === 'google_flight') {
        endpoint = '/api/google-flights';
        payload = {
          origin:                    d.origin,
          destination:               d.destination,
          outbound_date:             d.outbound_date,
          return_date:               d.return_date || null,
          adults:                    d.adults || 1,
          children:                  d.children || 0,
          baggage:                   d.baggage || 'none',
          baggage_10kg:              d.baggage_10kg || 0,
          baggage_20kg:              d.baggage_20kg || 0,
          baggage_23kg:              d.baggage_23kg || 0,
          seat:                      d.seat || false,
          seat_cost:                 d.seat_cost || 0.0,
          initial_price:             result.price || null,
          initial_airline:           d.airline || null,
          initial_dep_time:          d.departure_time || null,
          initial_arr_time:          d.arrival_time || null,
          initial_duration:          d.duration_min || null,
          initial_stops:             d.stops ?? 0,
          initial_layover_airports:  d.layover_airports || [],
          initial_layover_durations: d.layover_durations || [],
        };
      } else if (result._tracker_type === 'camping') {
        endpoint = '/api/accommodations/homair';
        payload = {
          region:             d.region || d.destination || '',
          accommodation_type: d.accommodation_type || 'mobilheim',
          checkin_date:       d.checkin_date,
          checkout_date:      d.checkout_date,
          adults:             d.adults || 2,
          children:           d.children || 0,
          bedrooms:           d.bedrooms || '1',
          aircon:             d.aircon  || false,
          pets:               d.pets   || false,
          covered_terrace:    d.covered_terrace || false,
          campsite_name:      d.campsite_name || result.title || null,
          initial_price:      result.price || null,
          final_cleaning:     d.final_cleaning || false,
        };
      } else if (result._tracker_type === 'hotel') {
        endpoint = '/api/accommodations/booking';
        payload = {
          destination:   d.destination,
          checkin_date:  d.checkin_date,
          checkout_date: d.checkout_date,
          adults:        d.adults || 2,
          rooms:         d.rooms  || 1,
          source:        d.source || 'booking',
          hotel_name:    d.hotel_name || result.title || null,
          initial_price: result.price || null,
        };
      } else {
        toast('Unbekannter Tracker-Typ', 'error');
        savingTracker = null;
        return;
      }

      await api(endpoint, { method: 'POST', body: JSON.stringify(payload) });
      toast(get(t)('radarTrackerSaved'), 'success');
      await loadAllTrackers();
    } catch (e) {
      toast(e.message, 'error');
    }
    savingTracker = null;
  }

  // ── Tracker CRUD ──────────────────────────────────────────────────────────
  async function loadAllTrackers() {
    if (!get(apiUrl)) { trackersLoading = false; return; }
    trackersLoading = true;
    try {
      const [ry, gf, hm, bk] = await Promise.allSettled([
        api('/api/trackers'),
        api('/api/google-flights'),
        api('/api/accommodations/homair'),
        api('/api/accommodations/booking'),
      ]);
      allTrackers = [
        ...(ry.status === 'fulfilled' ? (ry.value || []).map(tr => ({ ...tr, _type: 'flight',        _table: 'trackers' }))         : []),
        ...(gf.status === 'fulfilled' ? (gf.value || []).map(tr => ({ ...tr, _type: 'google_flight', _table: 'gf_trackers' }))      : []),
        ...(hm.status === 'fulfilled' ? (hm.value || []).map(tr => ({ ...tr, _type: 'camping',       _table: 'homair_trackers' }))  : []),
        ...(bk.status === 'fulfilled' ? (bk.value || []).map(tr => ({ ...tr, _type: 'hotel',         _table: 'booking_trackers' })) : []),
      ];
    } catch {}
    trackersLoading = false;
  }

  async function deleteTracker(tracker) {
    if (!confirm(get(t)('delete') + '?')) return;
    const endpoints = {
      flight:        `/api/trackers/${tracker.id}`,
      google_flight: `/api/google-flights/${tracker.id}`,
      camping:       `/api/accommodations/homair/${tracker.id}`,
      hotel:         `/api/accommodations/booking/${tracker.id}`,
    };
    try {
      await api(endpoints[tracker._type], { method: 'DELETE' });
      await loadAllTrackers();
    } catch (e) { toast(e.message, 'error'); }
  }

  async function scrapeTracker(tracker) {
    toast(get(t)('radarUpdatePrice') + '…', 'warning');
    const endpoints = {
      flight:        `/api/trackers/${tracker.id}/scrape`,
      google_flight: `/api/google-flights/${tracker.id}/scrape`,
      camping:       `/api/accommodations/homair/${tracker.id}/scrape`,
      hotel:         `/api/accommodations/booking/${tracker.id}/scrape`,
    };
    try {
      await api(endpoints[tracker._type], { method: 'POST' });
      toast(get(t)('radarUpdatePrice') + ' ✓', 'success');
      await loadAllTrackers();
    } catch (e) { toast(e.message, 'error'); }
  }

  async function saveWishPrice(type, id, table, newPrice) {
    const key = `${type}-${id}`;
    wishState[key] = { ...wishState[key], saving: true };
    try {
      await api(`/api/prices/wish/${table}/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ wish_price: newPrice === '' ? null : parseFloat(newPrice) }),
      });
      toast(get(t)('radarWishPrice') + ' ✓', 'success');
      wishState[key] = { editing: false, value: newPrice, saving: false };
      await loadAllTrackers();
    } catch (e) {
      toast(e.message, 'error');
      wishState[key] = { ...wishState[key], saving: false };
    }
  }

  async function toggleChart(type, id) {
    const key = `${type}-${id}`;
    if (!chartState[key]) chartState[key] = { open: false, history: [], loading: false };
    chartState[key] = { ...chartState[key], open: !chartState[key].open };
    if (chartState[key].open && chartState[key].history.length === 0) {
      chartState[key] = { ...chartState[key], loading: true };
      try {
        const res = await api(`/api/prices/history/${type}/${id}`);
        chartState[key] = { ...chartState[key], history: res.history || [] };
      } catch { chartState[key] = { ...chartState[key], history: [] }; }
      chartState[key] = { ...chartState[key], loading: false };
    }
  }

  async function refreshAllTrackers() {
    if (isRefreshing) return;
    isRefreshing = true;
    try {
      await api('/api/scheduler/run', { method: 'POST' });
      toast('⏳ Alle Tracker werden aktualisiert… dauert 1–2 Min.', 'warning');
      setTimeout(async () => {
        await loadAllTrackers();
        isRefreshing = false;
      }, 90000);
    } catch (e) {
      toast(e.message, 'error');
      isRefreshing = false;
    }
  }

  onMount(() => { loadAllTrackers(); });
</script>

<!-- ── Page ── -->
<div class="space-y-5">

  <CategoryTabs
    bind:activeCategory
    oncategorychange={() => { searchResults = []; }}
  />

  <!-- Search forms -->
  {#if activeCategory === 'flights'}
    <FlightSearchForm {searching} onsearch={doSearch} />
  {:else if activeCategory === 'hotels'}
    <HotelSearchForm {searching} onsearch={doSearch} />
  {:else if activeCategory === 'camping'}
    <CampingSearchForm {searching} onsearch={doSearch} />
  {:else if activeCategory === 'rentals'}
    <div class="rounded-xl p-8 border text-center space-y-3" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <div class="text-4xl">🚗</div>
      <h2 class="text-lg font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">{$t('radarRentals')}</h2>
      <span class="inline-block px-3 py-1 rounded-full text-xs font-semibold"
        style="background:rgba(196,98,45,.12);color:var(--ws-accent)">
        🔜 {$t('radarComingSoon')}
      </span>
      <p class="text-xs" style="color:var(--ws-muted)">Mietwagen-Vergleich von mehreren Anbietern — demnächst verfügbar.</p>
    </div>
  {/if}

  <!-- Search results -->
  <SearchResults
    {searching}
    results={searchResults}
    {savingTracker}
    onsavetracker={saveAsTracker}
  />

  <!-- Active trackers -->
  <TrackerGrid
    trackers={visibleTrackers}
    allCount={allTrackers.length}
    loading={trackersLoading}
    {isRefreshing}
    {activeCategory}
    bind:chartState
    bind:wishState
    bind:stopsOpen
    onrefreshall={refreshAllTrackers}
    ondelete={deleteTracker}
    onscrape={scrapeTracker}
    onwishsave={saveWishPrice}
    ontogglerchart={toggleChart}
  />

</div>

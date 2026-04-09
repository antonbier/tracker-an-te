<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';
  import { apiUrl } from '$lib/stores.js';
  import { toast } from '$lib/toast.js';
  import { t } from '$lib/i18n.js';

  // ── Category tabs ─────────────────────────────────────────────────────────
  let activeCategory = $state('flights');

  const categories = $derived([
    { id: 'flights',  label: '✈️ ' + $t('radarFlights')  },
    { id: 'hotels',   label: '🏨 ' + $t('radarHotels')   },
    { id: 'camping',  label: '⛺ ' + $t('radarCamping')  },
    { id: 'rentals',  label: '🚗 ' + $t('radarRentals')  },
  ]);

  // ── Shared helpers ────────────────────────────────────────────────────────
  const today = new Date();
  const d30   = new Date(today); d30.setDate(d30.getDate() + 30);
  const d37   = new Date(today); d37.setDate(d37.getDate() + 37);
  function fmt(d) { return d.toISOString().slice(0, 10); }
  // Lokalisiert YYYY-MM-DD nach konfigurierbarem Format (global store)
  function fmtDate(iso) {
    if (!iso) return '–';
    const parts = String(iso).slice(0, 10).split('-');
    if (parts.length !== 3) return iso;
    const [yyyy, mm, dd] = parts;
    // Read date_format from localStorage (set by Settings)
    const fmt = typeof localStorage !== 'undefined' ? (localStorage.getItem('ws-date-format') || 'DD.MM.YYYY') : 'DD.MM.YYYY';
    if (fmt === 'MM/DD/YYYY') return `${mm}/${dd}/${yyyy}`;
    if (fmt === 'YYYY-MM-DD') return `${yyyy}-${mm}-${dd}`;
    return `${dd}.${mm}.${yyyy}`; // default DD.MM.YYYY
  }
  // Lokalisiert Datum-Range
  function fmtRange(from, to) {
    return to ? `${fmtDate(from)} – ${fmtDate(to)}` : fmtDate(from);
  }
  const inputCls   = 'w-full px-3 py-2 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ws-accent)]';
  const inputStyle = 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)';
  const labelCls   = 'block text-xs font-bold uppercase tracking-wider mb-1';

  // ── Autocomplete (local, no external API) ─────────────────────────────────
  // Top airports with IATA + city name for filtering
  const AIRPORTS = [
    { iata: 'VIE', city: 'Wien', country: 'AT' },
    { iata: 'MUC', city: 'München', country: 'DE' },
    { iata: 'FRA', city: 'Frankfurt', country: 'DE' },
    { iata: 'BER', city: 'Berlin', country: 'DE' },
    { iata: 'HAM', city: 'Hamburg', country: 'DE' },
    { iata: 'STR', city: 'Stuttgart', country: 'DE' },
    { iata: 'DUS', city: 'Düsseldorf', country: 'DE' },
    { iata: 'CGN', city: 'Köln', country: 'DE' },
    { iata: 'NUE', city: 'Nürnberg', country: 'DE' },
    { iata: 'ZRH', city: 'Zürich', country: 'CH' },
    { iata: 'GVA', city: 'Genf', country: 'CH' },
    { iata: 'BSL', city: 'Basel', country: 'CH' },
    { iata: 'BGY', city: 'Bergamo / Mailand', country: 'IT' },
    { iata: 'MXP', city: 'Mailand Malpensa', country: 'IT' },
    { iata: 'FCO', city: 'Rom', country: 'IT' },
    { iata: 'VCE', city: 'Venedig', country: 'IT' },
    { iata: 'NAP', city: 'Neapel', country: 'IT' },
    { iata: 'BLQ', city: 'Bologna', country: 'IT' },
    { iata: 'PMO', city: 'Palermo', country: 'IT' },
    { iata: 'CAG', city: 'Cagliari', country: 'IT' },
    { iata: 'TRN', city: 'Turin', country: 'IT' },
    { iata: 'FLR', city: 'Florenz', country: 'IT' },
    { iata: 'LIN', city: 'Mailand Linate', country: 'IT' },
    { iata: 'LNZ', city: 'Linz', country: 'AT' },
    { iata: 'GRZ', city: 'Graz', country: 'AT' },
    { iata: 'SZG', city: 'Salzburg', country: 'AT' },
    { iata: 'INN', city: 'Innsbruck', country: 'AT' },
    { iata: 'LHR', city: 'London Heathrow', country: 'GB' },
    { iata: 'LGW', city: 'London Gatwick', country: 'GB' },
    { iata: 'STN', city: 'London Stansted', country: 'GB' },
    { iata: 'MAN', city: 'Manchester', country: 'GB' },
    { iata: 'DUB', city: 'Dublin', country: 'IE' },
    { iata: 'BCN', city: 'Barcelona', country: 'ES' },
    { iata: 'MAD', city: 'Madrid', country: 'ES' },
    { iata: 'PMI', city: 'Palma de Mallorca', country: 'ES' },
    { iata: 'ALC', city: 'Alicante', country: 'ES' },
    { iata: 'AGP', city: 'Málaga', country: 'ES' },
    { iata: 'CDG', city: 'Paris Charles de Gaulle', country: 'FR' },
    { iata: 'ORY', city: 'Paris Orly', country: 'FR' },
    { iata: 'NCE', city: 'Nizza', country: 'FR' },
    { iata: 'MRS', city: 'Marseille', country: 'FR' },
    { iata: 'AMS', city: 'Amsterdam', country: 'NL' },
    { iata: 'BRU', city: 'Brüssel', country: 'BE' },
    { iata: 'CPH', city: 'Kopenhagen', country: 'DK' },
    { iata: 'OSL', city: 'Oslo', country: 'NO' },
    { iata: 'ARN', city: 'Stockholm', country: 'SE' },
    { iata: 'HEL', city: 'Helsinki', country: 'FI' },
    { iata: 'ATH', city: 'Athen', country: 'GR' },
    { iata: 'SKG', city: 'Thessaloniki', country: 'GR' },
    { iata: 'HER', city: 'Heraklion (Kreta)', country: 'GR' },
    { iata: 'CFU', city: 'Korfu', country: 'GR' },
    { iata: 'RHO', city: 'Rhodos', country: 'GR' },
    { iata: 'IST', city: 'Istanbul', country: 'TR' },
    { iata: 'SAW', city: 'Istanbul Sabiha', country: 'TR' },
    { iata: 'AYT', city: 'Antalya', country: 'TR' },
    { iata: 'OPO', city: 'Porto', country: 'PT' },
    { iata: 'LIS', city: 'Lissabon', country: 'PT' },
    { iata: 'FAO', city: 'Faro (Algarve)', country: 'PT' },
    { iata: 'PRG', city: 'Prag', country: 'CZ' },
    { iata: 'BUD', city: 'Budapest', country: 'HU' },
    { iata: 'WAW', city: 'Warschau', country: 'PL' },
    { iata: 'KRK', city: 'Krakau', country: 'PL' },
    { iata: 'OTP', city: 'Bukarest', country: 'RO' },
    { iata: 'SOF', city: 'Sofia', country: 'BG' },
    { iata: 'ZAG', city: 'Zagreb', country: 'HR' },
    { iata: 'SPU', city: 'Split', country: 'HR' },
    { iata: 'DBV', city: 'Dubrovnik', country: 'HR' },
    { iata: 'TIA', city: 'Tirana', country: 'AL' },
    { iata: 'KIV', city: 'Chisinau', country: 'MD' },
    { iata: 'JFK', city: 'New York JFK', country: 'US' },
    { iata: 'EWR', city: 'New York Newark', country: 'US' },
    { iata: 'LAX', city: 'Los Angeles', country: 'US' },
    { iata: 'ORD', city: 'Chicago', country: 'US' },
    { iata: 'MIA', city: 'Miami', country: 'US' },
    { iata: 'DXB', city: 'Dubai', country: 'AE' },
    { iata: 'DOH', city: 'Doha', country: 'QA' },
    { iata: 'BKK', city: 'Bangkok', country: 'TH' },
    { iata: 'SIN', city: 'Singapur', country: 'SG' },
    { iata: 'HKG', city: 'Hongkong', country: 'HK' },
    { iata: 'NRT', city: 'Tokio Narita', country: 'JP' },
    { iata: 'KIX', city: 'Osaka', country: 'JP' },
    { iata: 'SYD', city: 'Sydney', country: 'AU' },
    { iata: 'MEL', city: 'Melbourne', country: 'AU' },
    { iata: 'GRU', city: 'São Paulo', country: 'BR' },
    { iata: 'EZE', city: 'Buenos Aires', country: 'AR' },
    { iata: 'CMN', city: 'Casablanca', country: 'MA' },
    { iata: 'TUN', city: 'Tunis', country: 'TN' },
    { iata: 'CAI', city: 'Kairo', country: 'EG' },
    { iata: 'HRG', city: 'Hurghada', country: 'EG' },
    { iata: 'SSH', city: 'Sharm el-Sheikh', country: 'EG' },
  ];

  // Simple destinations for hotels/camping autocomplete
  const DESTINATIONS = [
    'Wien', 'München', 'Berlin', 'Hamburg', 'Frankfurt', 'Stuttgart', 'Köln', 'Düsseldorf',
    'Zürich', 'Genf', 'Basel', 'Bern',
    'Mailand', 'Rom', 'Venedig', 'Florenz', 'Neapel', 'Bologna', 'Turin', 'Palermo', 'Sardegna',
    'Paris', 'Nizza', 'Marseille', 'Lyon', 'Bordeaux', 'Strasbourg',
    'Barcelona', 'Madrid', 'Palma de Mallorca', 'Valencia', 'Sevilla', 'Málaga', 'Ibiza',
    'London', 'Manchester', 'Edinburgh', 'Dublin',
    'Amsterdam', 'Brüssel', 'Kopenhagen', 'Stockholm', 'Oslo', 'Helsinki',
    'Prag', 'Budapest', 'Warschau', 'Krakau', 'Bukarest', 'Bratislava',
    'Athen', 'Thessaloniki', 'Santorini', 'Mykonos', 'Kreta', 'Rhodos', 'Korfu',
    'Istanbul', 'Antalya', 'Bodrum', 'Kappadokien',
    'Lissabon', 'Porto', 'Faro / Algarve', 'Madeira',
    'Dubrovnik', 'Split', 'Zadar', 'Zagreb', 'Boka Kotorska',
    'Côte d\'Azur', 'Languedoc', 'Provence', 'Bretagne', 'Normandie',
    'Toskana', 'Venetien', 'Ligurien', 'Sizilien', 'Sardinien', 'Kalabrien', 'Apulien',
    'Katalonien', 'Costa Brava', 'Costa Blanca', 'Andalusien', 'Balearen',
    'Kroatien - Istrien', 'Kroatien - Dalmatien',
    'Schwarzwald', 'Bayern / Alpen', 'Österreich / Tirol', 'Schweiz Wallis',
    'Dubai', 'Marrakesch', 'Hurghada', 'Sharm el-Sheikh', 'Tunesien', 'Zypern',
    'New York', 'Miami', 'Los Angeles', 'Bali', 'Thailand - Phuket', 'Singapur',
  ];

  // Autocomplete state — one per field key
  let acState = $state({});

  function acFilter(key, value, list, iataMode = false) {
    if (!value || value.length < 1) {
      acState = { ...acState, [key]: { open: false, items: [] } };
      return;
    }
    const q = value.toLowerCase();
    let items;
    if (iataMode) {
      items = list.filter(a =>
        a.iata.toLowerCase().startsWith(q) ||
        a.city.toLowerCase().includes(q) ||
        a.country.toLowerCase().includes(q)
      ).slice(0, 8);
    } else {
      items = list.filter(d => d.toLowerCase().includes(q)).slice(0, 8);
    }
    acState = { ...acState, [key]: { open: items.length > 0, items } };
  }

  function acSelect(key, value, bindSetter) {
    bindSetter(value);
    acState = { ...acState, [key]: { open: false, items: [] } };
  }

  function acClose(key) {
    setTimeout(() => {
      acState = { ...acState, [key]: { open: false, items: [] } };
    }, 150);
  }

  // ── Flights form ──────────────────────────────────────────────────────────
  let flOrigin    = $state('BGY');
  let flDest      = $state('DUB');
  let flOut       = $state(fmt(d30));
  let flRet       = $state('');
  let flAdults    = $state(1);       // Erwachsene
  let flChildren  = $state(0);       // Kinder (2–11 J.)
  let flBaggage   = $state('none');  // Legacy
  let fl10kg      = $state(0);       // Anzahl 10kg-Koffer
  let fl20kg      = $state(0);       // Anzahl 20kg-Koffer
  let fl23kg      = $state(0);       // Anzahl 23kg-Koffer
  let fl10kgPrice = $state(0);       // €/Koffer 10kg (manuell)
  let fl20kgPrice = $state(0);       // €/Koffer 20kg (manuell)
  let fl23kgPrice = $state(0);       // €/Koffer 23kg (manuell)
  let flSeatCost  = $state(0);       // Sitzplatz €/Person/Flug
  let flSeat      = $state(false);   // Legacy
  let flDepFrom   = $state('');      // Abflug ab HH:MM
  let flDepTo     = $state('');      // Abflug bis HH:MM
  let flArrFrom   = $state('');      // Ankunft ab HH:MM
  let flArrTo     = $state('');      // Ankunft bis HH:MM
  let flMaxStops  = $state(-1);      // -1=alle, 0=nonstop, 1=max1, 2=max2

  // Gepäck-Preis-Preview (reaktiv) — nutzt User-eingegebene Preise
  const flBaggageCost = $derived(
    fl10kg * fl10kgPrice + fl20kg * fl20kgPrice + fl23kg * fl23kgPrice
  );
  const flTotalPax = $derived(flAdults + flChildren);
  // Gesamtpreis-Aufschlag (ohne Flugpreis) für Preview-Badge
  const flExtrasLabel = $derived(() => {
    const parts = [];
    if (fl10kg > 0)     parts.push(fl10kg + '× 10kg');
    if (fl20kg > 0)     parts.push(fl20kg + '× 20kg');
    if (fl23kg > 0)     parts.push(fl23kg + '× 23kg');
    if (flSeatCost > 0) parts.push($t('radarSeatBadge').replace('{n}', flSeatCost));
    return parts.join(' · ');
  });

  // ── Hotels form ───────────────────────────────────────────────────────────
  let htCity     = $state('');
  let htIn       = $state(fmt(d30));
  let htOut      = $state(fmt(d37));
  let htAdults   = $state(2);
  let htChildren = $state(0);
  let htRooms    = $state(1);

  // ── Camping form ──────────────────────────────────────────────────────────
  let cpRegion    = $state('');
  // Unterkunfts-Klassen — kann später durch API-Daten ersetzt werden
  let cpAccomOptions = $state([
    { value: 'mobilheim',         label: 'Mobilheim (Standard)' },
    { value: 'mobilheim-premium', label: 'Mobilheim (Premium)' },
    { value: 'glamping',          label: 'Glamping' },
    { value: 'stellplatz',        label: 'Stellplatz' },
  ]);
  let cpIn        = $state(fmt(d30));
  let cpOut       = $state(fmt(d37));
  let cpAdults    = $state(2);
  let cpChildren  = $state(0);
  let cpAccomType = $state('mobilheim');
  let cpBedrooms  = $state('1');
  let cpAircon    = $state(false);
  let cpPets      = $state(false);
  let cpTerrace   = $state(false);
  let cpFinalClean = $state(false); // Endreinigung

  // ── Search state ──────────────────────────────────────────────────────────
  let searching    = $state(false);
  let searchResults = $state([]);
  let activeProviderFilter = $state('all');
  let savingTracker = $state(null); // tracker id being saved

  // Provider chips derived from results
  const providerChips = $derived(() => {
    const providers = ['all', ...new Set(searchResults.map(r => r.provider))];
    return providers;
  });

  const filteredResults = $derived(() => {
    if (activeProviderFilter === 'all') return searchResults;
    return searchResults.filter(r => r.provider === activeProviderFilter);
  });

  async function doSearch() {
    if (!$apiUrl) { toast($t('radarNoBackend'), 'warning'); return; }
    searching = true;
    searchResults = [];
    activeProviderFilter = 'all';
    try {
      let endpoint, payload;
      if (activeCategory === 'flights') {
        endpoint = '/api/search/flights';
        payload = {
          origin:        flOrigin.toUpperCase(),
          destination:   flDest.toUpperCase(),
          outbound_date: flOut,
          return_date:   flRet || null,
          adults:        flAdults,
          children:      flChildren,
          baggage:       flBaggage,
          baggage_10kg:  fl10kg,
          baggage_20kg:  fl20kg,
          baggage_23kg:  fl23kg,
          seat_cost:     flSeatCost,
          seat:          flSeatCost > 0,
          dep_from:      flDepFrom || null,
          dep_to:        flDepTo   || null,
          arr_from:      flArrFrom || null,
          arr_to:        flArrTo   || null,
          max_stops:     flMaxStops,
        };
      } else if (activeCategory === 'hotels') {
        endpoint = '/api/search/hotels';
        payload = {
          destination:   htCity,
          checkin_date:  htIn,
          checkout_date: htOut,
          adults:        htAdults,
          children:      htChildren,
          rooms:         htRooms,
        };
      } else if (activeCategory === 'camping') {
        endpoint = '/api/search/camping';
        payload = {
          destination:        cpRegion,
          checkin_date:       cpIn,
          checkout_date:      cpOut,
          adults:             cpAdults,
          children:           cpChildren,
          accommodation_type: cpAccomType,
          bedrooms:           cpBedrooms,
          aircon:             cpAircon,
          pets:               cpPets,
          covered_terrace:    cpTerrace,
          final_cleaning:     cpFinalClean,
        };
      }
      const res = await api(endpoint, {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      searchResults = res.results || [];
      // Show red alert if a provider had no API key configured
      if (res.missing_api_keys?.length > 0) {
        toast(`⚠️ API Key für ${res.missing_api_keys.join(', ')} fehlt in den Einstellungen.`, 'error');
      }
      if (searchResults.length === 0 && !res.missing_api_keys?.length) toast($t('radarNoResults'), 'warning');
    } catch (e) {
      // 422 = structured API key error from backend
      const detail = e.detail || {};
      if (detail.error === 'missing_api_key') {
        toast(`⚠️ API Key für ${detail.provider} fehlt in den Einstellungen.`, 'error');
      } else {
        toast(e.message || 'Suche fehlgeschlagen', 'error');
      }
    }
    searching = false;
  }

  async function saveAsTracker(result) {
    if (!$apiUrl) { toast($t('radarNoBackend'), 'warning'); return; }
    savingTracker = result.id;
    try {
      const d = result.detail || {};
      let endpoint, payload;

      if (result._tracker_type === 'flight') {
        // Ryanair — baggage as list[BaggageItem] from stepper counts in badges
        endpoint = '/api/trackers';
        // Reconstruct BaggageItems from badge strings or legacy baggage field
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
          origin:            d.origin,
          destination:       d.destination,
          outbound_date:     d.outbound_date,
          return_date:       d.return_date || null,
          adults:            d.adults || 1,
          children:          d.children || 0,
          baggage:           d.baggage || 'none',
          baggage_10kg:      d.baggage_10kg || 0,
          baggage_20kg:      d.baggage_20kg || 0,
          baggage_23kg:      d.baggage_23kg || 0,
          seat:              d.seat || false,
          seat_cost:         d.seat_cost || 0.0,
          // Initial snapshot data from search result
          initial_price:     result.price || null,
          initial_airline:   d.airline || null,
          initial_dep_time:  d.departure_time || null,
          initial_arr_time:  d.arrival_time || null,
          initial_duration:  d.duration_min || null,
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
      toast($t('radarTrackerSaved'), 'success');
      await loadAllTrackers();
    } catch (e) {
      toast(e.message, 'error');
    }
    savingTracker = null;
  }

    // ── Active trackers ───────────────────────────────────────────────────────
  let allTrackers     = $state([]);
  let trackersLoading = $state(true);

  // Tracker gefiltert nach aktivem Tab
  const TRACKER_TYPES_BY_CAT = {
    flights: ['flight', 'google_flight'],
    hotels:  ['hotel'],
    camping: ['camping'],
    rentals: [],
  };
  const visibleTrackers = $derived(
    allTrackers.filter(t => (TRACKER_TYPES_BY_CAT[activeCategory] || []).includes(t._type))
  );

  async function loadAllTrackers() {
    if (!$apiUrl) { trackersLoading = false; return; }
    trackersLoading = true;
    try {
      // Load from all existing endpoints (backward compat until unified endpoint in Step 3)
      const [ry, gf, hm, bk] = await Promise.allSettled([
        api('/api/trackers'),
        api('/api/google-flights'),
        api('/api/accommodations/homair'),
        api('/api/accommodations/booking'),
      ]);
      allTrackers = [
        ...(ry.status === 'fulfilled' ? (ry.value || []).map(t => ({ ...t, _type: 'flight',        _table: 'trackers' }))         : []),
        ...(gf.status === 'fulfilled' ? (gf.value || []).map(t => ({ ...t, _type: 'google_flight', _table: 'gf_trackers' }))      : []),
        ...(hm.status === 'fulfilled' ? (hm.value || []).map(t => ({ ...t, _type: 'camping',       _table: 'homair_trackers' }))  : []),
        ...(bk.status === 'fulfilled' ? (bk.value || []).map(t => ({ ...t, _type: 'hotel',         _table: 'booking_trackers' })) : []),
      ];
    } catch {}
    trackersLoading = false;
  }

  // ── Price chart accordion ─────────────────────────────────────────────────
  let chartState = $state({});

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

  // Trend-Pfeil: vergleicht letzten mit vorletztem Preis-Eintrag
  function priceTrend(history) {
    if (!history || history.length < 2) return null;
    const last = history[history.length - 1].price;
    const prev = history[history.length - 2].price;
    if (last < prev) return { dir: 'down', pct: (((prev - last) / prev) * 100).toFixed(1) };
    if (last > prev) return { dir: 'up',   pct: (((last - prev) / prev) * 100).toFixed(1) };
    return { dir: 'equal', pct: '0.0' };
  }

  // Ist der aktuelle Preis der historisch günstigste?
  function isTopPrice(history, currentPrice) {
    if (!history || history.length < 2 || currentPrice == null) return false;
    const minHist = Math.min(...history.map(e => e.price));
    return currentPrice <= minHist;
  }

  function chartPts(history, w = 290, h = 65, pad = 5) {
    const prices = history.map(e => e.price);
    const minP   = Math.min(...prices);
    const maxP   = Math.max(...prices);
    const range  = maxP - minP || 1;
    const pts = history.map((e, i) => {
      const x = (i / (history.length - 1 || 1)) * w + pad;
      const y = h - ((e.price - minP) / range) * (h - 5);
      return { x, y, price: e.price };
    });
    const minPt = pts.reduce((m, p) => p.price < m.price ? p : m, pts[0]);
    const maxPt = pts.reduce((m, p) => p.price > m.price ? p : m, pts[0]);
    return {
      minP, maxP,
      minPt, maxPt,
      polyline: pts.map(p => `${p.x},${p.y}`).join(' '),
      area: [
        `${pad},${h}`,
        ...pts.map(p => `${p.x},${p.y}`),
        `${(history.length > 1 ? 1 : 0) * w + pad},${h}`,
      ].join(' '),
    };
  }

  // ── Wish-price inline edit ────────────────────────────────────────────────
  let wishState = $state({});

  async function saveWishPrice(type, id, table, newPrice) {
    const key = `${type}-${id}`;
    wishState[key] = { ...wishState[key], saving: true };
    try {
      await api(`/api/prices/wish/${table}/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ wish_price: newPrice === '' ? null : parseFloat(newPrice) }),
      });
      toast($t('radarWishPrice') + ' ✓', 'success');
      wishState[key] = { editing: false, value: newPrice, saving: false };
      await loadAllTrackers();
    } catch (e) {
      toast(e.message, 'error');
      wishState[key] = { ...wishState[key], saving: false };
    }
  }

  // ── Delete tracker ────────────────────────────────────────────────────────
  async function deleteTracker(tracker) {
    if (!confirm($t('delete') + '?')) return;
    try {
      const endpoints = {
        flight:        `/api/trackers/${tracker.id}`,
        google_flight: `/api/google-flights/${tracker.id}`,
        camping:       `/api/accommodations/homair/${tracker.id}`,
        hotel:         `/api/accommodations/booking/${tracker.id}`,
      };
      await api(endpoints[tracker._type], { method: 'DELETE' });
      await loadAllTrackers();
    } catch (e) { toast(e.message, 'error'); }
  }

  // ── Scrape / update tracker ───────────────────────────────────────────────
  async function scrapeTracker(tracker) {
    toast($t('radarUpdatePrice') + '…', 'warning');
    try {
      const endpoints = {
        flight:        `/api/trackers/${tracker.id}/scrape`,
        google_flight: `/api/google-flights/${tracker.id}/scrape`,
        camping:       `/api/accommodations/homair/${tracker.id}/scrape`,
        hotel:         `/api/accommodations/booking/${tracker.id}/scrape`,
      };
      await api(endpoints[tracker._type], { method: 'POST' });
      toast($t('radarUpdatePrice') + ' ✓', 'success');
      await loadAllTrackers();
    } catch (e) { toast(e.message, 'error'); }
  }

  // ── Refresh all trackers ─────────────────────────────────────────────────
  let isRefreshing = $state(false);
  async function refreshAllTrackers() {
    if (isRefreshing) return;
    isRefreshing = true;
    try {
      // Batching: trigger backend scheduler run
      await api('/api/scheduler/run', { method: 'POST' });
      toast('⏳ Alle Tracker werden aktualisiert… dauert 1–2 Min.', 'warning');
      // After delay, reload trackers
      setTimeout(async () => {
        await loadAllTrackers();
        isRefreshing = false;
      }, 90000); // 90s
    } catch (e) {
      toast(e.message, 'error');
      isRefreshing = false;
    }
  }

  // ── Tracker label helpers ─────────────────────────────────────────────────
  function trackerTitle(tr) {
    if (tr._type === 'flight' || tr._type === 'google_flight') {
      return `${tr.origin} → ${tr.destination}`;
    }
    if (tr._type === 'hotel') return `🏨 ${tr.hotel_name || tr.destination}`;
    if (tr._type === 'camping') return `⛺ ${tr.campsite_name || tr.region || tr.destination || ''}`;
    return tr.destination || tr.location_name || '–';
  }

  function trackerSubtitle(tr) {
    const parts = [];
    if (tr.outbound_date) parts.push(fmtDate(tr.outbound_date) + (tr.return_date ? ' ⇄ ' + fmtDate(tr.return_date) : ''));
    if (tr.checkin_date)  parts.push(fmtDate(tr.checkin_date)  + (tr.checkout_date ? ' – ' + fmtDate(tr.checkout_date) : ''));
    if (tr.adults) parts.push(tr.adults + ' ' + $t('radarAdultsShort'));
    if (tr.rooms)  parts.push(tr.rooms  + ' Zi.');
    // NOTE: airline/zeiten werden in separater Zeile gerendert (kein Doppel)
    return parts.join(' · ');
  }

  function trackerBadges(tr) {
    const badges = [];
    if (tr._type === 'flight') {
      // Parse baggage_json (list of BaggageItems) from Ryanair tracker
      try {
        const bagItems = JSON.parse(tr.baggage_json || '[]');
        const cnt10 = bagItems.filter(b => b.type === '10kg').length;
        const cnt20 = bagItems.filter(b => b.type === '20kg').length;
        const cnt23 = bagItems.filter(b => b.type === '23kg').length;
        if (cnt10 > 0) badges.push(`🎒 ${cnt10}× 10kg`);
        if (cnt20 > 0) badges.push(`🎒 ${cnt20}× 20kg`);
        if (cnt23 > 0) badges.push(`🧳 ${cnt23}× 23kg`);
      } catch {}
      if ((tr.seat_cost || 0) > 0) badges.push($t('radarSeatBadge').replace('{n}', tr.seat_cost));
    }
    if (tr._type === 'google_flight') {
      // Parse baggage_json (JSON object) from GF tracker
      try {
        const bg = JSON.parse(tr.baggage_json || '{}');
        if (bg.baggage_10kg > 0) badges.push(`🎒 ${bg.baggage_10kg}× 10kg`);
        else if (bg.baggage === '10kg') badges.push('🎒 1× 10kg');
        if (bg.baggage_20kg > 0) badges.push(`🎒 ${bg.baggage_20kg}× 20kg`);
        else if (bg.baggage === '20kg' && !bg.baggage_10kg) badges.push('🎒 1× 20kg');
        if (bg.baggage_23kg > 0) badges.push(`🧳 ${bg.baggage_23kg}× 23kg`);
      } catch {}
      if ((tr.seat_cost || 0) > 0) badges.push($t('radarSeatBadge').replace('{n}', tr.seat_cost));
    }
    if (tr._type === 'camping') {
      const at = (tr.accommodation_type || '').toLowerCase();
      if (at.includes('mobilheim') || at.includes('chalet')) badges.push('⛺ Mobilheim');
      else if (at.includes('glamping')) badges.push('🌟 Glamping');
      else if (at.includes('stellplatz') || at.includes('pitch')) badges.push('🅿️ Stellplatz');
      if (tr.aircon) badges.push('❄️ Klima');
      if (tr.pets) badges.push('🐕 Hunde');
    }
    if (tr._type === 'hotel') {
      if (tr.rooms > 1) badges.push(`🛏 ${tr.rooms} Zi.`);
    }
    return badges;
  }

  function providerIcon(type) {
    if (type === 'flight') return '🟠';
    if (type === 'google_flight') return '🔵';
    if (type === 'camping') return '⛺';
    if (type === 'hotel') return '🏨';
    return '📍';
  }

  function providerLabel(tr) {
    if (tr._type === 'flight')        return 'Ryanair';
    if (tr._type === 'google_flight') return 'Google Flights';
    if (tr._type === 'hotel')         return tr.source === 'google_hotels' ? 'Google Hotels' : 'Booking.com';
    if (tr._type === 'camping')       return 'Homair';
    return tr._type;
  }

  // ── Init ──────────────────────────────────────────────────────────────────
  onMount(() => { loadAllTrackers(); });
</script>

<!-- ── Page ── -->
<div class="space-y-5">

  <!-- ── Category tab bar ── -->
  <div class="flex border-b overflow-x-auto" style="border-color:var(--ws-border)">
    {#each categories as cat}
      <button
        onclick={() => { activeCategory = cat.id; searchResults = []; }}
        class="px-4 py-2.5 text-xs font-semibold whitespace-nowrap shrink-0 transition-colors border-b-2"
        style={activeCategory === cat.id
          ? 'border-color:var(--ws-accent);color:var(--ws-accent)'
          : 'border-color:transparent;color:var(--ws-muted)'}>
        {cat.label}
      </button>
    {/each}
  </div>

  <!-- ══════════════════════════ FLIGHTS ══════════════════════════ -->
  {#if activeCategory === 'flights'}
  <div class="rounded-xl p-4 border space-y-4" style="background:var(--ws-surface);border-color:var(--ws-border)">
    <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">✈️ {$t('radarFlights')}</h2>

    <!-- Origin / Destination mit Autocomplete -->
    <div class="grid grid-cols-2 gap-3">
      <div class="relative">
        <label class="{labelCls}" style="color:var(--ws-muted)">{$t('radarDeparture')}</label>
        <input bind:value={flOrigin} placeholder="BGY" maxlength="3"
          class="{inputCls} font-mono uppercase" style={inputStyle}
          oninput={() => acFilter('flOrigin', flOrigin, AIRPORTS, true)}
          onblur={() => acClose('flOrigin')}/>
        {#if acState.flOrigin?.open}
          <div class="absolute z-50 left-0 right-0 top-full mt-1 rounded-xl border shadow-lg overflow-hidden" style="background:var(--ws-surface);border-color:var(--ws-border)">
            {#each acState.flOrigin.items as a}
              <button class="w-full text-left px-3 py-2 text-xs hover:bg-[var(--ws-surface2)] flex items-center gap-2"
                onmousedown={() => acSelect('flOrigin', a.iata, v => flOrigin = v)}>
                <span class="font-mono font-bold" style="color:var(--ws-accent)">{a.iata}</span>
                <span style="color:var(--ws-text)">{a.city}</span>
                <span class="ml-auto text-xs" style="color:var(--ws-muted)">{a.country}</span>
              </button>
            {/each}
          </div>
        {/if}
      </div>
      <div class="relative">
        <label class="{labelCls}" style="color:var(--ws-muted)">{$t('radarArrival')}</label>
        <input bind:value={flDest} placeholder="DUB" maxlength="3"
          class="{inputCls} font-mono uppercase" style={inputStyle}
          oninput={() => acFilter('flDest', flDest, AIRPORTS, true)}
          onblur={() => acClose('flDest')}/>
        {#if acState.flDest?.open}
          <div class="absolute z-50 left-0 right-0 top-full mt-1 rounded-xl border shadow-lg overflow-hidden" style="background:var(--ws-surface);border-color:var(--ws-border)">
            {#each acState.flDest.items as a}
              <button class="w-full text-left px-3 py-2 text-xs hover:bg-[var(--ws-surface2)] flex items-center gap-2"
                onmousedown={() => acSelect('flDest', a.iata, v => flDest = v)}>
                <span class="font-mono font-bold" style="color:var(--ws-accent)">{a.iata}</span>
                <span style="color:var(--ws-text)">{a.city}</span>
                <span class="ml-auto text-xs" style="color:var(--ws-muted)">{a.country}</span>
              </button>
            {/each}
          </div>
        {/if}
      </div>
    </div>

    <!-- Daten -->
    <div class="grid grid-cols-2 gap-3">
      <div>
        <label class="{labelCls}" style="color:var(--ws-muted)">{$t('radarOutboundDate')}</label>
        <input type="date" bind:value={flOut} class="{inputCls}" style={inputStyle}/>
      </div>
      <div>
        <label class="{labelCls}" style="color:var(--ws-muted)">{$t('radarReturnDate')}</label>
        <input type="date" bind:value={flRet} class="{inputCls}" style={inputStyle}/>
      </div>
    </div>

    <!-- Personen-Split: Erwachsene + Kinder -->
    <div>
      <label class="{labelCls}" style="color:var(--ws-muted)">👥 {$t('radarPassengers')}</label>
      <div class="grid grid-cols-2 gap-3 mt-1">
        <!-- Erwachsene -->
        <div class="rounded-xl border p-2.5 flex items-center justify-between gap-2"
          style="background:var(--ws-surface2);border-color:var(--ws-border)">
          <div>
            <div class="text-xs font-semibold" style="color:var(--ws-text)">{$t('radarAdults')}</div>
            <div class="text-[10px]" style="color:var(--ws-muted)">ab 12 J.</div>
          </div>
          <div class="flex items-center gap-2">
            <button onclick={() => flAdults = Math.max(1, flAdults - 1)}
              class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center transition-opacity hover:opacity-70"
              style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">−</button>
            <span class="w-5 text-center text-sm font-bold" style="color:var(--ws-text)">{flAdults}</span>
            <button onclick={() => flAdults = Math.min(9, flAdults + 1)}
              class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center transition-opacity hover:opacity-70"
              style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
          </div>
        </div>
        <!-- Kinder -->
        <div class="rounded-xl border p-2.5 flex items-center justify-between gap-2"
          style="background:var(--ws-surface2);border-color:var(--ws-border)">
          <div>
            <div class="text-xs font-semibold" style="color:var(--ws-text)">{$t('radarChildren')}</div>
            <div class="text-[10px]" style="color:var(--ws-muted)">2–11 J.</div>
          </div>
          <div class="flex items-center gap-2">
            <button onclick={() => flChildren = Math.max(0, flChildren - 1)}
              class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center transition-opacity hover:opacity-70"
              style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">−</button>
            <span class="w-5 text-center text-sm font-bold" style="color:var(--ws-text)">{flChildren}</span>
            <button onclick={() => flChildren = Math.min(8, flChildren + 1)}
              class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center transition-opacity hover:opacity-70"
              style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ✈️ Akkordeon 1: Gepäck & Sitzplätze -->
    <details class="rounded-xl border overflow-hidden" style="border-color:var(--ws-border)">
      <summary class="px-3 py-2.5 text-xs font-semibold cursor-pointer select-none flex items-center gap-2"
        style="background:var(--ws-surface2);color:var(--ws-muted);list-style:none">
        <span>🧳 {$t('radarBaggageSeat')}</span>
        {#if fl10kg > 0 || fl20kg > 0 || fl23kg > 0 || flSeatCost > 0}
          <span class="ml-auto text-[10px] font-normal" style="color:var(--ws-accent)">aktiv</span>
        {/if}
      </summary>
      <div class="p-3 space-y-4" style="background:var(--ws-surface)">
        <!-- Gepäck-Stepper: 10kg / 20kg / 23kg -->
        <div>
          <label class="{labelCls}" style="color:var(--ws-muted)">🧳 {$t('radarBaggage')} — {$t('radarInclusions')}</label>
          <div class="space-y-2 mt-1">
            {#each [
              [() => fl10kg, v => fl10kg = v, () => fl10kgPrice, v => fl10kgPrice = v, '10 kg'],
              [() => fl20kg, v => fl20kg = v, () => fl20kgPrice, v => fl20kgPrice = v, '20 kg'],
              [() => fl23kg, v => fl23kg = v, () => fl23kgPrice, v => fl23kgPrice = v, '23 kg'],
            ] as [getter, setter, pGetter, pSetter, label]}
              <div class="rounded-xl border p-2.5 flex items-center gap-2"
                style="background:var(--ws-surface2);border-color:var(--ws-border)">
                <span class="text-xs font-semibold w-10 shrink-0" style="color:var(--ws-text)">{label}</span>
                <div class="flex items-center gap-1.5 shrink-0">
                  <button onclick={() => setter(Math.max(0, getter() - 1))}
                    class="w-6 h-6 rounded-lg border text-sm font-bold flex items-center justify-center"
                    style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">−</button>
                  <span class="w-4 text-center text-sm font-bold" style="color:{getter()>0?'var(--ws-accent)':'var(--ws-muted)'}">{getter()}</span>
                  <button onclick={() => setter(Math.min(9, getter() + 1))}
                    class="w-6 h-6 rounded-lg border text-sm font-bold flex items-center justify-center"
                    style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
                </div>
                <div class="flex items-center gap-1 flex-1 min-w-0">
                  <input type="number" bind:value={() => pGetter(), v => pSetter(v)} min="0" step="0.01"
                    placeholder="€/Koffer"
                    class="flex-1 min-w-0 px-2 py-1 rounded-lg border text-xs font-mono text-center outline-none"
                    style="{inputStyle};opacity:{getter()>0?1:0.4}"
                    disabled={getter() === 0}/>
                  <span class="text-[10px] shrink-0" style="color:var(--ws-muted)">€</span>
                </div>
                {#if getter() > 0 && pGetter() > 0}
                  <span class="text-xs font-mono shrink-0" style="color:var(--ws-accent)">{(getter()*pGetter()).toFixed(2)}€</span>
                {/if}
              </div>
            {/each}
            {#if flBaggageCost > 0}
              <div class="text-xs px-2" style="color:var(--ws-muted)">
                🧳 Gepäck gesamt: <strong style="color:var(--ws-accent)">{flBaggageCost.toFixed(2)} €</strong>
              </div>
            {/if}
          </div>
        </div>
        <!-- Sitzplatz -->
        <div>
          <label class="{labelCls}" style="color:var(--ws-muted)">💺 {$t('radarSeat')}</label>
          <div class="flex items-center gap-3 mt-1">
            <div class="flex items-center gap-2 rounded-xl border p-2.5 flex-1"
              style="background:var(--ws-surface2);border-color:var(--ws-border)">
              <button onclick={() => flSeatCost = Math.max(0, Math.round((flSeatCost - 1)*10)/10)}
                class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center transition-opacity hover:opacity-70"
                style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">−</button>
              <input type="number" bind:value={flSeatCost} min="0" step="0.5"
                class="flex-1 text-center text-sm font-bold bg-transparent outline-none"
                style="color:var(--ws-text)" placeholder="0"/>
              <button onclick={() => flSeatCost = Math.round((flSeatCost + 1)*10)/10}
                class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center transition-opacity hover:opacity-70"
                style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
            </div>
            <span class="text-xs shrink-0" style="color:var(--ws-muted)">€</span>
          </div>
          {#if flSeatCost > 0}
            <div class="text-xs mt-1 px-1" style="color:var(--ws-muted)">
              💺 {flTotalPax} × {flSeatCost} € = <strong style="color:var(--ws-accent)">{(flTotalPax * flSeatCost).toFixed(2)} €</strong>
            </div>
          {/if}
        </div>
      </div>
    </details>

    <!-- ✈️ Akkordeon 2: Zeiten & Stopps -->
    <details class="rounded-xl border overflow-hidden" style="border-color:var(--ws-border)">
      <summary class="px-3 py-2.5 text-xs font-semibold cursor-pointer select-none flex items-center gap-2"
        style="background:var(--ws-surface2);color:var(--ws-muted);list-style:none">
        <span>⏱️ {$t('radarTimesStops')}</span>
        {#if flMaxStops >= 0 || flDepFrom || flDepTo || flArrFrom || flArrTo}
          <span class="ml-auto text-[10px] font-normal" style="color:var(--ws-accent)">aktiv</span>
        {/if}
      </summary>
      <div class="p-3 space-y-3" style="background:var(--ws-surface)">
        <!-- Stopp-Filter -->
        <div>
          <label class="{labelCls}" style="color:var(--ws-muted)">🔀 Stopps</label>
          <div class="flex gap-2 flex-wrap mt-1">
            {#each [[-1,'Alle'], [0,'Nonstop'], [1,'Max 1'], [2,'Max 2']] as [val, lbl]}
              <button onclick={() => flMaxStops = val}
                class="px-3 py-1.5 rounded-xl border text-xs font-medium transition-colors"
                style={flMaxStops === val
                  ? 'background:rgba(196,98,45,.12);border-color:var(--ws-accent);color:var(--ws-accent)'
                  : 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)'}>
                {lbl}
              </button>
            {/each}
          </div>
        </div>
        <!-- Abflug-Fenster -->
        <div>
          <div class="text-xs font-semibold mb-1.5" style="color:var(--ws-muted)">🛫 Abflug</div>
          <div class="grid grid-cols-2 gap-2">
            <div>
              <div class="text-[10px] mb-1" style="color:var(--ws-muted)">ab</div>
              <input type="time" bind:value={flDepFrom} class="{inputCls}" style={inputStyle}/>
            </div>
            <div>
              <div class="text-[10px] mb-1" style="color:var(--ws-muted)">bis</div>
              <input type="time" bind:value={flDepTo} class="{inputCls}" style={inputStyle}/>
            </div>
          </div>
        </div>
        <!-- Ankunft-Fenster -->
        <div>
          <div class="text-xs font-semibold mb-1.5" style="color:var(--ws-muted)">🛬 Ankunft</div>
          <div class="grid grid-cols-2 gap-2">
            <div>
              <div class="text-[10px] mb-1" style="color:var(--ws-muted)">ab</div>
              <input type="time" bind:value={flArrFrom} class="{inputCls}" style={inputStyle}/>
            </div>
            <div>
              <div class="text-[10px] mb-1" style="color:var(--ws-muted)">bis</div>
              <input type="time" bind:value={flArrTo} class="{inputCls}" style={inputStyle}/>
            </div>
          </div>
        </div>
        <button onclick={() => { flDepFrom=''; flDepTo=''; flArrFrom=''; flArrTo=''; flMaxStops=-1; }}
          class="text-xs px-2 py-1 rounded-lg border" style="border-color:var(--ws-border);color:var(--ws-muted)">
          ✕ Filter zurücksetzen
        </button>
      </div>
    </details>

        <!-- Suche-Button + Preview-Summary -->
    {#if flExtrasLabel()}
      <div class="text-xs px-1" style="color:var(--ws-muted)">
        ℹ️ Aufschlag wird auf Flugpreis addiert: {flExtrasLabel()}
      </div>
    {/if}
    <button
      onclick={doSearch}
      disabled={searching || !flOrigin || !flDest || !flOut}
      class="w-full py-2.5 rounded-xl font-semibold text-sm transition-opacity hover:opacity-80 disabled:opacity-50"
      style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
      {searching ? $t('radarSearching') : '🔍 ' + $t('radarSearch')}
    </button>
  </div>

  <!-- ══════════════════════════ HOTELS ══════════════════════════ -->
  {:else if activeCategory === 'hotels'}
  <div class="rounded-xl p-4 border space-y-4" style="background:var(--ws-surface);border-color:var(--ws-border)">
    <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">🏨 {$t('radarHotels')}</h2>

    <!-- City autocomplete -->
    <div class="relative">
      <label class="{labelCls}" style="color:var(--ws-muted)">{$t('radarCity')}</label>
      <input
        bind:value={htCity}
        placeholder="z.B. Barcelona, Wien, Kreta…"
        class="{inputCls}"
        style={inputStyle}
        oninput={() => acFilter('htCity', htCity, DESTINATIONS)}
        onblur={() => acClose('htCity')}
      />
      {#if acState.htCity?.open}
        <div class="absolute z-50 left-0 right-0 top-full mt-1 rounded-xl border shadow-lg overflow-hidden" style="background:var(--ws-surface);border-color:var(--ws-border)">
          {#each acState.htCity.items as dest}
            <button
              class="w-full text-left px-3 py-2 text-xs hover:bg-[var(--ws-surface2)]"
              style="color:var(--ws-text)"
              onmousedown={() => acSelect('htCity', dest, v => htCity = v)}>
              {dest}
            </button>
          {/each}
        </div>
      {/if}
    </div>

    <!-- Dates -->
    <div class="grid grid-cols-2 gap-3">
      <div>
        <label class="{labelCls}" style="color:var(--ws-muted)">{$t('radarCheckin')}</label>
        <input type="date" bind:value={htIn} class="{inputCls}" style={inputStyle}/>
      </div>
      <div>
        <label class="{labelCls}" style="color:var(--ws-muted)">{$t('radarCheckout')}</label>
        <input type="date" bind:value={htOut} class="{inputCls}" style={inputStyle}/>
      </div>
    </div>

    <!-- Personen-Split Erw./Kinder + Zimmer -->
    <div class="grid grid-cols-3 gap-2">
      <!-- Erwachsene -->
      <div class="rounded-xl border p-2.5 flex flex-col items-center gap-1.5"
        style="background:var(--ws-surface2);border-color:var(--ws-border)">
        <div class="text-[10px] font-semibold" style="color:var(--ws-muted)">{$t('radarAdults')}</div>
        <div class="flex items-center gap-1.5">
          <button onclick={() => htAdults = Math.max(1, htAdults-1)}
            class="w-6 h-6 rounded-lg border text-sm font-bold flex items-center justify-center"
            style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">−</button>
          <span class="text-sm font-bold w-4 text-center" style="color:var(--ws-text)">{htAdults}</span>
          <button onclick={() => htAdults = Math.min(9, htAdults+1)}
            class="w-6 h-6 rounded-lg border text-sm font-bold flex items-center justify-center"
            style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
        </div>
      </div>
      <!-- Kinder -->
      <div class="rounded-xl border p-2.5 flex flex-col items-center gap-1.5"
        style="background:var(--ws-surface2);border-color:var(--ws-border)">
        <div class="text-[10px] font-semibold" style="color:var(--ws-muted)">{$t('radarChildren')}</div>
        <div class="flex items-center gap-1.5">
          <button onclick={() => htChildren = Math.max(0, htChildren-1)}
            class="w-6 h-6 rounded-lg border text-sm font-bold flex items-center justify-center"
            style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">−</button>
          <span class="text-sm font-bold w-4 text-center" style="color:var(--ws-text)">{htChildren}</span>
          <button onclick={() => htChildren = Math.min(8, htChildren+1)}
            class="w-6 h-6 rounded-lg border text-sm font-bold flex items-center justify-center"
            style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
        </div>
      </div>
      <!-- Zimmer -->
      <div class="rounded-xl border p-2.5 flex flex-col items-center gap-1.5"
        style="background:var(--ws-surface2);border-color:var(--ws-border)">
        <div class="text-[10px] font-semibold" style="color:var(--ws-muted)">{$t('radarRoomsLabel')}</div>
        <div class="flex items-center gap-1.5">
          <button onclick={() => htRooms = Math.max(1, htRooms-1)}
            class="w-6 h-6 rounded-lg border text-sm font-bold flex items-center justify-center"
            style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">−</button>
          <span class="text-sm font-bold w-4 text-center" style="color:var(--ws-text)">{htRooms}</span>
          <button onclick={() => htRooms = Math.min(4, htRooms+1)}
            class="w-6 h-6 rounded-lg border text-sm font-bold flex items-center justify-center"
            style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
        </div>
      </div>
    </div>

    <button
      onclick={doSearch}
      disabled={searching || !htCity || !htIn || !htOut}
      class="w-full py-2.5 rounded-xl font-semibold text-sm hover:opacity-80 disabled:opacity-50"
      style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
      {searching ? $t('radarSearching') : '🔍 ' + $t('radarSearch')}
    </button>
  </div>

  <!-- ══════════════════════════ CAMPING ══════════════════════════ -->
  {:else if activeCategory === 'camping'}
  <div class="rounded-xl p-4 border space-y-4" style="background:var(--ws-surface);border-color:var(--ws-border)">
    <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">⛺ {$t('radarCamping')}</h2>

    <!-- Region autocomplete -->
    <div class="relative">
      <label class="{labelCls}" style="color:var(--ws-muted)">{$t('radarRegionOrPlace')}</label>
      <input
        bind:value={cpRegion}
        placeholder="z.B. Côte d'Azur, Toskana, Kroatien…"
        class="{inputCls}"
        style={inputStyle}
        oninput={() => acFilter('cpRegion', cpRegion, DESTINATIONS)}
        onblur={() => acClose('cpRegion')}
      />
      {#if acState.cpRegion?.open}
        <div class="absolute z-50 left-0 right-0 top-full mt-1 rounded-xl border shadow-lg overflow-hidden" style="background:var(--ws-surface);border-color:var(--ws-border)">
          {#each acState.cpRegion.items as dest}
            <button
              class="w-full text-left px-3 py-2 text-xs hover:bg-[var(--ws-surface2)]"
              style="color:var(--ws-text)"
              onmousedown={() => acSelect('cpRegion', dest, v => cpRegion = v)}>
              {dest}
            </button>
          {/each}
        </div>
      {/if}
    </div>

    <!-- Dates -->
    <div class="grid grid-cols-2 gap-3">
      <div>
        <label class="{labelCls}" style="color:var(--ws-muted)">{$t('radarCheckin')}</label>
        <input type="date" bind:value={cpIn} class="{inputCls}" style={inputStyle}/>
      </div>
      <div>
        <label class="{labelCls}" style="color:var(--ws-muted)">{$t('radarCheckout')}</label>
        <input type="date" bind:value={cpOut} class="{inputCls}" style={inputStyle}/>
      </div>
    </div>

    <!-- Personen-Split Erw./Kinder -->
    <div>
      <label class="{labelCls}" style="color:var(--ws-muted)">👥 {$t('radarPassengers')}</label>
      <div class="grid grid-cols-2 gap-2 mt-1">
        <div class="rounded-xl border p-2.5 flex items-center justify-between"
          style="background:var(--ws-surface2);border-color:var(--ws-border)">
          <div>
            <div class="text-xs font-semibold" style="color:var(--ws-text)">{$t('radarAdults')}</div>
          </div>
          <div class="flex items-center gap-2">
            <button onclick={() => cpAdults = Math.max(1, cpAdults-1)}
              class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center"
              style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">−</button>
            <span class="w-5 text-center text-sm font-bold" style="color:var(--ws-text)">{cpAdults}</span>
            <button onclick={() => cpAdults = Math.min(9, cpAdults+1)}
              class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center"
              style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
          </div>
        </div>
        <div class="rounded-xl border p-2.5 flex items-center justify-between"
          style="background:var(--ws-surface2);border-color:var(--ws-border)">
          <div>
            <div class="text-xs font-semibold" style="color:var(--ws-text)">{$t('radarChildren')}</div>
            <div class="text-[10px]" style="color:var(--ws-muted)">bis 17 J.</div>
          </div>
          <div class="flex items-center gap-2">
            <button onclick={() => cpChildren = Math.max(0, cpChildren-1)}
              class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center"
              style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">−</button>
            <span class="w-5 text-center text-sm font-bold" style="color:var(--ws-text)">{cpChildren}</span>
            <button onclick={() => cpChildren = Math.min(8, cpChildren+1)}
              class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center"
              style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Accommodation type dropdown -->
    <div>
      <label class="{labelCls}" style="color:var(--ws-muted)">{$t('radarAccomType')}</label>
      <!-- Dropdown vorbereitet für dynamische API-Klassen (Standard/Premium etc.) -->
      <select bind:value={cpAccomType} class="{inputCls}" style={inputStyle}>
        {#each cpAccomOptions as opt}
          <option value={opt.value}>{opt.label}</option>
        {/each}
      </select>
    </div>

    <!-- Bedrooms dropdown -->
    <div>
      <label class="{labelCls}" style="color:var(--ws-muted)">{$t('radarBedrooms')}</label>
      <select bind:value={cpBedrooms} class="{inputCls}" style={inputStyle}>
        <option value="1">1 Schlafzimmer</option>
        <option value="2">2 Schlafzimmer</option>
        <option value="3">3+ Schlafzimmer</option>
      </select>
    </div>

    <!-- Extras checkboxes -->
    <div>
      <label class="{labelCls}" style="color:var(--ws-muted)">{$t('radarExtras')}</label>
      <div class="mt-1.5 space-y-2">
        {#each [
          [() => cpAircon,     v => cpAircon     = v, 'radarAircon'],
          [() => cpPets,       v => cpPets       = v, 'radarPetsAllowed'],
          [() => cpTerrace,    v => cpTerrace    = v, 'radarCoveredTerrace'],
          [() => cpFinalClean, v => cpFinalClean = v, 'radarFinalCleaning'],
        ] as [getter, setter, key]}
          <button
            onclick={() => setter(!getter())}
            class="w-full flex items-center gap-3 px-3 py-2 rounded-xl border text-sm text-left transition-colors"
            style={getter()
              ? 'background:rgba(196,98,45,.1);border-color:var(--ws-accent);color:var(--ws-text)'
              : 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)'}>
            <span class="w-4 h-4 rounded border flex items-center justify-center text-xs shrink-0"
              style="border-color:{getter() ? 'var(--ws-accent)' : 'var(--ws-border)'}">
              {getter() ? '✓' : ''}
            </span>
            {$t(key)}
          </button>
        {/each}
      </div>
    </div>

    <button
      onclick={doSearch}
      disabled={searching || !cpRegion || !cpIn || !cpOut}
      class="w-full py-2.5 rounded-xl font-semibold text-sm hover:opacity-80 disabled:opacity-50"
      style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
      {searching ? $t('radarSearching') : '🔍 ' + $t('radarSearch')}
    </button>
  </div>

  <!-- ══════════════════════════ RENTALS (Coming Soon) ══════════════════════════ -->
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

  <!-- ══════════════════════════ SEARCH RESULTS ══════════════════════════ -->
  {#if searching}
    <!-- Skeleton screens -->
    <div class="space-y-3">
      <div class="text-xs font-semibold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('radarSearchResults')}</div>
      {#each [1,2,3] as _}
        <div class="rounded-xl p-4 border animate-pulse" style="background:var(--ws-surface);border-color:var(--ws-border)">
          <div class="flex justify-between items-start">
            <div class="space-y-2 flex-1">
              <div class="h-4 w-40 rounded" style="background:var(--ws-border)"></div>
              <div class="h-3 w-56 rounded" style="background:var(--ws-border)"></div>
              <div class="flex gap-2">
                <div class="h-5 w-16 rounded-full" style="background:var(--ws-border)"></div>
                <div class="h-5 w-20 rounded-full" style="background:var(--ws-border)"></div>
              </div>
            </div>
            <div class="space-y-2 text-right">
              <div class="h-6 w-20 rounded" style="background:var(--ws-border)"></div>
              <div class="h-7 w-28 rounded-xl" style="background:var(--ws-border)"></div>
            </div>
          </div>
        </div>
      {/each}
    </div>

  {:else if searchResults.length > 0}
    <div class="space-y-3">
      <!-- Header + provider chips -->
      <div class="flex items-center gap-2 flex-wrap">
        <span class="text-xs font-semibold uppercase tracking-wider" style="color:var(--ws-muted)">
          {$t('radarSearchResults')} ({filteredResults().length})
        </span>
        <div class="flex gap-1.5 overflow-x-auto">
          {#each providerChips() as chip}
            <button
              onclick={() => activeProviderFilter = chip}
              class="px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap shrink-0 border transition-colors"
              style={activeProviderFilter === chip
                ? 'background:var(--ws-accent);color:#fff;border-color:var(--ws-accent)'
                : 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)'}>
              {chip === 'all' ? $t('radarAllProviders') : chip}
            </button>
          {/each}
        </div>
      </div>

      <!-- Result cards -->
      {#each filteredResults() as result}
        {@const d = result.detail || {}}
        <div class="rounded-xl p-4 border" style="background:var(--ws-surface);border-color:var(--ws-border)">
          <div class="flex items-start justify-between gap-2">
            <div class="flex-1 min-w-0 overflow-hidden">
              <div class="font-bold text-sm truncate" style="color:var(--ws-text)">{result.title || result.label || '–'}</div>
              {#if result.subtitle}
                {@const cleanSubtitle = d.airline
                  ? result.subtitle
                      .replace(/·\s*[^·]+·\s*\d{2}:\d{2}→\d{2}:\d{2}/, '')  // strip "· Airline · HH:MM→HH:MM"
                      .replace(/(\d{4})-(\d{2})-(\d{2})/g, (_, y, m, d2) => `${d2}.${m}.${y}`)
                      .replace(/·\s*·/g, '·').trim().replace(/·\s*$/, '').trim()
                  : result.subtitle.replace(/(\d{4})-(\d{2})-(\d{2})/g, (_, y, m, d2) => `${d2}.${m}.${y}`)}
                <div class="text-xs mt-0.5" style="color:var(--ws-muted)">{cleanSubtitle}</div>
              {/if}
              <!-- Airline + Flugzeiten (einzige Quelle — nicht doppelt im Subtitle) -->
              {#if d.airline || (d.departure_time && d.arrival_time)}
                <div class="flex items-center gap-1.5 mt-1.5 flex-wrap">
                  {#if d.airline}
                    <span class="text-xs">✈️</span>
                    <span class="text-xs font-semibold" style="color:var(--ws-accent)">{d.airline}</span>
                  {/if}
                  {#if d.flight_number}
                    <span class="text-xs font-mono px-1.5 py-0.5 rounded" style="background:var(--ws-surface2);color:var(--ws-muted)">{d.flight_number}</span>
                  {/if}
                  {#if d.departure_time && d.arrival_time}
                    <span class="text-xs font-mono" style="color:var(--ws-muted)">{String(d.departure_time).slice(0,5)} → {String(d.arrival_time).slice(0,5)}</span>
                  {/if}
                  {#if d.duration_min}
                    <span class="text-xs" style="color:var(--ws-muted)">({Math.floor(d.duration_min/60)}h{d.duration_min%60}m)</span>
                  {/if}
                </div>
              {/if}
              <div class="flex gap-1.5 flex-wrap mt-1.5">
                <span class="text-xs px-2 py-0.5 rounded-full" style="background:var(--ws-surface2);color:var(--ws-muted)">{result.provider}</span>
                {#each (result.badges || []) as badge}
                  <span class="text-xs px-2 py-0.5 rounded-full" style="background:rgba(196,98,45,.08);color:var(--ws-accent)">{badge}</span>
                {/each}
              </div>
            </div>
            <div class="text-right flex-none pl-1" style="min-width:90px;max-width:130px">
              <div class="font-bold font-mono text-base whitespace-nowrap" style="color:var(--ws-green)">
                {result.price ? result.price.toFixed(2) + ' €' : '–'}
              </div>
              {#if result.price_per_night && result.nights > 1}
                <div class="text-[10px] font-mono whitespace-nowrap" style="color:var(--ws-muted)">
                  Ø {result.price_per_night.toFixed(2)} {$t('radarPerNight')}
                </div>
              {/if}
              <button
                onclick={() => saveAsTracker(result)}
                disabled={savingTracker === result.id}
                class="mt-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-opacity hover:opacity-80 disabled:opacity-50"
                style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
                {savingTracker === result.id ? '⏳…' : $t('radarSaveTracker')}
              </button>
              {#if result.booking_url}
                <a href={result.booking_url} target="_blank" rel="noopener noreferrer"
                  class="mt-1 block text-center px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all hover:opacity-80"
                  style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-accent);text-decoration:none">
                  Buchen ↗
                </a>
              {/if}
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}

  <!-- ══════════════════════════ ACTIVE TRACKERS ══════════════════════════ -->
  <div>
    <div class="flex items-center justify-between gap-2 mb-3 flex-wrap">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">
        📌 {$t('radarActiveTrackers')}
        {#if visibleTrackers.length > 0}
          <span class="ml-1 text-xs font-normal" style="color:var(--ws-muted)">({visibleTrackers.length} / {allTrackers.length} gesamt)</span>
        {/if}
      </h2>
      {#if allTrackers.length > 0}
        <button
          onclick={refreshAllTrackers}
          disabled={isRefreshing}
          class="px-3 py-1.5 rounded-xl text-xs border transition-all disabled:opacity-50"
          style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">
          {isRefreshing ? '⏳ ' + $t('radarRefreshing') : '🔄 ' + $t('radarRefreshAll')}
        </button>
      {/if}
    </div>

    {#if trackersLoading}
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 items-stretch">
        {#each [1,2,3] as _}
          <div class="rounded-xl p-4 border animate-pulse" style="background:var(--ws-surface);border-color:var(--ws-border)">
            <div class="h-4 w-32 rounded mb-2" style="background:var(--ws-border)"></div>
            <div class="h-3 w-48 rounded mb-3" style="background:var(--ws-border)"></div>
            <div class="h-8 rounded" style="background:var(--ws-border)"></div>
          </div>
        {/each}
      </div>

    {:else if visibleTrackers.length === 0}
      <div class="rounded-xl p-6 border text-center" style="background:var(--ws-surface);border-color:var(--ws-border)">
        <div class="text-2xl mb-2">📭</div>
        <p class="text-xs" style="color:var(--ws-muted)">
          {allTrackers.length > 0
            ? 'Keine ' + (activeCategory === 'flights' ? 'Flug' : activeCategory === 'hotels' ? 'Hotel' : 'Camping') + '-Tracker — oben suchen und speichern!'
            : $t('dashNoTrackers')}
        </p>
      </div>

    {:else}
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 items-stretch">
        {#each visibleTrackers as tr}
          {@const wKey   = `${tr._type}-${tr.id}`}
          {@const cKey   = wKey}
          {@const s      = tr.latest_snapshot}
          {@const price  = s?.total_price}
          {@const wish   = tr.wish_price}
          {@const wishMet = wish && price && price <= wish}
          {@const badges  = trackerBadges(tr)}

          <div
            class="rounded-xl p-4 border flex flex-col gap-3 transition-all h-full"
            style="background:var(--ws-surface);border-color:{wishMet ? 'var(--ws-green)' : 'var(--ws-border)'};
                   {wishMet ? 'box-shadow:0 0 0 2px rgba(22,163,74,.2)' : ''}">

            <!-- Provider badge + wish met + Buchen-Button -->
            <div class="flex items-center justify-between gap-2">
              <span class="text-xs px-2 py-0.5 rounded-full font-medium" style="background:var(--ws-surface2);color:var(--ws-muted)">
                {providerIcon(tr._type)} {providerLabel(tr)}
              </span>
              <div class="flex items-center gap-1.5">
                {#if wishMet}
                  <span class="text-xs font-bold px-2 py-0.5 rounded-full" style="background:rgba(22,163,74,.12);color:var(--ws-green)">
                    🎯 {$t('radarWishMet')}
                  </span>
                {/if}
                {#if tr.booking_url}
                  <a href={tr.booking_url} target="_blank" rel="noopener noreferrer"
                    class="text-xs px-2.5 py-1 rounded-lg font-semibold transition-opacity hover:opacity-80"
                    style="background:var(--ws-accent);color:#fff5ec;text-decoration:none">
                    Buchen ↗
                  </a>
                {/if}
              </div>
            </div>

            <!-- Title + subtitle -->
            <div>
              <div class="font-bold text-sm" style="color:var(--ws-text)">{trackerTitle(tr)}</div>
              <div class="text-xs mt-0.5" style="color:var(--ws-muted)">{trackerSubtitle(tr)}</div>
              {#if tr._type === 'flight' || tr._type === 'google_flight'}
                {@const snap = tr.latest_snapshot}
                {@const showAirline  = snap?.airline}
                {@const showFlight   = snap?.flight_number || snap?.outbound_flight}
                {@const showTimes    = snap?.departure_time && snap?.arrival_time}
                {@const showDuration = snap?.duration_min}
                {#if showAirline || showFlight || showTimes}
                  <div class="flex items-center gap-1.5 mt-1 flex-wrap">
                    <span class="text-xs">✈️</span>
                    {#if showAirline}
                      <span class="text-xs font-semibold" style="color:var(--ws-accent)">{snap.airline}</span>
                    {:else}
                      <span class="text-xs font-semibold" style="color:var(--ws-accent)">{tr._type === 'flight' ? 'Ryanair' : 'Google Flights'}</span>
                    {/if}
                    {#if showFlight}
                      <span class="text-xs font-mono px-1.5 py-0.5 rounded" style="background:var(--ws-surface2);color:var(--ws-muted)">{snap.flight_number || snap.outbound_flight}</span>
                    {/if}
                    {#if showTimes}
                      <span class="text-xs font-mono" style="color:var(--ws-muted)">
                        {snap.departure_time.slice(0,5)} → {snap.arrival_time.slice(0,5)}
                      </span>
                    {/if}
                    {#if showDuration}
                      <span class="text-xs" style="color:var(--ws-muted)">({Math.floor(snap.duration_min/60)}h{snap.duration_min%60}m)</span>
                    {/if}
                  </div>
                {:else}
                  <div class="text-xs mt-1" style="color:var(--ws-muted)">
                    <span>✈️ {tr._type === 'flight' ? 'Ryanair' : 'Google Flights'} · noch kein Preis-Scan</span>
                  </div>
                {/if}
              {/if}
            </div>

            <!-- Inclusions badges -->
            {#if badges.length > 0}
              <div class="flex flex-wrap gap-1.5">
                {#each badges as badge}
                  <span class="text-xs px-2 py-0.5 rounded-full font-medium"
                    style="background:rgba(196,98,45,.08);color:var(--ws-accent)">
                    {badge}
                  </span>
                {/each}
              </div>
            {/if}

            <!-- Price row — Preis links, Datum rechts -->
            <div class="flex items-end justify-between gap-2">
              <div>
                <div class="flex items-center gap-1.5">
                  <div class="text-xs" style="color:var(--ws-muted)">{$t('radarCurrentPrice') || 'Aktuell'}</div>
                  {#if chartState[cKey]?.history?.length >= 2}
                    {@const trend = priceTrend(chartState[cKey].history)}
                    {#if trend?.dir === 'down'}
                      <span class="text-xs font-semibold" style="color:var(--ws-green)">⬇ {trend.pct}%</span>
                    {:else if trend?.dir === 'up'}
                      <span class="text-xs font-semibold" style="color:#ef4444">⬆ {trend.pct}%</span>
                    {/if}
                  {/if}
                </div>
                <div class="font-bold font-mono text-xl" style="color:{price ? 'var(--ws-green)' : 'var(--ws-muted)'}">
                  {price ? price.toFixed(2) + ' €' : '–'}
                </div>
                {#if (tr._type === 'hotel' || tr._type === 'camping') && tr.checkin_date && tr.checkout_date}
                  {@const nights = Math.max(1, Math.round((new Date(tr.checkout_date) - new Date(tr.checkin_date)) / 86400000))}
                  {#if nights > 1 && price}
                    <div class="text-[10px] font-mono" style="color:var(--ws-muted)">Ø {(price/nights).toFixed(2)} {$t('radarPerNight')}</div>
                  {/if}
                {/if}
                {#if chartState[cKey]?.history?.length >= 2 && isTopPrice(chartState[cKey].history, price)}
                  <div class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold mt-0.5"
                    style="background:rgba(234,179,8,.15);color:#ca8a04;border:1px solid rgba(234,179,8,.3)">
                    🏆 Top Preis
                  </div>
                {/if}
              </div>
              {#if s?.fetched_at}
                <div class="text-[10px] text-right" style="color:var(--ws-muted)">
                  Stand<br>{fmtDate(s.fetched_at.slice(0, 10))}
                </div>
              {/if}
            </div>

            <!-- Wunschpreis — prominente eigene Zeile -->
            <div class="rounded-xl border px-3 py-2" style="background:var(--ws-surface2);border-color:{wish ? 'var(--ws-accent)' : 'var(--ws-border)'}">
              <div class="flex items-center justify-between gap-2">
                <span class="text-xs" style="color:var(--ws-muted)">🎯 {$t('radarWishPrice')}</span>
                {#if !wishState[wKey]?.editing}
                  <div class="flex items-center gap-2">
                    <span class="text-sm font-mono font-bold" style="color:{wish ? 'var(--ws-accent)' : 'var(--ws-muted)'}">
                      {wish ? wish.toFixed(2) + ' €' : '–'}
                    </span>
                    <button
                      onclick={() => wishState[wKey] = { editing: true, value: wish?.toString() || '' }}
                      class="text-xs px-2 py-0.5 rounded-lg border"
                      style="border-color:var(--ws-border);color:var(--ws-muted)">✏️ {$t('radarSet')}</button>
                  </div>
                {/if}
              </div>
              {#if wishState[wKey]?.editing}
                <div class="flex items-center gap-1 mt-1.5">
                  <input
                    type="number"
                    bind:value={wishState[wKey].value}
                    min="0"
                    step="1"
                    placeholder="Zielpreis in €"
                    class="flex-1 min-w-0 px-2 py-1 rounded-lg border text-xs font-mono"
                    style={inputStyle}
                    onkeydown={(e) => e.key === 'Enter' && saveWishPrice(tr._type, tr.id, tr._table, wishState[wKey].value)}
                  />
                  <button
                    onclick={() => saveWishPrice(tr._type, tr.id, tr._table, wishState[wKey].value)}
                    disabled={wishState[wKey]?.saving}
                    class="px-2 py-1 rounded-lg text-xs font-semibold shrink-0"
                    style="background:var(--ws-accent);color:#fff">✓</button>
                  <button
                    onclick={() => wishState[wKey] = { editing: false }}
                    class="px-2 py-1 rounded-lg text-xs shrink-0"
                    style="background:var(--ws-surface2);color:var(--ws-muted)">✕</button>
                </div>
              {/if}
            </div>

            <!-- Action buttons — history left, delete far right -->
            <div class="flex items-center gap-2 mt-auto pt-1">
              <button
                onclick={() => toggleChart(tr._type, tr.id)}
                class="px-3 py-1.5 rounded-xl text-xs border transition-colors"
                style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">
                {chartState[cKey]?.open ? '▲' : '📉'} {$t('radarPriceHistory')}
              </button>
              <button
                onclick={() => scrapeTracker(tr)}
                class="px-3 py-1.5 rounded-xl text-xs border transition-colors"
                style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">
                ⟳
              </button>

              <button
                onclick={() => deleteTracker(tr)}
                class="ml-auto px-3 py-1.5 rounded-xl text-xs border transition-colors hover:border-red-400 hover:text-red-400"
                style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">
                ✕
              </button>
            </div>

            <!-- Price history accordion (inline SVG) -->
            {#if chartState[cKey]?.open}
              <div class="pt-3 border-t" style="border-color:var(--ws-border)">
                {#if chartState[cKey]?.loading}
                  <div class="h-24 rounded animate-pulse" style="background:var(--ws-border)"></div>
                {:else if (chartState[cKey]?.history?.length || 0) < 2}
                  <p class="text-xs text-center py-4" style="color:var(--ws-muted)">{$t('radarTooFewData')}</p>
                {:else}
                  {#each [chartPts(chartState[cKey].history, 290, 70, 5)] as cp}
                    <div class="relative h-24">
                      <svg viewBox="0 0 300 80" class="w-full h-full" preserveAspectRatio="none">
                        <defs>
                          <linearGradient id="cg-{tr._type}-{tr.id}" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%"   stop-color="var(--ws-accent)" stop-opacity="0.25"/>
                            <stop offset="100%" stop-color="var(--ws-accent)" stop-opacity="0"/>
                          </linearGradient>
                        </defs>
                        <!-- Y-axis reference lines -->
                        <line x1="0" y1="5" x2="300" y2="5" stroke="var(--ws-border)" stroke-width="0.5" stroke-dasharray="4,4"/>
                        <line x1="0" y1="75" x2="300" y2="75" stroke="var(--ws-green)" stroke-width="0.5" stroke-dasharray="4,4" opacity="0.5"/>
                        <polygon fill="url(#cg-{tr._type}-{tr.id})" points={cp.area}/>
                        <polyline fill="none" stroke="var(--ws-accent)" stroke-width="2" stroke-linejoin="round" points={cp.polyline}/>
                        <!-- Min/Max price markers -->
                        <circle cx={cp.minPt.x} cy={cp.minPt.y} r="3" fill="var(--ws-green)" opacity="0.9"/>
                        <circle cx={cp.maxPt.x} cy={cp.maxPt.y} r="3" fill="#ef4444" opacity="0.6"/>
                      </svg>
                      <div class="absolute top-0 right-0 text-[10px] font-mono" style="color:var(--ws-muted)">{cp.maxP.toFixed(0)}€</div>
                      <div class="absolute bottom-0 right-0 text-[10px] font-mono" style="color:var(--ws-green)">{cp.minP.toFixed(0)}€ ↓min</div>
                      <div class="absolute bottom-0 left-0 text-xs" style="color:var(--ws-muted)">
                        {fmtDate(chartState[cKey].history[0].fetched_at.slice(0, 10))}
                      </div>
                    </div>
                  {/each}
                {/if}
              </div>
            {/if}

          </div>
        {/each}
      </div>
    {/if}
  </div>

</div>







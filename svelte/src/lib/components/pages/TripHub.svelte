<script>
  import { onMount } from 'svelte';
  import { t } from '$lib/i18n.js';
  import { api } from '$lib/api.js';
  import { toast } from '$lib/toast.js';
  import { currentPage, activeWsTripId, priceradarParams } from '$lib/stores.js';

  // ── State ──────────────────────────────────────────────────────────────────
  let trip       = $state(null);
  let todos      = $state([]);
  let loading    = $state(true);
  let newTask    = $state('');
  let addingTodo = $state(false);
  let regenLoading = $state(false);

  // Weather
  let weather    = $state(null);
  let weatherLoad = $state(false);

  // Manual expenses
  let manualExpDraft   = $state('');
  let manualExpEditing = $state(false);
  let manualExpSaving  = $state(false);

  // Tracker slots + budget
  let slots           = $state({ flight: null, hotel: null, camping: null });
  let budgetBreakdown = $state(null);

  // Book modal
  let bookModal  = $state(null);
  let bookPrice  = $state('');
  let bookSaving = $state(false);

  // ── Load ───────────────────────────────────────────────────────────────────
  onMount(async () => {
    const id = $activeWsTripId;
    if (!id) { loading = false; return; }
    await Promise.all([loadTrip(id), loadSlots(id), loadBudget(id)]);
    loading = false;
  });

  async function loadTrip(id) {
    try {
      const res = await api(`/api/ws-trips/${id}`);
      trip  = res;
      todos = res.todos || [];
      manualExpDraft = String(res.manual_expenses || 0);
      // Fetch weather if needed
      if (res.destination && (phase === 'active' || daysUntilStart <= 7)) {
        fetchWeather(res.destination);
      }
    } catch { toast('Trip konnte nicht geladen werden', 'error'); }
  }

  async function loadSlots(id) {
    try { slots = await api(`/api/ws-trips/${id}/trackers`); } catch {}
  }

  async function loadBudget(id) {
    try { budgetBreakdown = await api(`/api/ws-trips/${id}/budget`); } catch {}
  }

  // ── Phase Lifecycle ────────────────────────────────────────────────────────
  const today = new Date().toISOString().slice(0, 10);

  const daysUntilStart = $derived.by(() => {
    if (!trip?.start_date) return 999;
    return Math.ceil((new Date(trip.start_date) - new Date()) / 86400000);
  });

  const phase = $derived.by(() => {
    if (!trip) return 'planning';
    const t_start = trip.start_date || '';
    const t_end   = trip.end_date   || trip.start_date || '';
    if (today > t_end)   return 'archived';
    if (today >= t_start) return 'active';
    return 'planning';
  });

  const isArchived = $derived(phase === 'archived');

  const statusLabel = $derived.by(() => {
    if (!trip) return '';
    if (phase === 'archived') return $t('tripCardExperienced') || 'ERLEBT';
    if (phase === 'active')   return $t('tripPhaseActive')     || 'ON TOUR';
    return { planning: $t('tripHubStatusPlanning'), booked: $t('tripHubStatusBooked'), completed: $t('tripHubStatusDone') }[trip.status] || $t('tripHubStatusPlanning');
  });

  const statusColor = $derived.by(() => {
    if (phase === 'archived') return 'var(--ws-muted)';
    if (phase === 'active')   return 'var(--ws-green)';
    return ({ planning: 'var(--ws-accent)', booked: 'var(--ws-green)', completed: 'var(--ws-muted)' }[trip?.status] || 'var(--ws-accent)');
  });

  const statusPulse = $derived(phase === 'active');

  const countdown = $derived.by(() => {
    if (!trip?.start_date) return null;
    const diff = daysUntilStart;
    if (diff === 0) return $t('tripHubToday');
    if (diff === 1) return $t('tripHubTomorrow');
    if (diff > 0)   return $t('tripHubCountdown').replace('{n}', diff);
    if (phase === 'active') {
      const endDiff = Math.ceil((new Date(trip.end_date) - new Date()) / 86400000);
      if (endDiff >= 0) return ($t('tripPhaseActiveCountdown') || 'Noch {n} Tage').replace('{n}', endDiff + 1);
    }
    return null;
  });

  const heroBg = $derived.by(() => {
    if (!trip) return 'linear-gradient(135deg,#1e293b,#374151)';
    if (phase === 'active')
      return 'linear-gradient(135deg,#0f4c2a 0%,#1a6b3a 50%,#0d3d22 100%)';
    return trip.travel_mode === 'car'
      ? 'linear-gradient(135deg,#1a3a2a 0%,#2d6a4f 60%,#1a4a3a 100%)'
      : 'linear-gradient(135deg,#1a2a4a 0%,var(--ws-accent) 70%,#b84928 100%)';
  });

  // ── Weather ────────────────────────────────────────────────────────────────
  async function fetchWeather(destination) {
    if (!destination || weatherLoad) return;
    weatherLoad = true;
    try {
      const geoRes = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(destination)}&count=1&language=de&format=json`);
      const geoData = await geoRes.json();
      const loc = geoData.results?.[0];
      if (!loc) { weatherLoad = false; return; }
      const wRes = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${loc.latitude}&longitude=${loc.longitude}&current_weather=true&timezone=auto`);
      const wData = await wRes.json();
      const cw = wData.current_weather;
      if (cw) {
        weather = {
          temp:  Math.round(cw.temperature),
          wind:  Math.round(cw.windspeed),
          code:  cw.weathercode,
          icon:  wmoIcon(cw.weathercode),
          city:  loc.name,
        };
      }
    } catch {}
    weatherLoad = false;
  }

  function wmoIcon(code) {
    if (code === 0) return '☀️';
    if (code <= 2) return '🌤️';
    if (code <= 3) return '☁️';
    if (code <= 49) return '🌫️';
    if (code <= 67) return '🌧️';
    if (code <= 77) return '🌨️';
    if (code <= 82) return '🌦️';
    if (code <= 99) return '⛈️';
    return '🌡️';
  }

  // ── Todos ──────────────────────────────────────────────────────────────────
  async function toggleTodo(todo) {
    try {
      await api(`/api/ws-trips/${trip.id}/todos/${todo.id}/toggle`, { method: 'PATCH' });
      todos = todos.map(t => t.id === todo.id ? { ...t, is_done: t.is_done ? 0 : 1 } : t);
    } catch { toast('Fehler', 'error'); }
  }
  async function addTodo() {
    if (!newTask.trim() || addingTodo) return;
    addingTodo = true;
    try {
      await api(`/api/ws-trips/${trip.id}/todos`, { method: 'POST', body: JSON.stringify({ task: newTask.trim(), category: 'general' }) });
      todos = [...todos, { id: Date.now(), task: newTask.trim(), category: 'general', is_done: 0 }];
      newTask = '';
    } catch { toast('Fehler', 'error'); }
    addingTodo = false;
  }
  async function deleteTodo(todo) {
    try {
      await api(`/api/ws-trips/${trip.id}/todos/${todo.id}`, { method: 'DELETE' });
      todos = todos.filter(t => t.id !== todo.id);
    } catch { toast('Fehler', 'error'); }
  }
  async function regenerateTodos() {
    if (regenLoading) return;
    regenLoading = true;
    try {
      const res = await api(`/api/ws-trips/${trip.id}/todos/regenerate`, { method: 'POST' });
      todos = (res.todos || []).map((t, i) => ({ id: Date.now() + i, ...t, is_done: 0 }));
      toast(`✨ ${todos.length} To-Dos neu generiert`, 'success');
      await loadTrip(trip.id);
    } catch (e) { toast(e.message || 'Fehler', 'error'); }
    regenLoading = false;
  }

  function catIcon(cat) {
    return { booking: '🎫', documents: '📄', packing: '🧳', general: '✅' }[cat] || '✅';
  }
  const donePct = $derived(todos.length ? Math.round(todos.filter(t => t.is_done).length / todos.length * 100) : 0);

  // ── Manual Expenses ────────────────────────────────────────────────────────
  async function saveManualExp() {
    manualExpSaving = true;
    try {
      const val = parseFloat(manualExpDraft) || 0;
      await api(`/api/ws-trips/${trip.id}/manual-expenses`, {
        method: 'PATCH',
        body: JSON.stringify({ manual_expenses: val }),
      });
      trip = { ...trip, manual_expenses: val };
      manualExpEditing = false;
      toast($t('hubManualExpSaved') || 'Manuelle Ausgaben gespeichert ✓', 'success');
      await loadBudget(trip.id);
    } catch (e) { toast(e.message, 'error'); }
    manualExpSaving = false;
  }

  // ── PriceRadar deep-link ───────────────────────────────────────────────────
  function goSearch(type) {
    if (trip) {
      priceradarParams.set({
        destination: trip.destination || '',
        dateFrom:    trip.start_date  || '',
        dateTo:      trip.end_date    || '',
        adults:      trip.adults      || 2,
        children:    trip.children    || 0,
        homeAirport: trip.home_airport || '',
        _fromTripHub: trip.id,
        _searchType:  type,
      });
    }
    currentPage.set('priceradar');
  }

  // ── Book modal ─────────────────────────────────────────────────────────────
  function openBookModal(trackerId, trackerType, slotKey) {
    bookModal = { trackerId, trackerType, slotKey };
    bookPrice = '';
  }
  function closeBookModal() { bookModal = null; bookPrice = ''; bookSaving = false; }

  async function confirmBook() {
    if (!bookModal || !bookPrice) return;
    bookSaving = true;
    try {
      await api(`/api/ws-trips/${trip.id}/trackers/${bookModal.trackerId}/book`, {
        method: 'POST',
        body: JSON.stringify({ booked_price: parseFloat(bookPrice), tracker_type: bookModal.trackerType }),
      });
      toast('✅ Als gebucht markiert!', 'success');
      closeBookModal();
      await loadSlots(trip.id);
      await loadBudget(trip.id);
    } catch (e) { toast(e.message, 'error'); }
    bookSaving = false;
  }

  async function unbook(trackerId, trackerType) {
    try {
      await api(`/api/ws-trips/${trip.id}/trackers/${trackerId}/book?tracker_type=${trackerType}`, { method: 'DELETE' });
      toast('Buchung zurückgesetzt', 'success');
      await loadSlots(trip.id);
      await loadBudget(trip.id);
    } catch (e) { toast(e.message, 'error'); }
  }

  // Trigger weather load reactively after trip is loaded
  $effect(() => {
    if (trip?.destination && (phase === 'active' || daysUntilStart <= 7) && !weather && !weatherLoad) {
      fetchWeather(trip.destination);
    }
  });
</script>

<!-- ── Book Modal ──────────────────────────────────────────────────────────── -->
{#if bookModal}
  <div class="fixed inset-0 z-50 flex items-center justify-center"
    style="background:rgba(0,0,0,.48);backdrop-filter:blur(4px)"
    role="dialog" aria-modal="true">
    <div class="w-full max-w-xs mx-4 rounded-2xl border p-6 space-y-4 shadow-2xl"
      style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h3 class="font-bold text-base" style="color:var(--ws-text)">{$t('hubSlotMarkBooked')}</h3>
      <div>
        <label class="text-xs font-semibold uppercase tracking-wider mb-1 block" style="color:var(--ws-muted)">{$t('hubSlotBookedPrice')}</label>
        <div class="flex items-center gap-2">
          <input type="number" min="0" step="0.01"
            bind:value={bookPrice}
            placeholder={$t('hubSlotEnterPrice')}
            onkeydown={(e) => e.key === 'Enter' && confirmBook()}
            class="flex-1 px-3 py-2 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ws-accent)]"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
          <span class="text-sm" style="color:var(--ws-muted)">€</span>
        </div>
      </div>
      <div class="flex gap-3">
        <button onclick={closeBookModal}
          class="flex-1 py-2.5 rounded-xl border text-sm font-semibold hover:opacity-70"
          style="border-color:var(--ws-border);color:var(--ws-muted)">{$t('hubSlotCancelBook')}</button>
        <button onclick={confirmBook} disabled={!bookPrice || bookSaving}
          class="flex-1 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-40"
          style="background:var(--ws-green,#2d6a4f);color:#fff">
          {bookSaving ? '⏳' : $t('hubSlotSavePrice')}
        </button>
      </div>
    </div>
  </div>
{/if}

<div class="max-w-2xl mx-auto space-y-5 pb-10">

  <button onclick={() => currentPage.set('home')}
    class="flex items-center gap-1.5 text-sm font-semibold hover:opacity-70 transition-opacity"
    style="color:var(--ws-muted)">
    {$t('tripHubBack')}
  </button>

  {#if loading}
    <div class="rounded-2xl animate-pulse h-52" style="background:var(--ws-surface2)"></div>
    <div class="rounded-2xl animate-pulse h-32" style="background:var(--ws-surface2)"></div>
  {:else if !trip}
    <div class="rounded-2xl p-10 text-center" style="background:var(--ws-surface2)">
      <p class="text-4xl mb-3">🗺️</p>
      <p class="font-semibold" style="color:var(--ws-text)">Kein Trip gefunden</p>
      <button onclick={() => currentPage.set('home')} class="mt-4 text-sm" style="color:var(--ws-accent)">Zurück</button>
    </div>
  {:else}

    <!-- ── Hero ─────────────────────────────────────────────────────────────── -->
    <div class="relative rounded-2xl overflow-hidden" style="min-height:200px;background:{heroBg}">
      <div class="absolute inset-0 opacity-10" style="background-image:radial-gradient(circle at 20% 80%,rgba(255,255,255,.2) 0%,transparent 50%)"></div>
      <!-- Picsum background for active trips -->
      {#if phase === 'active' && trip.id}
        <img src="https://picsum.photos/seed/{trip.id}/800/300"
          alt=""
          class="absolute inset-0 w-full h-full object-cover opacity-20"
          aria-hidden="true" />
      {/if}
      <div class="relative z-10 p-6 flex flex-col justify-between" style="min-height:200px">
        <div class="flex items-start justify-between">
          <div class="flex flex-col gap-2">
            <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold"
              style="background:rgba(255,255,255,.15);color:#fff;backdrop-filter:blur(8px)">
              {#if statusPulse}
                <span class="w-1.5 h-1.5 rounded-full animate-pulse" style="background:{statusColor}"></span>
              {:else}
                <span class="w-1.5 h-1.5 rounded-full" style="background:{statusColor}"></span>
              {/if}
              {statusLabel}
            </span>
            {#if countdown}
              <span class="text-sm font-semibold" style="color:rgba(255,255,255,.85)">{countdown}</span>
            {/if}
          </div>
          <!-- Weather widget (active or < 7 days) -->
          <div class="flex items-center gap-2">
            {#if weather}
              <div class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold"
                style="background:rgba(255,255,255,.15);color:#fff;backdrop-filter:blur(8px)">
                <span class="text-base">{weather.icon}</span>
                <span>{weather.temp}°C</span>
                <span style="opacity:.7">{weather.city}</span>
              </div>
            {:else if weatherLoad}
              <div class="px-3 py-1.5 rounded-xl text-xs" style="background:rgba(255,255,255,.1);color:rgba(255,255,255,.6)">
                🌡️ …
              </div>
            {/if}
            <span class="text-2xl">{trip.travel_mode === 'car' ? '🚗' : '✈️'}</span>
          </div>
        </div>
        <div>
          <h1 class="text-2xl font-bold leading-tight mb-1"
            style="font-family:var(--ws-serif);color:#fff;text-shadow:0 2px 12px rgba(0,0,0,.4)">
            {trip.title || trip.destination || $t('tripHubTitle')}
          </h1>
          <div class="flex items-center gap-3 flex-wrap">
            {#if trip.destination}
              <span class="text-sm font-mono" style="color:rgba(255,255,255,.75)">📍 {trip.destination}</span>
            {/if}
            {#if trip.start_date}
              <span class="text-sm font-mono" style="color:rgba(255,255,255,.65)">
                📅 {trip.start_date}{trip.end_date && trip.end_date !== trip.start_date ? ' → ' + trip.end_date : ''}
              </span>
            {/if}
          </div>
        </div>
      </div>
    </div>

    <!-- ── Smart Action Slots (hidden in active + archived) ─────────────────── -->
    {#if phase === 'planning'}
    <div class="grid grid-cols-2 gap-3">
      {#each [
        { key: 'flight', icon: '✈️', label: $t('tripHubPlanArrival'), emptyLabel: $t('hubSlotFlightEmpty'), type: 'flight' },
        { key: 'hotel',  icon: '🏨', label: $t('tripHubFindAccom'),  emptyLabel: $t('hubSlotHotelEmpty'),  type: 'hotel' },
      ] as slot}
        {@const tracker     = slots[slot.key] || slots.camping}
        {@const isBooked    = tracker?.is_booked}
        {@const trackerType = tracker?._type || slot.type}
        {@const isCarSlot   = slot.key === 'flight' && trip?.travel_mode === 'car'}

        <div class="rounded-2xl border overflow-hidden transition-all {isCarSlot ? 'opacity-40 grayscale' : ''}"
          style="border-color:{isBooked ? 'var(--ws-green,#2d6a4f)' : 'var(--ws-border)'};background:var(--ws-surface2);{isBooked ? 'box-shadow:0 0 0 2px rgba(22,163,74,.15)' : ''}">

          {#if !tracker}
            <button onclick={() => goSearch(slot.type)}
              class="w-full flex flex-col items-center gap-2 p-5 transition-all hover:opacity-85 active:scale-[.98]">
              <span class="text-3xl">{slot.icon}</span>
              <span class="text-sm font-semibold text-center" style="color:var(--ws-text)">{slot.emptyLabel}</span>
              {#if trip.start_date}
                <span class="text-[10px] px-2 py-0.5 rounded-full font-medium" style="background:color-mix(in srgb,var(--ws-accent) 12%,var(--ws-surface));color:var(--ws-accent)">
                  {$t('hubSearchHint')}
                </span>
              {/if}
              <span class="text-xs" style="color:var(--ws-muted)">PriceRadar →</span>
            </button>

          {:else if isBooked}
            <div class="p-4 space-y-2">
              <div class="flex items-center gap-2">
                <span class="text-xl">{slot.icon}</span>
                <span class="text-xs font-bold px-2 py-0.5 rounded-full"
                  style="background:rgba(22,163,74,.15);color:var(--ws-green,#2d6a4f)">
                  {$t('hubSlotBooked')}
                </span>
              </div>
              <div class="text-lg font-bold font-mono" style="color:var(--ws-text)">
                {parseFloat(tracker.booked_price).toFixed(2)} €
              </div>
              <div class="text-xs" style="color:var(--ws-muted)">{$t('hubSlotBookedPrice')}</div>
              {#if tracker.booking_url}
                <a href={tracker.booking_url} target="_blank" rel="noopener noreferrer"
                  class="block text-center text-xs font-bold px-3 py-1.5 rounded-lg transition-opacity hover:opacity-80"
                  style="background:var(--ws-accent);color:#fff5ec;text-decoration:none">
                  {$t('hubSlotBook')}
                </a>
              {/if}
              <button onclick={() => unbook(tracker.id, trackerType)}
                class="text-[10px] w-full text-center hover:opacity-70 transition-opacity"
                style="color:var(--ws-muted)">↩ zurücksetzen</button>
            </div>

          {:else}
            <div class="p-4 space-y-2">
              <div class="flex items-center justify-between">
                <span class="text-xl">{slot.icon}</span>
                <span class="text-[10px] font-semibold px-2 py-0.5 rounded-full"
                  style="background:color-mix(in srgb,var(--ws-accent) 12%,var(--ws-surface));color:var(--ws-accent)">
                  {$t('hubSlotTracking')}
                </span>
              </div>
              {#if tracker.latest_snapshot?.total_price}
                <div>
                  <div class="text-xs" style="color:var(--ws-muted)">{$t('hubSlotCurrentPrice')}</div>
                  <div class="text-lg font-bold font-mono" style="color:var(--ws-text)">
                    {parseFloat(tracker.latest_snapshot.total_price).toFixed(2)} €
                  </div>
                </div>
              {/if}
              <div class="flex gap-2">
                {#if tracker.booking_url}
                  <a href={tracker.booking_url} target="_blank" rel="noopener noreferrer"
                    class="flex-1 text-center text-xs font-bold px-2 py-1.5 rounded-lg transition-opacity hover:opacity-80"
                    style="background:var(--ws-accent);color:#fff5ec;text-decoration:none">
                    {$t('hubSlotBook')}
                  </a>
                {/if}
                <button onclick={() => openBookModal(tracker.id, trackerType, slot.key)}
                  class="flex-1 text-xs font-semibold px-2 py-1.5 rounded-lg border transition-all hover:opacity-80"
                  style="border-color:var(--ws-green,#2d6a4f);color:var(--ws-green,#2d6a4f)">
                  {$t('hubSlotMarkBooked')}
                </button>
              </div>
            </div>
          {/if}
        </div>
      {/each}
    </div>
    {/if}

    <!-- ── Budget Breakdown ──────────────────────────────────────────────────── -->
    {#if budgetBreakdown?.has_budget}
      <div class="rounded-2xl border p-4 space-y-3" style="background:var(--ws-surface2);border-color:var(--ws-border)">
        <h3 class="font-bold text-sm" style="color:var(--ws-text)">💶 Budget</h3>
        <div class="space-y-2">
          {#each [
            [$t('hubBudgetTotal'),  budgetBreakdown.total_budget,  false],
            [$t('hubBudgetFlight'), budgetBreakdown.booked_flight, true],
            [$t('hubBudgetHotel'),  budgetBreakdown.booked_hotel,  true],
          ] as [label, val, indent]}
            {#if val > 0 || !indent}
              <div class="flex items-center justify-between {indent ? 'pl-3 border-l-2' : ''}"
                style="{indent ? 'border-color:var(--ws-border)' : ''}">
                <span class="text-xs" style="color:var(--ws-muted)">{label}</span>
                <span class="text-sm font-mono font-bold" style="color:var(--ws-text)">
                  {indent ? '−' : ''}{parseFloat(val).toFixed(0)} €
                </span>
              </div>
            {/if}
          {/each}

          <!-- Manual expenses row -->
          <div class="flex items-center justify-between pl-3 border-l-2" style="border-color:var(--ws-border)">
            <span class="text-xs" style="color:var(--ws-muted)">💵 {$t('hubManualExp') || 'Barausgaben'}</span>
            {#if manualExpEditing}
              <div class="flex items-center gap-1">
                <input type="number" min="0" step="1"
                  bind:value={manualExpDraft}
                  class="w-20 px-2 py-0.5 text-xs rounded-lg border font-mono focus:outline-none"
                  style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)"
                  onkeydown={(e) => { if (e.key==='Enter') saveManualExp(); if (e.key==='Escape') manualExpEditing=false; }} />
                <span class="text-xs" style="color:var(--ws-muted)">€</span>
                <button onclick={saveManualExp} disabled={manualExpSaving}
                  class="px-2 py-0.5 rounded text-xs font-bold disabled:opacity-40"
                  style="background:var(--ws-accent);color:#fff5ec">{manualExpSaving ? '⏳' : '✓'}</button>
                <button onclick={() => manualExpEditing=false} class="text-xs px-1" style="color:var(--ws-muted)">✕</button>
              </div>
            {:else}
              <div class="flex items-center gap-2">
                <span class="text-sm font-mono font-bold" style="color:var(--ws-text)">
                  −{parseFloat(trip.manual_expenses || 0).toFixed(0)} €
                </span>
                <button onclick={() => { manualExpEditing=true; manualExpDraft=String(trip.manual_expenses||0); }}
                  class="text-[10px] px-1.5 py-0.5 rounded border hover:opacity-70"
                  style="border-color:var(--ws-border);color:var(--ws-muted)">✏️</button>
              </div>
            {/if}
          </div>

          <!-- On-site remainder -->
          <div class="flex items-center justify-between pt-2 mt-1 border-t" style="border-color:var(--ws-border)">
            <span class="text-sm font-semibold" style="color:var(--ws-text)">{$t('hubBudgetOnSite')}</span>
            <span class="text-lg font-bold font-mono"
              style="color:{budgetBreakdown.on_site_budget >= 0 ? 'var(--ws-green,#2d6a4f)' : '#ef4444'}">
              {parseFloat(budgetBreakdown.on_site_budget).toFixed(0)} €
            </span>
          </div>
        </div>
        {#if budgetBreakdown.total_budget > 0}
          {@const spent = budgetBreakdown.booked_flight + budgetBreakdown.booked_hotel + (budgetBreakdown.manual_expenses || 0)}
          {@const pct   = Math.min(100, (spent / budgetBreakdown.total_budget) * 100)}
          <div class="h-2 rounded-full overflow-hidden" style="background:var(--ws-border)">
            <div class="h-full rounded-full transition-all duration-700"
              style="width:{pct}%;background:{pct > 85 ? '#ef4444' : 'var(--ws-green,#2d6a4f)'}"></div>
          </div>
        {/if}
      </div>
    {/if}

    <!-- ── Active Phase Placeholders ────────────────────────────────────────── -->
    {#if phase === 'active'}
      <div class="grid grid-cols-2 gap-3">
        <!-- Reisetagebuch placeholder -->
        <div class="rounded-2xl border-2 border-dashed p-5 flex flex-col items-center gap-2 text-center"
          style="border-color:color-mix(in srgb,var(--ws-accent) 30%,var(--ws-border));background:color-mix(in srgb,var(--ws-accent) 4%,var(--ws-surface))">
          <span class="text-3xl">📓</span>
          <span class="text-xs font-semibold" style="color:var(--ws-text)">{$t('placeholderJournal') || 'Reisetagebuch'}</span>
          <span class="text-[10px] px-2 py-0.5 rounded-full font-bold" style="background:rgba(196,98,45,.12);color:var(--ws-accent)">Coming Soon</span>
        </div>
        <!-- Tagesausflüge placeholder -->
        <div class="rounded-2xl border-2 border-dashed p-5 flex flex-col items-center gap-2 text-center"
          style="border-color:color-mix(in srgb,var(--ws-accent) 30%,var(--ws-border));background:color-mix(in srgb,var(--ws-accent) 4%,var(--ws-surface))">
          <span class="text-3xl">🗺️</span>
          <span class="text-xs font-semibold" style="color:var(--ws-text)">{$t('placeholderDayTrips') || 'Tagesausflüge'}</span>
          <span class="text-[10px] px-2 py-0.5 rounded-full font-bold" style="background:rgba(196,98,45,.12);color:var(--ws-accent)">Coming Soon</span>
        </div>
      </div>
    {/if}

    <!-- ── Archived Phase Placeholder ───────────────────────────────────────── -->
    {#if phase === 'archived'}
      <div class="rounded-2xl border-2 border-dashed p-6 flex flex-col items-center gap-2 text-center"
        style="border-color:color-mix(in srgb,var(--ws-muted) 40%,var(--ws-border));background:color-mix(in srgb,var(--ws-muted) 4%,var(--ws-surface))">
        <span class="text-4xl">🖼️</span>
        <span class="text-sm font-semibold" style="color:var(--ws-text)">{$t('placeholderGallery') || 'Foto-Galerie (Immich)'}</span>
        <span class="text-xs" style="color:var(--ws-muted)">{$t('placeholderGalleryHint') || 'Verknüpfe deine Immich-Instanz für automatische Reisefotos'}</span>
        <span class="text-[10px] px-3 py-0.5 rounded-full font-bold mt-1" style="background:rgba(100,100,100,.12);color:var(--ws-muted)">Coming Soon</span>
      </div>
    {/if}

    <!-- ── Checkliste ────────────────────────────────────────────────────────── -->
    <div class="rounded-2xl border overflow-hidden" style="border-color:var(--ws-border)">
      <div class="flex items-center justify-between px-5 py-3.5 border-b" style="background:var(--ws-surface2);border-color:var(--ws-border)">
        <div class="flex items-center gap-2">
          <span class="font-bold text-sm" style="color:var(--ws-text)">{$t('tripHubTodos')}</span>
          {#if todos.length > 0}
            <span class="text-xs px-2 py-0.5 rounded-full font-semibold"
              style="background:color-mix(in srgb,var(--ws-accent) 15%,var(--ws-surface));color:var(--ws-accent)">
              {todos.filter(t => t.is_done).length}/{todos.length}
            </span>
          {/if}
        </div>
        <div class="flex items-center gap-2">
          {#if todos.length > 0}
            <div class="w-24 h-1.5 rounded-full overflow-hidden" style="background:var(--ws-border)">
              <div class="h-full rounded-full transition-all duration-500"
                style="width:{donePct}%;background:{donePct === 100 ? 'var(--ws-green)' : 'var(--ws-accent)'}"></div>
            </div>
            <span class="text-xs font-mono" style="color:var(--ws-muted)">{donePct}%</span>
          {/if}
          <!-- Regenerate button (planning phase only) -->
          {#if phase === 'planning'}
            <button onclick={regenerateTodos} disabled={regenLoading}
              class="text-xs px-2 py-1 rounded-lg border transition-all hover:opacity-80 disabled:opacity-40"
              style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-muted)">
              {regenLoading ? '⏳' : ($t('hubRegenTodos') || '🔄')}
            </button>
          {/if}
        </div>
      </div>
      <div class="divide-y" style="border-color:var(--ws-border)">
        {#if todos.length === 0}
          <div class="px-5 py-8 text-center text-sm" style="color:var(--ws-muted)">{$t('tripHubNoTodos')}</div>
        {:else}
          {#each todos as todo}
            <div class="flex items-center gap-3 px-5 py-3" style="background:var(--ws-surface);{todo.is_done ? 'opacity:0.5' : ''}">
              <button onclick={() => !isArchived && toggleTodo(todo)}
                class="w-5 h-5 rounded-md border-2 flex items-center justify-center shrink-0 transition-all {isArchived ? 'cursor-default' : ''}"
                style={todo.is_done ? 'background:var(--ws-green);border-color:var(--ws-green)' : 'background:transparent;border-color:var(--ws-border)'}>
                {#if todo.is_done}<span class="text-[10px] text-white font-bold">✓</span>{/if}
              </button>
              <span class="text-base shrink-0">{catIcon(todo.category)}</span>
              <span class="flex-1 text-sm" style="color:var(--ws-text);{todo.is_done ? 'text-decoration:line-through' : ''}">{todo.task}</span>
              {#if !isArchived}<button onclick={() => deleteTodo(todo)} class="text-sm shrink-0 px-1 hover:opacity-70" style="color:var(--ws-muted)">✕</button>{/if}
            </div>
          {/each}
        {/if}
      </div>
      {#if !isArchived}
        <div class="flex items-center gap-2 px-4 py-3 border-t" style="border-color:var(--ws-border);background:var(--ws-surface2)">
          <input bind:value={newTask} placeholder={$t('tripHubTodoPlaceholder')}
            onkeydown={(e) => e.key === 'Enter' && addTodo()}
            class="flex-1 px-3 py-1.5 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ws-accent)] bg-transparent"
            style="border-color:var(--ws-border);color:var(--ws-text)"/>
          <button onclick={addTodo} disabled={!newTask.trim() || addingTodo}
            class="px-3 py-1.5 rounded-xl text-xs font-bold disabled:opacity-40"
            style="background:var(--ws-accent);color:#fff5ec">
            {addingTodo ? '⏳' : '+'}
          </button>
        </div>
      {/if}
    </div>

  {/if}
</div>

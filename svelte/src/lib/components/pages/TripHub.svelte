<script>
  /**
   * TripHub.svelte — modular container.
   * All logic delegated to dedicated widget components.
   */
  import { onMount } from 'svelte';
  import { t } from '$lib/i18n.js';
  import { api } from '$lib/api.js';
  import { toast } from '$lib/toast.js';
  import { currentPage, activeWsTripId, priceradarParams, previousPage, activeMyTripsTab } from '$lib/stores.js';
  import { get as storeGet } from 'svelte/store';

  import WeatherWidget   from '$lib/components/triphub/WeatherWidget.svelte';
  import BudgetWidget    from '$lib/components/triphub/BudgetWidget.svelte';
  import ChecklistWidget from '$lib/components/triphub/ChecklistWidget.svelte';
  import SlotWidget      from '$lib/components/triphub/SlotWidget.svelte';
  import { destinationGradient } from '$lib/components/triphub/helpers.js';
  import TripEditModal    from '$lib/components/triphub/TripEditModal.svelte';
  import ImmichGallery   from '$lib/components/triphub/ImmichGallery.svelte';
  import { fmtDate, today, getTripPhase, daysBetween } from '$lib/utils.js';

  // ── State ───────────────────────────────────────────────────────────────
  let trip            = $state(null);
  let todos           = $state([]);
  let loading         = $state(true);
  let regenLoading    = $state(false);
  let slots           = $state({ flight: null, hotel: null, camping: null });
  let budgetBreakdown = $state(null);
  let bookModal       = $state(null);
  let bookPrice       = $state('');
  let bookSaving      = $state(false);
  let deleteModal     = $state(false);
  let deleteLinkedTrackers = $state([]);
  let deleteLoading   = $state(false);
  let manualExpEditing = $state(false);
  let manualExpDraft   = $state('');
  let manualExpSaving  = $state(false);

  // ── Trip-Edit-Modal (Block 7: kosmetischer Titel vs. Geo-Ort) ────────────
  let editModal = $state(false);

  // ── Hero-Bild (Unsplash mit Caching + Attribution) ────────────────────────
  let heroImgUrl        = $state(null);
  let heroImgAuthor     = $state('');
  let heroImgAuthorUrl  = $state('');
  let heroImgError      = $state(false);
  const UTM = '?utm_source=wandersuite&utm_medium=referral';

  async function loadHeroImage(t) {
    if (!t) return;

    // 1. Gecachtes Bild aus Trip-DB nutzen
    if (t.image_url) {
      heroImgUrl       = t.image_url;
      heroImgAuthor    = t.image_author    || '';
      heroImgAuthorUrl = t.image_author_url || '';
      return;
    }

    // 2. Destination für Unsplash-Suche ermitteln
    const dest = t.destination || t.title || '';
    if (!dest) return;

    try {
      const res = await api(`/api/discovery/trip-image?destination=${encodeURIComponent(dest)}&source=unsplash`);
      if (!res?.image_url) return;

      heroImgUrl       = res.image_url;
      heroImgAuthor    = res.author_name  || '';
      heroImgAuthorUrl = res.author_url   || '';

      // 3. Sofort am Backend cachen (fire-and-forget)
      api(`/api/ws-trips/${t.id}/image`, {
        method: 'PATCH',
        body: JSON.stringify({
          image_url:        res.image_url,
          image_author:     res.author_name || null,
          image_author_url: res.author_url  || null,
        }),
      }).catch(() => {});
    } catch { /* kein Bild verfügbar */ }
  }

  // ── Load ─────────────────────────────────────────────────────────────────
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
      manualExpDraft = String(res.manual_expenses ?? 0);
      // Hero-Bild laden (gecacht oder neu)
      await loadHeroImage(res);
    } catch { toast('Trip konnte nicht geladen werden', 'error'); }
  }

  async function loadSlots(id) {
    try { slots = await api(`/api/ws-trips/${id}/trackers`); } catch {}
  }

  async function loadBudget(id) {
    try { budgetBreakdown = await api(`/api/ws-trips/${id}/budget`); } catch {}
  }

  // ── Phase Lifecycle ──────────────────────────────────────────────────────
  const daysUntilStart = $derived.by(() => {
    if (!trip?.start_date) return 999;
    const startMs = new Date(trip.start_date + 'T00:00:00').getTime();
    const nowMs   = new Date(today + 'T00:00:00').getTime();
    return Math.ceil((startMs - nowMs) / 86400000);
  });

  const phase = $derived(getTripPhase(trip));

  const isArchived  = $derived(phase === 'archived');

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
      const endMs  = new Date((trip.end_date || trip.start_date) + 'T00:00:00').getTime();
      const nowMs  = new Date(today + 'T00:00:00').getTime();
      const endDiff = Math.ceil((endMs - nowMs) / 86400000);
      if (endDiff >= 0) return ($t('tripPhaseActiveCountdown') || 'Noch {n} Tage').replace('{n}', endDiff + 1);
    }
    return null;
  });

  // Generative gradient — no external images
  const heroBg = $derived.by(() => {
    if (!trip) return 'linear-gradient(135deg,#1e293b,#374151)';
    if (phase === 'active') return 'linear-gradient(135deg,#0f4c2a 0%,#1a6b3a 50%,#0d3d22 100%)';
    return destinationGradient(trip.destination || trip.title, trip.travel_mode);
  });

  // ── Smart Back-Button ────────────────────────────────────────────────────
  // FIX 5: previousPage store is set by MyTrips/Dashboard before navigating here
  function navigateBack() {
    const prev = storeGet(previousPage);
    // prev holds the MyTrips tab id — MyTrips lives at currentPage='mytrips'
    const myTripsTabs = ['overview','planned','ontour','archive','bucketlist'];
    if (myTripsTabs.includes(prev)) {
      activeMyTripsTab.set(prev);   // restore the correct tab
      currentPage.set('mytrips');   // FIX: was 'home', correct page is 'mytrips'
    } else {
      // fallback: go back to wherever we came from, default mytrips
      currentPage.set(prev && prev !== 'triphub' ? prev : 'mytrips');
    }
  }

  // ── Todos ────────────────────────────────────────────────────────────────
  async function toggleTodo(todo) {
    try {
      await api(`/api/ws-trips/${trip.id}/todos/${todo.id}/toggle`, { method: 'PATCH' });
      todos = todos.map(t => t.id === todo.id ? { ...t, is_done: t.is_done ? 0 : 1 } : t);
    } catch { toast('Fehler', 'error'); }
  }

  async function addTodo(task, due_date = null) {
    try {
      await api(`/api/ws-trips/${trip.id}/todos`, {
        method: 'POST',
        body: JSON.stringify({ task, category: 'general', due_date }),
      });
      todos = [...todos, { id: Date.now(), task, category: 'general', is_done: 0, due_date }];
    } catch { toast('Fehler', 'error'); }
  }

  async function deleteTodo(todo) {
    try {
      await api(`/api/ws-trips/${trip.id}/todos/${todo.id}`, { method: 'DELETE' });
      todos = todos.filter(t => t.id !== todo.id);
    } catch { toast('Fehler', 'error'); }
  }

  // FIX: regen available in ALL phases
  async function regenerateTodos() {
    if (regenLoading) return;
    regenLoading = true;
    try {
      const res = await api(`/api/ws-trips/${trip.id}/todos/regenerate`, { method: 'POST' });
      todos = (res.todos || []).map((t, i) => ({ id: Date.now() + i, ...t, is_done: 0 }));
      toast(`✨ ${todos.length} To-Dos neu generiert`, 'success');
    } catch (e) { toast(e.message || 'Fehler', 'error'); }
    regenLoading = false;
  }

  // ── Manual Expenses ──────────────────────────────────────────────────────
  async function saveManualExp() {
    manualExpSaving = true;
    try {
      const raw = String(manualExpDraft).replace(',', '.');
      const val = isFinite(parseFloat(raw)) ? Math.max(0, parseFloat(raw)) : 0;
      await api(`/api/ws-trips/${trip.id}/manual-expenses`, {
        method: 'PATCH',
        body: JSON.stringify({ manual_expenses: val }),
      });
      trip = { ...trip, manual_expenses: val };
      manualExpEditing = false;
      toast($t('hubManualExpSaved') || 'Gespeichert ✓', 'success');
      await loadBudget(trip.id);
    } catch (e) { toast(e.message, 'error'); }
    manualExpSaving = false;
  }

  // ── PriceRadar deep-link ─────────────────────────────────────────────────
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

  // ── Book modal ───────────────────────────────────────────────────────────
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

  // ── Delete Trip ──────────────────────────────────────────────────────────
  async function openDeleteModal() {
    deleteModal = true;
    deleteLinkedTrackers = [];
    try {
      const sl = await api(`/api/ws-trips/${trip.id}/trackers`);
      deleteLinkedTrackers = Object.values(sl || {}).filter(Boolean);
    } catch {}
  }

  async function confirmDelete(mode) {
    deleteLoading = true;
    try {
      await api(`/api/ws-trips/${trip.id}?mode=${mode}`, { method: 'DELETE' });
      toast(mode === 'all' ? '🗑️ Reise + Tracker gelöscht' : '🗑️ Reise gelöscht', 'success');
      deleteModal = false;
      currentPage.set('home');
    } catch (e) { toast(e.message, 'error'); }
    deleteLoading = false;
  }
</script>

<!-- ── Edit-Modal (Block 7: Titel vs. Geodaten) ──────────────────────────── -->
<TripEditModal
  bind:open={editModal}
  {trip}
  onsaved={(fields) => {
    trip = { ...trip, ...fields,
      lat: fields.lat ?? trip.lat,
      lon: fields.lon ?? trip.lon,
    };
  }}
/>

<!-- ── Book Modal ─────────────────────────────────────────────────────────── -->
{#if bookModal}
  <div class="fixed inset-0 z-50 flex items-center justify-center"
    style="background:rgba(0,0,0,.48);backdrop-filter:blur(4px)" role="dialog" aria-modal="true">
    <div class="w-full max-w-xs mx-4 rounded-2xl border p-6 space-y-4 shadow-2xl"
      style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h3 class="font-bold text-base" style="color:var(--ws-text)">{$t('hubSlotMarkBooked')}</h3>
      <div class="flex items-center gap-2">
        <input type="number" min="0" step="0.01" bind:value={bookPrice}
          placeholder={$t('hubSlotEnterPrice')}
          onkeydown={(e) => e.key === 'Enter' && confirmBook()}
          class="flex-1 px-3 py-2 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ws-accent)]"
          style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
        <span class="text-sm" style="color:var(--ws-muted)">€</span>
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

<!-- ── Delete Modal ──────────────────────────────────────────────────────── -->
{#if deleteModal}
  <div class="fixed inset-0 z-50 flex items-center justify-center"
    style="background:rgba(0,0,0,.55);backdrop-filter:blur(4px)" role="dialog" aria-modal="true">
    <div class="w-full max-w-sm mx-4 rounded-2xl border p-6 space-y-4 shadow-2xl"
      style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h3 class="font-bold text-base" style="color:#ef4444">🗑️ Reise löschen?</h3>
      {#if deleteLinkedTrackers.length > 0}
        <div class="rounded-xl border p-3 space-y-1.5"
          style="background:color-mix(in srgb,#ef4444 8%,var(--ws-surface));border-color:color-mix(in srgb,#ef4444 25%,var(--ws-border))">
          <p class="text-xs font-semibold" style="color:#ef4444">⚠️ {deleteLinkedTrackers.length} verknüpfte Tracker:</p>
          {#each deleteLinkedTrackers as tr}
            <div class="text-xs px-2 py-1 rounded-lg" style="background:var(--ws-surface2);color:var(--ws-muted)">
              {tr._type === 'flight' ? '✈️' : tr._type === 'google_flight' ? '🔍' : tr._type === 'hotel' ? '🏨' : '🏕️'}
              {tr.destination || tr.origin || 'Tracker #' + tr.id}
            </div>
          {/each}
        </div>
      {:else}
        <p class="text-sm" style="color:var(--ws-muted)">Keine verknüpften Tracker.</p>
      {/if}
      <div class="space-y-2">
        {#if deleteLinkedTrackers.length > 0}
          <button onclick={() => confirmDelete('trip_only')} disabled={deleteLoading}
            class="w-full py-2.5 rounded-xl border text-sm font-semibold hover:opacity-80 disabled:opacity-40"
            style="border-color:var(--ws-border);color:var(--ws-text);background:var(--ws-surface2)">
            {deleteLoading ? '⏳' : '🔓 Nur Reise löschen (Tracker bleiben)'}
          </button>
          <button onclick={() => confirmDelete('all')} disabled={deleteLoading}
            class="w-full py-2.5 rounded-xl text-sm font-semibold hover:opacity-80 disabled:opacity-40"
            style="background:#ef4444;color:#fff">
            {deleteLoading ? '⏳' : '💣 Alles löschen (Reise + Tracker)'}
          </button>
        {:else}
          <button onclick={() => confirmDelete('trip_only')} disabled={deleteLoading}
            class="w-full py-2.5 rounded-xl text-sm font-semibold hover:opacity-80 disabled:opacity-40"
            style="background:#ef4444;color:#fff">
            {deleteLoading ? '⏳' : '🗑️ Reise unwiderruflich löschen'}
          </button>
        {/if}
        <button onclick={() => deleteModal = false} disabled={deleteLoading}
          class="w-full py-2 text-sm hover:opacity-70" style="color:var(--ws-muted)">Abbrechen</button>
      </div>
    </div>
  </div>
{/if}

<!-- ── Main Layout — Full Width ──────────────────────────────────────────── -->
<div class="w-full px-4 md:px-8 space-y-5 pb-10">

  <!-- Top bar: back + delete -->
  <div class="flex items-center justify-between">
    <button onclick={navigateBack}
      class="flex items-center gap-1.5 text-sm font-semibold hover:opacity-70 transition-opacity"
      style="color:var(--ws-muted)">
      {$t('tripHubBack')}
    </button>
    {#if trip}
      <button onclick={openDeleteModal}
        class="flex items-center gap-1 text-xs px-3 py-1.5 rounded-xl border hover:border-red-400 hover:text-red-400 transition-colors"
        style="border-color:var(--ws-border);color:var(--ws-muted)">🗑️</button>
    {/if}
  </div>

  {#if loading}
    <div class="rounded-2xl animate-pulse h-52" style="background:var(--ws-surface2)"></div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="rounded-2xl animate-pulse h-32" style="background:var(--ws-surface2)"></div>
      <div class="rounded-2xl animate-pulse h-32" style="background:var(--ws-surface2)"></div>
    </div>
  {:else if !trip}
    <div class="rounded-2xl p-10 text-center" style="background:var(--ws-surface2)">
      <p class="text-4xl mb-3">🗺️</p>
      <p class="font-semibold" style="color:var(--ws-text)">Kein Trip gefunden</p>
      <button onclick={() => currentPage.set('home')} class="mt-4 text-sm" style="color:var(--ws-accent)">Zurück</button>
    </div>
  {:else}

    <!-- ── Hero Card ───────────────────────────────────────────────────── -->
    <div class="relative rounded-2xl overflow-hidden" style="min-height:200px;background:{heroBg}">

      <!-- Unsplash background image -->
      {#if heroImgUrl && !heroImgError}
        <img src={heroImgUrl} alt=""
          class="absolute inset-0 w-full h-full object-cover"
          style="opacity:.35"
          onerror={() => { heroImgError = true; }} />
        <div class="absolute inset-0" style="background:rgba(0,0,0,.45)"></div>
      {/if}

      <div class="absolute inset-0 opacity-10"
        style="background-image:radial-gradient(circle at 20% 80%,rgba(255,255,255,.2) 0%,transparent 50%)"></div>
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
          <span class="text-2xl">{trip.travel_mode === 'car' ? '🚗' : '✈️'}</span>
        </div>
        <div>
          <div class="flex items-start gap-2">
            <h1 class="text-2xl font-bold leading-tight mb-1"
              style="font-family:var(--ws-serif);color:#fff;text-shadow:0 2px 12px rgba(0,0,0,.4)">
              {trip.title || trip.destination || $t('tripHubTitle')}
            </h1>
            <button
              onclick={() => editModal = true}
              title="Reise bearbeiten"
              class="mt-1 shrink-0 p-1 rounded-lg opacity-60 hover:opacity-100 transition-opacity"
              style="background:rgba(255,255,255,.15);backdrop-filter:blur(6px);border:none;color:#fff;line-height:1">
              ✏️
            </button>
          </div>
          <div class="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3">
            {#if trip.destination && trip.title && trip.title !== trip.destination}
              <!-- title gesetzt + verschieden von destination → beide anzeigen -->
              <span class="text-sm font-mono" style="color:rgba(255,255,255,.75)">📍 {trip.destination}</span>
            {:else if trip.destination && !trip.title}
              <!-- kein kosmetischer title → destination ist der Hauptname (schon im H1) -->
              <span class="text-sm font-mono" style="color:rgba(255,255,255,.75)">📍 {trip.destination}</span>
            {/if}
            {#if trip.start_date}
              <span class="text-xs sm:text-sm font-mono" style="color:rgba(255,255,255,.65);word-break:keep-all;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%">
                📅 {fmtDate(trip.start_date)}{trip.end_date && trip.end_date !== trip.start_date ? ' → ' + fmtDate(trip.end_date) : ''}
              </span>
            {/if}
          </div>
        </div>
      </div>

      <!-- Unsplash Attribution Overlay -->
      {#if heroImgUrl && !heroImgError && heroImgAuthor}
        <div class="absolute bottom-1 right-1 z-20 text-[9px] rounded px-1.5 py-0.5 leading-tight"
          style="background:rgba(0,0,0,.45);color:rgba(255,255,255,.65);backdrop-filter:blur(4px)">
          Foto von
          <a href="{heroImgAuthorUrl ? heroImgAuthorUrl + UTM : 'https://unsplash.com' + UTM}"
            target="_blank" rel="noopener noreferrer"
            class="underline hover:opacity-90" style="color:rgba(255,255,255,.75)">{heroImgAuthor}</a>
          auf
          <a href="{'https://unsplash.com' + UTM}" target="_blank" rel="noopener noreferrer"
            class="underline hover:opacity-90" style="color:rgba(255,255,255,.75)">Unsplash</a>
        </div>
      {/if}

    </div>

    <!-- ── Widget Grid ─────────────────────────────────────────────────── -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">

      <!-- Weather Widget: nur für active/planning — archived zeigt aktuelles Wetter, was nutzlos ist -->
      {#if phase !== 'archived' && (phase === 'active' || daysUntilStart <= 7)}
        <div class="md:col-span-2">
          <WeatherWidget destination={trip.destination || trip.title || ''} {phase} {daysUntilStart} />
        </div>
      {/if}

      <!-- Budget Widget -->
      <BudgetWidget
        {trip}
        {budgetBreakdown}
        bind:manualExpEditing
        bind:manualExpDraft
        {manualExpSaving}
        onsaveManualExp={saveManualExp}
        onreloadBudget={() => loadBudget(trip.id)}
      />

      <!-- Phase-specific placeholders -->
      {#if phase === 'active'}
        <div class="rounded-2xl border-2 border-dashed p-5 flex flex-col items-center gap-2 text-center"
          style="border-color:color-mix(in srgb,var(--ws-accent) 30%,var(--ws-border));background:color-mix(in srgb,var(--ws-accent) 4%,var(--ws-surface))">
          <span class="text-3xl">📓</span>
          <span class="text-xs font-semibold" style="color:var(--ws-text)">{$t('placeholderJournal') || 'Reisetagebuch'}</span>
          <span class="text-[10px] px-2 py-0.5 rounded-full font-bold" style="background:rgba(196,98,45,.12);color:var(--ws-accent)">Coming Soon</span>
        </div>
        <div class="rounded-2xl border-2 border-dashed p-5 flex flex-col items-center gap-2 text-center"
          style="border-color:color-mix(in srgb,var(--ws-accent) 30%,var(--ws-border));background:color-mix(in srgb,var(--ws-accent) 4%,var(--ws-surface))">
          <span class="text-3xl">🗺️</span>
          <span class="text-xs font-semibold" style="color:var(--ws-text)">{$t('placeholderDayTrips') || 'Tagesausflüge'}</span>
          <span class="text-[10px] px-2 py-0.5 rounded-full font-bold" style="background:rgba(196,98,45,.12);color:var(--ws-accent)">Coming Soon</span>
        </div>
      {/if}

      {#if phase === 'archived'}
        <div class="md:col-span-2">
          <ImmichGallery {trip} />
        </div>
      {/if}
    </div>

    <!-- Slot Widget (planning only) -->
    <SlotWidget
      {trip} {slots} {phase}
      onopenBook={openBookModal}
      onunbook={unbook}
      ongosearch={goSearch}
    />

    <!-- Checklist Widget (all phases) -->
    <ChecklistWidget
      {trip}
      bind:todos
      {phase}
      {regenLoading}
      onregenerate={regenerateTodos}
      ontoggle={toggleTodo}
      onadd={addTodo}
      ondelete={deleteTodo}
    />

  {/if}
</div>

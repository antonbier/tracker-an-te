<script>
  import { onMount } from 'svelte';
  import { t } from '$lib/i18n.js';
  import { currentPage, apiUrl, activeWsTripId } from '$lib/stores.js';
  import { api } from '$lib/api.js';

  let {
    nextTrip,
    lastTrip,
    heroDays,
    yearBudget,
    yearSpent,
    yearRemaining,
    yearSpentPct,
    budgetEditing,
    budgetInput    = $bindable(),
    budgetSaving,
    currentYear,
    onopenbodgetedit,
    onclosebodgetedit,
    onsavebudget,
    onopenWizzard,
  } = $props();


  // ── Next WS-Trip (WanderWizzard) ─────────────────────────────────────────
  let nextWsTrip = $state(null);
  let wsTripsLoaded = $state(false);

  async function loadWsTrips() {
    if (!$apiUrl) return;
    try {
      const trips = await api('/api/ws-trips');
      const planning = (trips || []).filter(t => t.status === 'planning' || t.status === 'booked');
      nextWsTrip = planning[0] || null;
    } catch { nextWsTrip = null; }
    wsTripsLoaded = true;
  }

  onMount(() => { loadWsTrips(); });
  // Re-fetch if apiUrl changes (e.g. after onboarding)
  $effect(() => { if ($apiUrl) loadWsTrips(); });

  function goToTripHub(tripId) {
    activeWsTripId.set(tripId);
    currentPage.set('triphub');
  }

  // ── Nostalgie background image ────────────────────────────────────────────
  let heroImageUrl = $state(null);

  $effect(() => {
    // Try to get image for last trip (Nostalgie) OR next trip
    const dest = hasLastTrip
      ? (lastTrip?.location_name || lastTrip?.name || lastTrip?.country || '')
      : hasNextTrip
        ? (nextTrip?.name || nextTrip?.location_name || '')
        : '';
    if (!dest || !$apiUrl) { heroImageUrl = null; return; }
    api(`/api/discovery/trip-image?destination=${encodeURIComponent(dest)}`)
      .then(res => { heroImageUrl = res?.image_url || null; })
      .catch(() => { heroImageUrl = null; });
  });

  // ── Hero content derived from trip state ──────────────────────────────────
  const hasNextTrip  = $derived(nextTrip !== null);
  const hasLastTrip  = $derived(!hasNextTrip && lastTrip !== null);
  const hasNoTrips   = $derived(!hasNextTrip && !hasLastTrip);

  const heroTitle = $derived.by(() => {
    if (hasNextTrip)  return nextTrip.name || 'Dein nächstes Abenteuer';
    if (hasLastTrip) {
      const name = lastTrip.location_name || lastTrip.name || 'dein letzter Trip';
      return name;
    }
    if (nextWsTrip)   return nextWsTrip.destination || nextWsTrip.title || $t('heroNextAdventure');
    return $t('heroWelcomeTitle') || 'Willkommen bei WanderSuite';
  });

  const heroSubtitle = $derived.by(() => {
    if (hasNextTrip && heroDays !== null) {
      if (heroDays === 0) return '🎒 Heute geht\'s los!';
      if (heroDays === 1) return '✈️ Morgen startet das Abenteuer!';
      return `✈️ Noch ${heroDays} Tage bis zum Abflug`;
    }
    if (hasLastTrip && heroDays !== null) {
      const days = Math.abs(heroDays);
      if (days === 0) return '📍 Gerade erst zurück';
      if (days < 7)   return `📍 Vor ${days} Tagen zurückgekehrt`;
      if (days < 30)  return `📍 Vor ${Math.floor(days/7)} Woche${Math.floor(days/7)>1?'n':''} zurückgekehrt`;
      const months = Math.floor(days/30);
      return `📍 Vor ${months} Monat${months>1?'en':''} zurückgekehrt`;
    }
    if (nextWsTrip && nextWsTrip.start_date) {
      const ms   = new Date(nextWsTrip.start_date + 'T00:00:00').getTime() - new Date().setHours(0,0,0,0);
      const days = Math.ceil(ms / 86400000);
      if (days <= 0)  return '🎒 ' + ($t('heroTodayStart') || "Heute geht's los!");
      if (days === 1) return '✈️ ' + ($t('heroTomorrow')   || 'Morgen startet das Abenteuer!');
      return '✈️ ' + ($t('heroInDays') || 'Noch {n} Tage').replace('{n}', days);
    }
    return '🌍 ' + ($t('heroNoTripsSubtitle') || 'Deine nächste Reise wartet auf dich');
  });

  // Gradient by trip state
  const heroBg = $derived.by(() => {
    if (hasNextTrip) return 'linear-gradient(135deg, #1a3a4a 0%, #c4622d 60%, #b84928 100%)';
    if (hasLastTrip) return 'linear-gradient(135deg, #2d1b0e 0%, #6b3a2a 50%, #2d6a4f 100%)';
    return 'linear-gradient(135deg, #1e293b 0%, #374151 50%, #1a3a4a 100%)';
  });

  // Budget bar color
  const budgetBarColor = $derived(
    yearSpentPct > 85 ? '#ef4444' :
    yearSpentPct > 60 ? 'var(--ws-accent2)' :
    'var(--ws-green)'
  );

  const budgetPct = $derived(Math.min(100, yearSpentPct));
</script>

<!-- ── Hero Container ── -->
<div class="relative rounded-2xl overflow-hidden" style="min-height:220px;background:{heroBg}">

  <!-- Nostalgie background image (lastTrip only) -->
  {#if heroImageUrl && (hasLastTrip || hasNextTrip)}
    <img
      src={heroImageUrl}
      alt=""
      class="absolute inset-0 w-full h-full object-cover"
      style="opacity:.35"
      onerror={(e) => { e.currentTarget.style.display='none'; }}
    />
    <!-- Extra dark overlay so text stays readable over image -->
    <div class="absolute inset-0" style="background:rgba(0,0,0,.45)"></div>
  {/if}

  <!-- Texture overlay for depth -->
  <div class="absolute inset-0 opacity-20"
    style="background-image:radial-gradient(circle at 20% 80%, rgba(255,255,255,.15) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(0,0,0,.3) 0%, transparent 50%)">
  </div>

  <!-- Main content -->
  <div class="relative z-10 p-6 flex flex-col justify-between h-full" style="min-height:220px">

    <!-- Top row: title + trip date -->
    <div>
      <!-- Countdown / nostalgia pill -->
      {#if hasNextTrip || hasLastTrip}
        <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold mb-3"
          style="background:rgba(255,255,255,.15);color:rgba(255,255,255,.9);backdrop-filter:blur(8px)">
          {#if hasNextTrip}
            <span class="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span>
          {/if}
          {heroSubtitle}
        </div>
      {/if}

      <!-- Trip name / hero title -->
      <h1 class="text-2xl font-bold leading-tight"
        style="font-family:var(--ws-serif);color:#fff;text-shadow:0 2px 12px rgba(0,0,0,.4)">
        {heroTitle}
      </h1>

      <!-- Trip metadata -->
      {#if hasNextTrip}
        <div class="flex items-center gap-3 mt-2 flex-wrap">
          {#if nextTrip.dateStart || nextTrip.date}
            <span class="text-sm font-mono" style="color:rgba(255,255,255,.75)">
              📅 {nextTrip.dateStart || nextTrip.date}
              {#if nextTrip.dateEnd && nextTrip.dateEnd !== (nextTrip.dateStart || nextTrip.date)}
                → {nextTrip.dateEnd}
              {/if}
            </span>
          {/if}
          {#if nextTrip.cost}
            <span class="text-sm font-mono font-bold" style="color:rgba(255,255,255,.9)">
              💶 {parseFloat(nextTrip.cost).toFixed(0)} €
            </span>
          {/if}
        </div>
      {:else if hasLastTrip}
        <div class="mt-2">
          <span class="text-sm" style="color:rgba(255,255,255,.65)">
            {#if lastTrip.start_date}
              {lastTrip.start_date}
              {#if lastTrip.end_date && lastTrip.end_date !== lastTrip.start_date}
                → {lastTrip.end_date}
              {/if}
              {#if lastTrip.nights}
                · {lastTrip.nights} Nächte
              {/if}
            {:else if lastTrip.dateStart}
              {lastTrip.dateStart}
            {/if}
          </span>
        </div>
      {:else}
        <p class="text-sm mt-2" style="color:rgba(255,255,255,.6)">
          {$t('heroNoTripsHint')}
        </p>
      {/if}
    </div>

    <!-- Bottom row: Budget overlay -->
    <div class="mt-6">
      {#if yearBudget > 0}
        <!-- Budget chip — click opens edit -->
        {#if !budgetEditing}
          <button onclick={onopenbodgetedit}
            class="flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all hover:opacity-90 active:scale-[.98]"
            style="background:rgba(0,0,0,.35);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.12)">

            <!-- Mini budget bar -->
            <div class="flex flex-col gap-1 flex-1 min-w-0">
              <div class="flex items-center justify-between gap-2">
                <span class="text-xs font-semibold" style="color:rgba(255,255,255,.8)">
                  {$t('dashBudget')} {currentYear}
                </span>
                <span class="text-xs font-mono font-bold" style="color:{yearSpentPct > 85 ? '#fca5a5' : 'rgba(255,255,255,.9)'}">
                  {yearRemaining.toFixed(0)} € {$t('heroBudgetFree')}
                </span>
              </div>
              <div class="h-1.5 rounded-full overflow-hidden" style="background:rgba(255,255,255,.15)">
                <div class="h-full rounded-full transition-all duration-700"
                  style="width:{budgetPct}%;background:{budgetBarColor}"></div>
              </div>
              <div class="text-[10px]" style="color:rgba(255,255,255,.5)">
                {yearSpent.toFixed(0)} € {$t('heroBudgetOf')} {yearBudget.toFixed(0)} € · ✏️ {$t('heroBudgetEdit')}
              </div>
            </div>
          </button>

        {:else}
          <!-- Inline Budget Edit -->
          <div class="flex gap-2 items-center px-4 py-2.5 rounded-xl"
            style="background:rgba(0,0,0,.45);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.2)">
            <span class="text-xs font-semibold shrink-0" style="color:rgba(255,255,255,.8)">
              {$t('dashBudget')} {currentYear}:
            </span>
            <input
              type="number"
              bind:value={budgetInput}
              placeholder="0"
              class="flex-1 min-w-0 px-2 py-1 rounded-lg text-sm font-mono text-center outline-none border-0"
              style="background:rgba(255,255,255,.1);color:#fff"
              onkeydown={(e) => {
                if (e.key === 'Enter') onsavebudget();
                if (e.key === 'Escape') onclosebodgetedit();
              }}
            />
            <span class="text-sm" style="color:rgba(255,255,255,.6)">€</span>
            <button onclick={onsavebudget} disabled={budgetSaving}
              class="px-3 py-1 rounded-lg text-xs font-bold shrink-0 disabled:opacity-50"
              style="background:var(--ws-accent);color:#fff5ec">
              {budgetSaving ? '⏳' : '✓'}
            </button>
            <button onclick={onclosebodgetedit}
              class="px-2 py-1 rounded-lg text-xs shrink-0"
              style="color:rgba(255,255,255,.5)">✕</button>
          </div>
        {/if}

      {:else}
        <!-- No budget set yet -->
        {#if !budgetEditing}
          <button onclick={onopenbodgetedit}
            class="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium transition-all hover:opacity-90"
            style="background:rgba(0,0,0,.3);backdrop-filter:blur(8px);border:1px solid rgba(255,255,255,.1);color:rgba(255,255,255,.6)">
            💶 {$t('heroSetBudget')} {currentYear}
          </button>
        {:else}
          <div class="flex gap-2 items-center px-4 py-2.5 rounded-xl"
            style="background:rgba(0,0,0,.45);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.2)">
            <span class="text-xs font-semibold shrink-0" style="color:rgba(255,255,255,.8)">
              {$t('dashBudget')} {currentYear}:
            </span>
            <input
              type="number"
              bind:value={budgetInput}
              placeholder="z.B. 4000"
              class="flex-1 min-w-0 px-2 py-1 rounded-lg text-sm font-mono text-center outline-none border-0"
              style="background:rgba(255,255,255,.1);color:#fff"
              onkeydown={(e) => {
                if (e.key === 'Enter') onsavebudget();
                if (e.key === 'Escape') onclosebodgetedit();
              }}
            />
            <span class="text-sm" style="color:rgba(255,255,255,.6)">€</span>
            <button onclick={onsavebudget} disabled={budgetSaving}
              class="px-3 py-1 rounded-lg text-xs font-bold shrink-0 disabled:opacity-50"
              style="background:var(--ws-accent);color:#fff5ec">
              {budgetSaving ? '⏳' : '✓'}
            </button>
            <button onclick={onclosebodgetedit}
              class="px-2 py-1 rounded-lg text-xs shrink-0"
              style="color:rgba(255,255,255,.5)">✕</button>
          </div>
        {/if}
      {/if}
    </div>

  </div>

  <!-- ── Action Button: only TripHub link (no Details/Trip planen) ── -->
  <div class="absolute top-4 right-4 flex gap-2 z-20">
    {#if wsTripsLoaded && nextWsTrip}
      <button onclick={() => goToTripHub(nextWsTrip.id)}
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all hover:opacity-90 active:scale-[.97]"
        style="background:rgba(0,0,0,.35);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.25);color:rgba(255,255,255,.9)">
        🗺️ {$t('dashTripHub')}
      </button>
    {/if}
  </div>

</div>

<script>
  import { onMount } from 'svelte';
  import { t } from '$lib/i18n.js';
  import { currentPage, apiUrl, activeWsTripId } from '$lib/stores.js';
  import { api } from '$lib/api.js';
  import HeroPastTrip from './HeroPastTrip.svelte';
  import HeroNextTrip from './HeroNextTrip.svelte';

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
    refreshKey = 0,
  } = $props();


  // ── Next WS-Trip (WanderWizzard) ─────────────────────────────────────────
  let nextWsTrip = $state(null);
  let wsTripsLoaded = $state(false);

  let archivedWsTrips = $state([]);

  async function loadWsTrips() {
    if (!$apiUrl) return;
    try {
      const trips = await api('/api/ws-trips');
      const today = new Date().toISOString().slice(0, 10);
      const planning = (trips || []).filter(t => t.status === 'planning' || t.status === 'booked');
      nextWsTrip    = planning[0] || null;
      // Archiv: WS-Trips die bereits stattgefunden haben
      // → end_date < heute ODER (kein end_date, aber start_date < heute)
      archivedWsTrips = (trips || []).filter(t => {
        const e = (t.end_date || '').slice(0, 10);
        const s = (t.start_date || '').slice(0, 10);
        if (e) return e < today;          // end_date gesetzt → danach archiviert
        return s && s < today;            // kein end_date → nach start_date archiviert
      });
    } catch { nextWsTrip = null; archivedWsTrips = []; }
    wsTripsLoaded = true;
  }

  onMount(() => { loadWsTrips(); });
  // Re-fetch if apiUrl changes (e.g. after onboarding)
  $effect(() => { if ($apiUrl) loadWsTrips(); });
  $effect(() => { refreshKey; loadWsTrips(); }); // reload when WW closes

  function goToTripHub(tripId) {
    activeWsTripId.set(tripId);
    currentPage.set('triphub');
  }


  // ── Hero content derived from trip state ──────────────────────────────────
  const hasNextTrip  = $derived(nextTrip !== null);
  const hasLastTrip  = $derived(!hasNextTrip && (lastTrip !== null || archivedWsTrips.length > 0));
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

  // Fallback background for no-trips state
  const heroBg = 'background:linear-gradient(135deg, #1e293b 0%, #374151 50%, #1a3a4a 100%)';

  // Budget bar color
  const budgetBarColor = $derived(
    yearSpentPct > 85 ? '#ef4444' :
    yearSpentPct > 60 ? 'var(--ws-accent2)' :
    'var(--ws-green)'
  );

  const budgetPct = $derived(Math.min(100, yearSpentPct));
</script>

<!-- ── Hero: 2-Kachel-Layout wenn beide Trips vorhanden ── -->
{#if (hasNextTrip || nextWsTrip) && hasLastTrip}
  <!-- BEIDE: Nebeneinander -->
  <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
    <HeroPastTrip
      archivedTrips={archivedWsTrips.length > 0 ? archivedWsTrips : (lastTrip ? [lastTrip] : [])}
      ongoToHub={(t) => {
        const id = t?.id;
        if (id) { activeWsTripId.set(id); currentPage.set('triphub'); }
      }}
    />
    <HeroNextTrip
      trip={nextWsTrip || nextTrip}
      ongoToHub={() => {
        const tr = nextWsTrip || nextTrip;
        if (tr?.id) { activeWsTripId.set(tr.id); currentPage.set('triphub'); }
      }}
    />
  </div>

{:else if hasNextTrip || nextWsTrip}
  <!-- NUR nächster Trip -->
  <HeroNextTrip
    trip={nextWsTrip || nextTrip}
    ongoToHub={() => {
      const tr = nextWsTrip || nextTrip;
      if (tr?.id) { activeWsTripId.set(tr.id); currentPage.set('triphub'); }
    }}
  />

{:else if hasLastTrip}
  <!-- NUR letzter Trip (Nostalgie) -->
  <HeroPastTrip
    archivedTrips={archivedWsTrips.length > 0 ? archivedWsTrips : (lastTrip ? [lastTrip] : [])}
    ongoToHub={(t) => {
      const id = t?.id;
      if (id) { activeWsTripId.set(id); currentPage.set('triphub'); }
    }}
  />

{:else}
  <!-- Kein Trip: Willkommen-Banner -->
  <div class="relative rounded-2xl overflow-hidden" style="min-height:180px;{heroBg}">
    <div class="absolute inset-0 opacity-20 pointer-events-none"
      style="background-image:radial-gradient(circle at 20% 80%, rgba(255,255,255,.15) 0%, transparent 50%)"></div>
    <div class="relative z-10 p-6 flex flex-col justify-between h-full" style="min-height:180px">
      <div>
        <h1 class="text-2xl font-bold leading-tight"
          style="font-family:var(--ws-serif);color:#fff;text-shadow:0 2px 12px rgba(0,0,0,.4)">
          {$t('heroWelcomeTitle') || 'Willkommen bei WanderSuite'}
        </h1>
        <p class="text-sm mt-2" style="color:rgba(255,255,255,.65)">{$t('heroNoTripsHint')}</p>
      </div>
      <div class="mt-4">
        <button onclick={onopenWizzard}
          class="px-4 py-2 rounded-xl text-sm font-semibold transition-all hover:opacity-90"
          style="background:var(--ws-accent);color:#fff5ec">
          🪄 {$t('dashTripHubNew') || 'Reise planen'}
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- ── Budget-Widget (immer unterhalb der Kacheln) ── -->
<div class="rounded-2xl px-5 py-4" style="background:linear-gradient(135deg,#1e293b 0%,#374151 100%)">
  {#if yearBudget > 0}
    {#if !budgetEditing}
      <!-- z-index fix: relative z-10 auf den interaktiven Elementen -->
      <button onclick={onopenbodgetedit}
        class="relative z-10 w-full flex items-center gap-3 transition-all hover:opacity-90 active:scale-[.99]">
        <div class="flex flex-col gap-1 flex-1 min-w-0">
          <div class="flex items-center justify-between gap-2">
            <span class="text-xs font-semibold" style="color:rgba(255,255,255,.8)">
              {$t('dashBudget')} {currentYear}
            </span>
            <span class="text-xs font-mono font-bold"
              style="color:{yearSpentPct > 85 ? '#fca5a5' : 'rgba(255,255,255,.9)'}">
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
      <div class="relative z-10 flex gap-2 items-center">
        <span class="text-xs font-semibold shrink-0" style="color:rgba(255,255,255,.8)">{$t('dashBudget')} {currentYear}:</span>
        <input type="number" bind:value={budgetInput} placeholder="0"
          class="flex-1 min-w-0 px-2 py-1 rounded-lg text-sm font-mono text-center outline-none border-0"
          style="background:rgba(255,255,255,.1);color:#fff"
          onkeydown={(e) => { if (e.key==='Enter') onsavebudget(); if (e.key==='Escape') onclosebodgetedit(); }} />
        <span class="text-sm" style="color:rgba(255,255,255,.6)">€</span>
        <button onclick={onsavebudget} disabled={budgetSaving}
          class="px-3 py-1 rounded-lg text-xs font-bold shrink-0 disabled:opacity-50"
          style="background:var(--ws-accent);color:#fff5ec">{budgetSaving ? '⏳' : '✓'}</button>
        <button onclick={onclosebodgetedit} class="px-2 py-1 rounded-lg text-xs shrink-0"
          style="color:rgba(255,255,255,.5)">✕</button>
      </div>
    {/if}
  {:else}
    {#if !budgetEditing}
      <button onclick={onopenbodgetedit}
        class="relative z-10 inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium transition-all hover:opacity-90"
        style="background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.1);color:rgba(255,255,255,.6)">
        💶 {$t('heroSetBudget')} {currentYear}
      </button>
    {:else}
      <div class="relative z-10 flex gap-2 items-center">
        <span class="text-xs font-semibold shrink-0" style="color:rgba(255,255,255,.8)">{$t('dashBudget')} {currentYear}:</span>
        <input type="number" bind:value={budgetInput} placeholder="0"
          class="flex-1 min-w-0 px-2 py-1 rounded-lg text-sm font-mono text-center outline-none border-0"
          style="background:rgba(255,255,255,.1);color:#fff"
          onkeydown={(e) => { if (e.key==='Enter') onsavebudget(); if (e.key==='Escape') onclosebodgetedit(); }} />
        <span class="text-sm" style="color:rgba(255,255,255,.6)">€</span>
        <button onclick={onsavebudget} disabled={budgetSaving}
          class="px-3 py-1 rounded-lg text-xs font-bold shrink-0 disabled:opacity-50"
          style="background:var(--ws-accent);color:#fff5ec">{budgetSaving ? '⏳' : '✓'}</button>
        <button onclick={onclosebodgetedit} class="px-2 py-1 rounded-lg text-xs shrink-0"
          style="color:rgba(255,255,255,.5)">✕</button>
      </div>
    {/if}
  {/if}
</div>

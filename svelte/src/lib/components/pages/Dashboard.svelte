<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';
  import { apiUrl, trips, budget, appVersion, currentPage } from '$lib/stores.js';
  import { toast } from '$lib/toast.js';
  import { t } from '$lib/i18n.js';

  import WanderWizzard      from '$lib/components/WanderWizzard.svelte';
  import HeroSection        from '$lib/components/dashboard/HeroSection.svelte';
  import TravelInspo        from '$lib/components/dashboard/TravelInspo.svelte';
  import CompactTripsList   from '$lib/components/dashboard/CompactTripsList.svelte';
  import CompactTrackerGrid from '$lib/components/dashboard/CompactTrackerGrid.svelte';

  // ── Loading / raw data ────────────────────────────────────────────────────
  let loading       = $state(true);
  let dawarichTrips = $state([]);
  let allTrackers   = $state([]);

  // ── Budget ────────────────────────────────────────────────────────────────
  const currentYear = new Date().getFullYear();
  let budgetByYear  = $state({});
  let budgetInput   = $state('');
  let budgetSaving  = $state(false);
  let budgetEditing  = $state(false);
  let wizzardOpen    = $state(false);

  const yearBudget    = $derived(parseFloat(budgetByYear[String(currentYear)]) || 0);
  const CIRC          = 2 * Math.PI * 38;

  const yearSpent = $derived.by(() => {
    const yr = String(currentYear);
    return $trips
      .filter(t => (t.dateStart || t.date || '').slice(0, 4) === yr)
      .reduce((s, t) => s + (parseFloat(t.cost) || 0), 0);
  });

  const yearRemaining  = $derived(Math.max(0, yearBudget - yearSpent));
  const yearSpentPct   = $derived(yearBudget > 0 ? Math.min(100, (yearSpent / yearBudget) * 100) : 0);
  const yearDonutFill  = $derived((yearSpentPct / 100) * CIRC);
  const yearDonutColor = $derived(
    yearSpentPct > 85 ? 'var(--ws-red,#dc2626)' :
    yearSpentPct > 60 ? 'var(--ws-accent2)' :
    'var(--ws-accent)'
  );

  async function loadBudget() {
    if (!$apiUrl) return;
    try { budgetByYear = (await api('/api/trips/budget')) || {}; } catch {}
    budgetInput = budgetByYear[String(currentYear)] != null
      ? String(budgetByYear[String(currentYear)]) : '';
  }

  async function saveBudget() {
    if (!$apiUrl) { toast('Backend-URL fehlt', 'warning'); return; }
    const amount = parseFloat(budgetInput);
    if (isNaN(amount) || amount < 0) { toast('Ungültiger Betrag', 'error'); return; }
    budgetSaving = true;
    try {
      await api('/api/trips/budget', { method: 'PUT', body: JSON.stringify({ year: currentYear, amount }) });
      budgetByYear = { ...budgetByYear, [String(currentYear)]: amount };
      budgetEditing = false;
      toast(`Budget ${currentYear}: ${amount.toFixed(0)} € gespeichert ✓`, 'success');
    } catch (e) { toast(e.message, 'error'); }
    budgetSaving = false;
  }

  // ── Tracker loading (alle 4 Typen) ───────────────────────────────────────
  async function loadAllTrackers() {
    if (!$apiUrl) return;
    try {
      const [ry, gf, hm, bk] = await Promise.allSettled([
        api('/api/trackers'),
        api('/api/google-flights'),
        api('/api/accommodations/homair'),
        api('/api/accommodations/booking'),
      ]);
      allTrackers = [
        ...(ry.status === 'fulfilled' ? (ry.value || []).map(t => ({ ...t, _type: 'flight' }))        : []),
        ...(gf.status === 'fulfilled' ? (gf.value || []).map(t => ({ ...t, _type: 'google_flight' })) : []),
        ...(hm.status === 'fulfilled' ? (hm.value || []).map(t => ({ ...t, _type: 'camping' }))       : []),
        ...(bk.status === 'fulfilled' ? (bk.value || []).map(t => ({ ...t, _type: 'hotel' }))         : []),
      ];
    } catch {}
  }

  // ── Derived trip lists ────────────────────────────────────────────────────
  const today     = new Date().toISOString().slice(0, 10);
  const upcoming  = $derived(
    [...$trips]
      .filter(t => (t.dateStart || t.date || '') >= today)
      .sort((a, b) => (a.dateStart || a.date || '').localeCompare(b.dateStart || b.date || ''))
  );
  const completed = $derived(
    [...$trips]
      .filter(t => (t.dateStart || t.date || '') < today)
      .sort((a, b) => (b.dateStart || b.date || '').localeCompare(a.dateStart || a.date || ''))
  );
  const recentDawarich = $derived(
    [...dawarichTrips]
      .sort((a, b) => b.start_date.localeCompare(a.start_date))
      .slice(0, 5)
  );

  // ── Hero data: next trip or last trip for nostalgia ───────────────────────
  const nextTrip = $derived(upcoming[0] ?? null);
  const lastTrip = $derived.by(() => {
    if (recentDawarich.length > 0) return recentDawarich[0];
    if (completed.length > 0) return completed[0];
    return null;
  });

  // Days until next trip (positive) or since last trip (negative/nostalgia)
  const heroDays = $derived.by(() => {
    if (nextTrip) {
      const ms = new Date(nextTrip.dateStart || nextTrip.date) - new Date(today);
      return Math.ceil(ms / 86400000);
    }
    if (lastTrip) {
      const dateStr = lastTrip.start_date || lastTrip.dateStart || lastTrip.date || '';
      if (!dateStr) return null;
      const ms = new Date(today) - new Date(dateStr);
      return -Math.floor(ms / 86400000); // negative = past
    }
    return null;
  });

  // ── Mount ─────────────────────────────────────────────────────────────────
  onMount(async () => {
    if (!$apiUrl) { loading = false; return; }
    try {
      await Promise.all([
        api('/api/dawarich/trips?limit=20')
          .then(r => { dawarichTrips = r || []; })
          .catch(() => {}),
        loadAllTrackers(),
        loadBudget(),
      ]);
    } catch {}
    loading = false;
  });

  $effect(() => { if ($apiUrl) loadBudget(); });
</script>

<div class="space-y-5">

  <!-- ── Hero ── -->
  <HeroSection
    {nextTrip}
    {lastTrip}
    {heroDays}
    {yearBudget}
    {yearSpent}
    {yearRemaining}
    {yearSpentPct}
    {budgetEditing}
    bind:budgetInput
    {budgetSaving}
    {currentYear}
    onopenbodgetedit={() => { budgetEditing = true; }}
    onclosebodgetedit={() => { budgetEditing = false; }}
    onsavebudget={saveBudget}
    onopenWizzard={() => wizzardOpen = true}
  />

  <!-- ── Travel Inspiration ── -->
  <TravelInspo
    {recentDawarich}
    onstartwizard={(data) => currentPage.set('discover')}
    onnavto={(page) => currentPage.set(page)}
  />

  <!-- ── Bottom split: trips + trackers ── -->
  <div class="grid md:grid-cols-2 gap-4">

    <CompactTripsList
      {upcoming}
      {completed}
      {recentDawarich}
      {yearBudget}
      {yearSpent}
      {yearRemaining}
      {yearSpentPct}
      {yearDonutFill}
      {yearDonutColor}
      {CIRC}
      {loading}
      onnavto={(page) => currentPage.set(page)}
    />

    <CompactTrackerGrid
      {allTrackers}
      {loading}
      onnavto={(page) => currentPage.set(page)}
    />

  </div>

  {#if $appVersion}
    <div class="text-center pt-2">
      <span class="text-xs font-mono" style="color:var(--ws-border)">{$appVersion}</span>
    </div>
  {/if}


<WanderWizzard bind:open={wizzardOpen} />

</div>
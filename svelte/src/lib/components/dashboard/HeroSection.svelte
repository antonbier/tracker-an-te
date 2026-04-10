<script>
  import { t } from '$lib/i18n.js';

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
  } = $props();

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
    return 'Willkommen bei WanderSuite';
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
    return '🌍 Deine nächste Reise wartet auf dich';
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
          Plane deinen ersten Trip in Meine Reisen.
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
                  Budget {currentYear}
                </span>
                <span class="text-xs font-mono font-bold" style="color:{yearSpentPct > 85 ? '#fca5a5' : 'rgba(255,255,255,.9)'}">
                  {yearRemaining.toFixed(0)} € frei
                </span>
              </div>
              <div class="h-1.5 rounded-full overflow-hidden" style="background:rgba(255,255,255,.15)">
                <div class="h-full rounded-full transition-all duration-700"
                  style="width:{budgetPct}%;background:{budgetBarColor}"></div>
              </div>
              <div class="text-[10px]" style="color:rgba(255,255,255,.5)">
                {yearSpent.toFixed(0)} € von {yearBudget.toFixed(0)} € · ✏️ tippen zum Bearbeiten
              </div>
            </div>
          </button>

        {:else}
          <!-- Inline Budget Edit -->
          <div class="flex gap-2 items-center px-4 py-2.5 rounded-xl"
            style="background:rgba(0,0,0,.45);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.2)">
            <span class="text-xs font-semibold shrink-0" style="color:rgba(255,255,255,.8)">
              Budget {currentYear}:
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
            💶 Jahresbudget für {currentYear} festlegen
          </button>
        {:else}
          <div class="flex gap-2 items-center px-4 py-2.5 rounded-xl"
            style="background:rgba(0,0,0,.45);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.2)">
            <span class="text-xs font-semibold shrink-0" style="color:rgba(255,255,255,.8)">
              Budget {currentYear}:
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
</div>

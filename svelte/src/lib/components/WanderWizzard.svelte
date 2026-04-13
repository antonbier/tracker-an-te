<script>
  import { t } from '$lib/i18n.js';
  import { AIRPORTS } from '$lib/components/priceradar/constants.js';
  import { currentPage, activeWsTripId } from '$lib/stores.js';
  import { api } from '$lib/api.js';
  import { toast } from '$lib/toast.js';

  // ── Props ──────────────────────────────────────────────────────────────────
  let {
    open        = $bindable(false),
    destination = '',
    dateFrom    = '',
    dateTo      = '',
    adults      = 2,
    children    = 0,
    homeAirport = '',
    budget      = 0,
  } = $props();

  // ── Core State ─────────────────────────────────────────────────────────────
  let step       = $state(1);
  let path       = $state('known');
  let travelMode = $state('flight');
  let creating   = $state(false);

  // Weg A
  let s1Dest          = $state(destination);
  let s1DestInput     = $state(destination || '');
  let s1AcSuggestions = $state([]);
  let s1DateFrom      = $state(dateFrom);
  let s1DateTo        = $state(dateTo);
  let s1Adults        = $state(adults);
  let s1Children      = $state(children);
  let s1Home          = $state(homeAirport);
  let s1HomeInput     = $state(homeAirport || '');
  let s1HomeAcSugg    = $state([]);

  // Weg B
  let s1DateMode   = $state('exact');
  let s1FlexMonth  = $state('');
  let s1FlexNights = $state(7);
  let s1MaxTime    = $state('any');
  let s1Vibes      = $state([]);
  let s1Wish       = $state('');

  // Budget (global)
  let s1Budget = $state(budget || 0);

  // ── Sync on open ───────────────────────────────────────────────────────────
  $effect(() => {
    if (open) {
      s1Dest = destination || ''; s1DestInput = destination || '';
      s1DateFrom = dateFrom || ''; s1DateTo = dateTo || '';
      s1Adults = adults || 2; s1Children = children || 0;
      s1Home = homeAirport || ''; s1HomeInput = homeAirport || '';
      s1Budget = budget || 0;
      step = 1; path = 'known'; travelMode = 'flight'; creating = false;
    }
  });

  // ── Styling ────────────────────────────────────────────────────────────────
  const inp  = 'w-full px-3 py-2 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ws-accent)]';
  const inpS = 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)';
  const lbl  = 'block text-xs font-bold uppercase tracking-wider mb-1.5';

  // ── Airport autocomplete ───────────────────────────────────────────────────
  function filterAP(q) {
    if (!q) return [];
    const ql = q.toLowerCase();
    return AIRPORTS.filter(a => a.iata.toLowerCase().startsWith(ql) || a.city.toLowerCase().includes(ql)).slice(0, 6);
  }
  function onDestInput(e) { s1DestInput = e.target.value; s1Dest = e.target.value; s1AcSuggestions = filterAP(e.target.value); }
  function pickDest(a)    { s1Dest = a.iata; s1DestInput = `${a.iata} – ${a.city}`; s1AcSuggestions = []; }
  function onHomeInput(e) { s1HomeInput = e.target.value; s1Home = e.target.value.slice(0,3).toUpperCase(); s1HomeAcSugg = filterAP(e.target.value); }
  function pickHome(a)    { s1Home = a.iata; s1HomeInput = `${a.iata} – ${a.city}`; s1HomeAcSugg = []; }

  // ── Vibes ──────────────────────────────────────────────────────────────────
  const VIBES = [
    ['sea','wwVibeSea'],['mountain','wwVibeMountain'],['culture','wwVibeCulture'],
    ['relax','wwVibeRelax'],['adventure','wwVibeAdventure'],['city','wwVibeCity'],
    ['food','wwVibeFood'],['nature','wwVibeNature'],
  ];
  function toggleVibe(v) {
    s1Vibes = s1Vibes.includes(v) ? s1Vibes.filter(x => x !== v) : [...s1Vibes, v];
  }

  // ── Navigation ─────────────────────────────────────────────────────────────
  const step1Valid = $derived.by(() => path === 'known' ? !!(s1Dest && s1DateFrom) : true);
  function close() { open = false; }

  const STEPS = $derived([$t('wwStepDetails'), $t('wwStepSummary')]);

  // ── Summary derived ────────────────────────────────────────────────────────
  const vibesSummary = $derived.by(() => {
    if (!s1Vibes.length) return '—';
    return s1Vibes.map(v => { const e = VIBES.find(([k]) => k === v); return e ? $t(e[1]) : v; }).join(', ');
  });
  const flexMonthOptions = $derived($t('wwFlexMonthOptions').split(','));
  const dateSummary = $derived.by(() => {
    if (path === 'inspire' && s1DateMode === 'flexible') return `${s1FlexMonth || '—'} · ${s1FlexNights} ${$t('wwFlexNights')}`;
    return s1DateFrom ? `${s1DateFrom}${s1DateTo ? ' → ' + s1DateTo : ''}` : '—';
  });
  const travelersSummary = $derived(
    `${s1Adults} ${$t('wwAdultsShort')}${s1Children > 0 ? ' · ' + s1Children + ' ' + $t('wwChildrenShort') : ''}`
  );
  const budgetHint = $derived.by(() => {
    if (!s1Budget) return '';
    const n = s1Adults + s1Children;
    const avg = Math.round(s1Budget / n);
    return $t('wwBudgetHint').replace('{budget}', s1Budget).replace('{n}', n).replace('{s}', n !== 1 ? 'en' : '').replace('{avg}', avg);
  });
  const maxTimeLabel = $derived(travelMode === 'car' ? $t('wwMaxTravelTimeCar') : $t('wwMaxTravelTime'));

  const summaryRows = $derived.by(() => {
    const rows = [];
    rows.push([travelMode === 'flight' ? '✈️' : '🚗',
      travelMode === 'flight' ? $t('wwModeFlugTitle') : $t('wwModeAutoTitle'),
      path === 'known' ? $t('wwPathKnownTitle') : $t('wwPathInspireTitle'), 'mode']);
    if (path === 'known') {
      rows.push(['📍', $t('wwSummaryDest'), s1Dest || '—', 'dest']);
    } else {
      rows.push(['✨', $t('wwPathInspireTitle'), vibesSummary || '—', 'inspire']);
      if (s1Wish) rows.push(['💬', $t('wwSummaryWish'), s1Wish, 'wish']);
    }
    rows.push(['📅', $t('wwSummaryDates'), dateSummary, 'dates']);
    if (path === 'inspire' && s1DateMode === 'flexible') {
      rows.push(['⏱️', maxTimeLabel, s1MaxTime === 'any' ? $t('wwMaxTimeAny') : s1MaxTime, 'maxtime']);
    }
    rows.push(['👥', $t('wwSummaryTravelers'), travelersSummary, 'travelers']);
    if (travelMode === 'flight') rows.push(['🛫', $t('wwSummaryHome'), s1Home || '—', 'home']);
    rows.push(['💶', $t('wwSummaryBudget'), s1Budget > 0 ? s1Budget + ' €' : $t('wwNoLimit'), 'budget']);
    return rows;
  });

  // ── Card styles ────────────────────────────────────────────────────────────
  const cardBase = 'relative flex-1 rounded-2xl border p-4 cursor-pointer transition-all duration-200 select-none';

  function cardStyle(active) {
    return active
      ? 'border-color:var(--ws-accent);background:color-mix(in srgb,var(--ws-accent) 8%,var(--ws-surface));box-shadow:0 0 0 2px color-mix(in srgb,var(--ws-accent) 30%,transparent)'
      : 'border-color:var(--ws-border);background:var(--ws-surface2);opacity:0.4;filter:grayscale(1)';
  }

  // ── Create Trip → API → redirect to Trip Hub ───────────────────────────────
  async function createTrip() {
    if (creating) return;
    creating = true;
    try {
      const payload = {
        title:       path === 'known' ? (s1Dest || 'Neue Reise') : ($t('wwPathInspireTitle')),
        destination: path === 'known' ? s1Dest : '',
        start_date:  s1DateMode === 'exact' ? s1DateFrom : null,
        end_date:    s1DateMode === 'exact' ? s1DateTo   : null,
        trip_type:   travelMode === 'flight' ? 'flight' : 'car',
        budget:      s1Budget || null,
        path,
        travel_mode: travelMode,
        vibes:       s1Vibes,
        wish_text:   s1Wish || null,
        flex_month:  s1FlexMonth || null,
        flex_nights: s1DateMode === 'flexible' ? s1FlexNights : null,
        max_time:    s1MaxTime !== 'any' ? s1MaxTime : null,
        home_airport: travelMode === 'flight' ? s1Home : null,
        adults:      s1Adults,
        children:    s1Children,
      };
      const res = await api('/api/ws-trips', { method: 'POST', body: JSON.stringify(payload) });
      toast($t('wizzardSuccess'), 'success');
      open = false;
      activeWsTripId.set(res.id);
      currentPage.set('triphub');
    } catch (e) {
      toast(e.message || 'Fehler beim Anlegen', 'error');
      creating = false;
    }
  }
</script>

{#if open}
<div
  class="fixed inset-0 z-50 flex items-center justify-center"
  style="background:rgba(0,0,0,.48);backdrop-filter:blur(6px)"
  role="dialog" aria-modal="true">

  <div class="fixed inset-0 md:inset-[4vh_8vw] flex flex-col rounded-none md:rounded-2xl overflow-hidden shadow-2xl"
    style="background:var(--ws-surface);border:1px solid var(--ws-border)">

    <!-- Header -->
    <div class="flex items-center gap-3 px-5 py-4 border-b shrink-0" style="border-color:var(--ws-border)">
      <span class="text-xl">🧙</span>
      <div class="flex-1">
        <h2 class="font-bold text-base" style="color:var(--ws-text)">{$t('wwTitle')}</h2>
        <p class="text-xs" style="color:var(--ws-muted)">{$t('wwSubtitle')}</p>
      </div>
      <button onclick={close}
        class="w-8 h-8 rounded-xl flex items-center justify-center text-lg hover:opacity-60 transition-opacity"
        style="color:var(--ws-muted)">✕</button>
    </div>

    <!-- Step Indicator — centered -->
    <div class="px-5 pt-4 pb-3 shrink-0">
      <div class="flex items-center justify-center gap-6">
        {#each STEPS as label, i}
          {@const idx = i + 1}
          {@const done = step > idx}
          {@const active = step === idx}
          <div class="flex items-center gap-2">
            <!-- connector before step 2 -->
            {#if i > 0}
              <div class="w-12 h-px rounded" style="background:{done ? 'var(--ws-green)' : 'var(--ws-border)'}"></div>
            {/if}
            <div class="flex flex-col items-center gap-1">
              <div class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all"
                style={done   ? 'background:var(--ws-green);color:#fff'
                      : active ? 'background:var(--ws-accent);color:#fff5ec'
                      : 'background:var(--ws-surface2);border:1px solid var(--ws-border);color:var(--ws-muted)'}>
                {done ? '✓' : idx}
              </div>
              <span class="text-[10px] font-semibold whitespace-nowrap hidden sm:block"
                style="color:{active ? 'var(--ws-accent)' : done ? 'var(--ws-green)' : 'var(--ws-muted)'}">{label}</span>
            </div>
          </div>
        {/each}
      </div>
    </div>

    <!-- Body -->
    <div class="flex-1 overflow-y-auto px-5 pb-4 space-y-5">

      <!-- ══ STEP 1 ══════════════════════════════════════════════════════════ -->
      {#if step === 1}

        <!-- PATH CARDS -->
        <div>
          <p class="text-[11px] font-semibold uppercase tracking-wider mb-2" style="color:var(--ws-muted)">{$t('wwStepDetails')}</p>
          <div class="flex gap-3">
            <button class={cardBase} style={cardStyle(path === 'known')} onclick={() => path = 'known'} type="button">
              {#if path === 'known'}
                <span class="absolute top-2.5 right-2.5 w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold"
                  style="background:var(--ws-accent);color:#fff">✓</span>
              {/if}
              <div class="text-2xl mb-1.5">📍</div>
              <div class="text-sm font-semibold mb-0.5" style="color:var(--ws-text)">{$t('wwPathKnownTitle')}</div>
              <div class="text-xs leading-snug" style="color:var(--ws-muted)">{$t('wwPathKnownDesc')}</div>
            </button>
            <button class={cardBase} style={cardStyle(path === 'inspire')} onclick={() => path = 'inspire'} type="button">
              {#if path === 'inspire'}
                <span class="absolute top-2.5 right-2.5 w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold"
                  style="background:var(--ws-accent);color:#fff">✓</span>
              {/if}
              <div class="text-2xl mb-1.5">✨</div>
              <div class="text-sm font-semibold mb-0.5" style="color:var(--ws-text)">{$t('wwPathInspireTitle')}</div>
              <div class="text-xs leading-snug" style="color:var(--ws-muted)">{$t('wwPathInspireDesc')}</div>
            </button>
          </div>
        </div>

        <!-- TRAVEL MODE CARDS -->
        <div class="flex gap-3">
          {#each [['flight','✈️','wwModeFlugTitle','wwModeFlugDesc'],['car','🚗','wwModeAutoTitle','wwModeAutoDesc']] as [m,icon,tk,dk]}
            <button class={cardBase} style={cardStyle(travelMode === m)} onclick={() => travelMode = m} type="button">
              {#if travelMode === m}
                <span class="absolute top-2.5 right-2.5 w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold"
                  style="background:var(--ws-accent);color:#fff">✓</span>
              {/if}
              <div class="text-2xl mb-1.5">{icon}</div>
              <div class="text-sm font-semibold mb-0.5" style="color:var(--ws-text)">{$t(tk)}</div>
              <div class="text-xs" style="color:var(--ws-muted)">{$t(dk)}</div>
            </button>
          {/each}
        </div>

        <div class="h-px" style="background:var(--ws-border)"></div>

        <!-- WEG A -->
        {#if path === 'known'}
          <div class="relative">
            <label class={lbl} style="color:var(--ws-muted)">{travelMode === 'flight' ? $t('wwDestLabel') : $t('wwDestLabelAuto')}</label>
            <input value={s1DestInput} oninput={onDestInput}
              placeholder={travelMode === 'flight' ? $t('wwDestPlaceholder') : $t('wwDestPlaceholderAuto')}
              class={inp} style={inpS} autocomplete="off"/>
            {#if s1AcSuggestions.length > 0 && travelMode === 'flight'}
              <div class="absolute z-10 left-0 right-0 top-full mt-1 rounded-xl shadow-xl overflow-hidden border"
                style="background:var(--ws-surface);border-color:var(--ws-border)">
                {#each s1AcSuggestions as a}
                  <button onclick={() => pickDest(a)} class="w-full text-left px-4 py-2.5 text-sm hover:opacity-80" style="color:var(--ws-text)">
                    <span class="font-mono font-bold text-xs mr-2" style="color:var(--ws-accent)">{a.iata}</span>{a.city}
                    <span class="text-xs ml-1" style="color:var(--ws-muted)">{a.country}</span>
                  </button>
                {/each}
              </div>
            {/if}
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div><label class={lbl} style="color:var(--ws-muted)">{$t('wwDateFrom')}</label>
              <input type="date" bind:value={s1DateFrom} class={inp} style={inpS}/></div>
            <div><label class={lbl} style="color:var(--ws-muted)">{$t('wwDateTo')}</label>
              <input type="date" bind:value={s1DateTo} class={inp} style={inpS}/></div>
          </div>
          <div>
            <label class={lbl} style="color:var(--ws-muted)">{$t('wwTravelers')}</label>
            <div class="grid grid-cols-2 gap-3">
              {#each [[$t('wwAdults'),()=>s1Adults,v=>s1Adults=v,1,9],[$t('wwChildren'),()=>s1Children,v=>s1Children=v,0,8]] as [title,getter,setter,min,max]}
                <div class="rounded-xl border p-3 flex flex-col items-center gap-2" style="background:var(--ws-surface2);border-color:var(--ws-border)">
                  <div class="text-xs font-semibold" style="color:var(--ws-muted)">{title}</div>
                  <div class="flex items-center gap-3">
                    <button onclick={() => setter(Math.max(min,getter()-1))} class="w-8 h-8 rounded-xl border text-lg font-bold flex items-center justify-center" style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">−</button>
                    <span class="text-lg font-bold w-6 text-center" style="color:var(--ws-text)">{getter()}</span>
                    <button onclick={() => setter(Math.min(max,getter()+1))} class="w-8 h-8 rounded-xl border text-lg font-bold flex items-center justify-center" style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
                  </div>
                </div>
              {/each}
            </div>
          </div>
          {#if travelMode === 'flight'}
            <div class="relative">
              <label class={lbl} style="color:var(--ws-muted)">{$t('wwHomeAirport')}</label>
              <input value={s1HomeInput} oninput={onHomeInput} placeholder={$t('wwHomeAirportPlaceholder')} class={inp} style={inpS} autocomplete="off"/>
              {#if s1HomeAcSugg.length > 0}
                <div class="absolute z-10 left-0 right-0 top-full mt-1 rounded-xl shadow-xl overflow-hidden border" style="background:var(--ws-surface);border-color:var(--ws-border)">
                  {#each s1HomeAcSugg as a}
                    <button onclick={() => pickHome(a)} class="w-full text-left px-4 py-2.5 text-sm hover:opacity-80" style="color:var(--ws-text)">
                      <span class="font-mono font-bold text-xs mr-2" style="color:var(--ws-accent)">{a.iata}</span>{a.city}
                      <span class="text-xs ml-1" style="color:var(--ws-muted)">{a.country}</span>
                    </button>
                  {/each}
                </div>
              {/if}
            </div>
          {/if}

        <!-- WEG B -->
        {:else}
          <div class="rounded-xl px-4 py-3 text-sm" style="background:color-mix(in srgb,var(--ws-accent) 8%,var(--ws-surface));color:var(--ws-text);border:1px solid color-mix(in srgb,var(--ws-accent) 20%,transparent)">
            {$t('wwInspireModeNote')}
          </div>
          <div>
            <label class={lbl} style="color:var(--ws-muted)">{$t('wwTravelers')}</label>
            <div class="grid grid-cols-2 gap-3">
              {#each [[$t('wwAdults'),()=>s1Adults,v=>s1Adults=v,1,9],[$t('wwChildren'),()=>s1Children,v=>s1Children=v,0,8]] as [title,getter,setter,min,max]}
                <div class="rounded-xl border p-3 flex flex-col items-center gap-2" style="background:var(--ws-surface2);border-color:var(--ws-border)">
                  <div class="text-xs font-semibold" style="color:var(--ws-muted)">{title}</div>
                  <div class="flex items-center gap-3">
                    <button onclick={() => setter(Math.max(min,getter()-1))} class="w-8 h-8 rounded-xl border text-lg font-bold flex items-center justify-center" style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">−</button>
                    <span class="text-lg font-bold w-6 text-center" style="color:var(--ws-text)">{getter()}</span>
                    <button onclick={() => setter(Math.min(max,getter()+1))} class="w-8 h-8 rounded-xl border text-lg font-bold flex items-center justify-center" style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
                  </div>
                </div>
              {/each}
            </div>
          </div>
          {#if travelMode === 'flight'}
            <div class="relative">
              <label class={lbl} style="color:var(--ws-muted)">{$t('wwHomeAirport')}</label>
              <input value={s1HomeInput} oninput={onHomeInput} placeholder={$t('wwHomeAirportPlaceholder')} class={inp} style={inpS} autocomplete="off"/>
              {#if s1HomeAcSugg.length > 0}
                <div class="absolute z-10 left-0 right-0 top-full mt-1 rounded-xl shadow-xl overflow-hidden border" style="background:var(--ws-surface);border-color:var(--ws-border)">
                  {#each s1HomeAcSugg as a}
                    <button onclick={() => pickHome(a)} class="w-full text-left px-4 py-2.5 text-sm hover:opacity-80" style="color:var(--ws-text)">
                      <span class="font-mono font-bold text-xs mr-2" style="color:var(--ws-accent)">{a.iata}</span>{a.city}
                      <span class="text-xs ml-1" style="color:var(--ws-muted)">{a.country}</span>
                    </button>
                  {/each}
                </div>
              {/if}
            </div>
          {/if}
          <div>
            <div class="flex items-center gap-1 mb-3 p-1 rounded-xl" style="background:var(--ws-surface2);border:1px solid var(--ws-border)">
              {#each [['exact',$t('wwDateModeExact')],['flexible',$t('wwDateModeFlexible')]] as [m,label]}
                <button onclick={() => s1DateMode = m} class="flex-1 py-1.5 rounded-lg text-xs font-semibold transition-all"
                  style={s1DateMode===m ? 'background:var(--ws-accent);color:#fff5ec;box-shadow:0 1px 4px rgba(0,0,0,.15)' : 'color:var(--ws-muted)'}>{label}</button>
              {/each}
            </div>
            {#if s1DateMode === 'exact'}
              <div class="grid grid-cols-2 gap-3">
                <div><label class={lbl} style="color:var(--ws-muted)">{$t('wwDateFrom')}</label><input type="date" bind:value={s1DateFrom} class={inp} style={inpS}/></div>
                <div><label class={lbl} style="color:var(--ws-muted)">{$t('wwDateTo')}</label><input type="date" bind:value={s1DateTo} class={inp} style={inpS}/></div>
              </div>
            {:else}
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class={lbl} style="color:var(--ws-muted)">{$t('wwFlexMonth')}</label>
                  <select value={s1FlexMonth} onchange={(e) => s1FlexMonth = e.target.value} class={inp} style={inpS}>
                    <option value="">—</option>
                    {#each flexMonthOptions as opt}<option value={opt}>{opt}</option>{/each}
                  </select>
                </div>
                <div>
                  <label class={lbl} style="color:var(--ws-muted)">{$t('wwFlexNights')}</label>
                  <div class="flex items-center gap-2">
                    <button onclick={() => s1FlexNights=Math.max(1,s1FlexNights-1)} class="w-9 h-9 rounded-xl border text-lg font-bold flex items-center justify-center" style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">−</button>
                    <span class="flex-1 text-center font-bold" style="color:var(--ws-text)">{s1FlexNights}</span>
                    <button onclick={() => s1FlexNights=Math.min(30,s1FlexNights+1)} class="w-9 h-9 rounded-xl border text-lg font-bold flex items-center justify-center" style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
                  </div>
                </div>
              </div>
            {/if}
          </div>
          <div>
            <label class={lbl} style="color:var(--ws-muted)">{maxTimeLabel}</label>
            <div class="flex flex-wrap gap-2">
              {#each [['2h','2h'],['4h','4h'],['6h','6h'],['8h','8h'],['any',$t('wwMaxTimeAny')]] as [val,label]}
                <button onclick={() => s1MaxTime=val} class="px-3.5 py-1.5 rounded-xl border text-sm font-medium transition-all"
                  style={s1MaxTime===val ? 'background:var(--ws-accent);border-color:var(--ws-accent);color:#fff5ec' : 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)'}>{label}</button>
              {/each}
            </div>
          </div>
          <div>
            <label class={lbl} style="color:var(--ws-muted)">{$t('wwVibeLabel')}</label>
            <div class="flex flex-wrap gap-2">
              {#each VIBES as [key,tk]}
                <button onclick={() => toggleVibe(key)} class="px-3 py-1.5 rounded-full border text-sm transition-all"
                  style={s1Vibes.includes(key) ? 'background:var(--ws-accent);border-color:var(--ws-accent);color:#fff5ec;font-weight:600' : 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)'}>{$t(tk)}</button>
              {/each}
            </div>
          </div>
          <div>
            <label class={lbl} style="color:var(--ws-muted)">{$t('wwWishLabel')}</label>
            <textarea bind:value={s1Wish} placeholder={$t('wwWishPlaceholder')} rows="2" class={inp + ' resize-none'} style={inpS}></textarea>
          </div>
        {/if}

        <!-- Budget -->
        <div class="rounded-xl border p-4" style="background:var(--ws-surface2);border-color:var(--ws-border)">
          <label class={lbl} style="color:var(--ws-muted)">{$t('wwBudgetLabel')}</label>
          <div class="flex items-center gap-3">
            <input type="range" min="0" max="5000" step="50" value={s1Budget} oninput={(e) => s1Budget=parseInt(e.target.value)} class="flex-1 accent-[var(--ws-accent)]"/>
            <div class="flex items-center border rounded-xl overflow-hidden shrink-0" style="background:var(--ws-surface);border-color:var(--ws-border)">
              <input type="number" min="0" step="50" value={s1Budget} oninput={(e) => s1Budget=parseInt(e.target.value)||0} class="w-20 px-2 py-1.5 text-sm text-right bg-transparent focus:outline-none" style="color:var(--ws-text)"/>
              <span class="px-2 text-sm" style="color:var(--ws-muted)">€</span>
            </div>
          </div>
          {#if s1Budget > 0}<p class="text-xs mt-1.5" style="color:var(--ws-accent)">{budgetHint}</p>{/if}
        </div>

      <!-- ══ STEP 2: Zusammenfassung ══════════════════════════════════════════ -->
      {:else if step === 2}
        <div class="space-y-4">
          <h3 class="font-bold text-base" style="color:var(--ws-text)">{$t('wwSummaryTitle')}</h3>
          <div class="rounded-2xl border overflow-hidden" style="border-color:var(--ws-border)">
            {#each summaryRows as [icon,label,value]}
              <div class="flex items-center gap-3 px-4 py-3 border-b last:border-b-0" style="border-color:var(--ws-border)">
                <span class="text-base w-6 text-center shrink-0">{icon}</span>
                <span class="text-xs font-semibold shrink-0 w-28" style="color:var(--ws-muted)">{label}</span>
                <span class="text-sm font-medium text-right flex-1" style="color:var(--ws-text)">{value}</span>
              </div>
            {/each}
          </div>
          <p class="text-xs px-1" style="color:var(--ws-muted)">
            {path === 'inspire' ? $t('wwSummaryHintInspire') : $t('wwSummaryHint')}
          </p>
        </div>
      {/if}
    </div>

    <!-- Footer -->
    <div class="px-5 py-4 border-t shrink-0 flex gap-3" style="border-color:var(--ws-border)">
      {#if step === 1}
        <button onclick={close} class="flex-1 py-2.5 rounded-xl border text-sm font-semibold hover:opacity-70 transition-opacity" style="border-color:var(--ws-border);color:var(--ws-muted)">{$t('wwBtnCancel')}</button>
        <button onclick={() => { if (step1Valid) step = 2; }} disabled={!step1Valid}
          class="flex-1 py-2.5 rounded-xl text-sm font-semibold hover:opacity-80 disabled:opacity-40 transition-opacity"
          style="background:var(--ws-accent);color:#fff5ec">{$t('wwBtnNext')}</button>
      {:else}
        <button onclick={() => step = 1} class="flex-1 py-2.5 rounded-xl border text-sm font-semibold hover:opacity-70 transition-opacity" style="border-color:var(--ws-border);color:var(--ws-muted)">{$t('wwBtnBack')}</button>
        <button onclick={createTrip} disabled={creating}
          class="flex-1 py-2.5 rounded-xl text-sm font-semibold hover:opacity-80 disabled:opacity-60 transition-opacity"
          style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
          {creating ? $t('wizzardCreating') : (path === 'inspire' ? $t('wwBtnInspire') : $t('wwBtnCreateTrip'))}
        </button>
      {/if}
    </div>

  </div>
</div>
{/if}

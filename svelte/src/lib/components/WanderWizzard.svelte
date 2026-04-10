<script>
  import { t } from '$lib/i18n.js';
  import { AIRPORTS } from '$lib/components/priceradar/constants.js';
  import { currentPage } from '$lib/stores.js';
  import { priceradarParams } from '$lib/stores.js';

  // ── Props ──────────────────────────────────────────────────────────────────
  let {
    open          = $bindable(false),
    destination   = '',
    dateFrom      = '',
    dateTo        = '',
    adults        = 2,
    children      = 0,
    homeAirport   = '',
    tripType      = '',
    budget        = 0,
    // WW Defaults (aus user_settings)
    lugS10        = 0,
    lugS20        = 0,
    lugS23        = 0,
    lugL10        = 0,
    lugL20        = 1,
    lugL23        = 0,
    depMin        = '',
    depMax        = '',
    arrMin        = '',
    arrMax        = '',
  } = $props();

  // ── Step State ─────────────────────────────────────────────────────────────
  let step = $state(destination ? 2 : 1);

  // Step 1
  let s1Dest       = $state(destination);
  let s1DateFrom   = $state(dateFrom);
  let s1DateTo     = $state(dateTo);
  let s1Adults     = $state(adults);
  let s1Children   = $state(children);
  let s1Home       = $state(homeAirport);
  let s1DestInput  = $state(destination);
  let s1AcSuggestions = $state([]);
  let s1HomeInput  = $state(homeAirport);
  let s1HomeAcSugg = $state([]);

  // Step 2
  let s2TripTypes  = $state(tripType ? [tripType] : []);
  let s2Budget     = $state(budget || 0);
  let s2LugPreset  = $state(''); // '' | 'short' | 'long'
  let s2Lug10      = $state(0);
  let s2Lug20      = $state(0);
  let s2Lug23      = $state(0);
  let s2DepMin     = $state(depMin);
  let s2DepMax     = $state(depMax);
  let s2ArrMin     = $state(arrMin);
  let s2ArrMax     = $state(arrMax);

  // ── Helpers ────────────────────────────────────────────────────────────────
  const inputCls   = 'w-full px-3 py-2 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ws-accent)]';
  const inputStyle = 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)';
  const labelCls   = 'block text-xs font-bold uppercase tracking-wider mb-1.5';

  function filterAirports(q) {
    if (!q || q.length < 1) return [];
    const ql = q.toLowerCase();
    return AIRPORTS.filter(a =>
      a.iata.toLowerCase().startsWith(ql) ||
      a.city.toLowerCase().includes(ql)
    ).slice(0, 6);
  }

  function onDestInput(e) {
    s1DestInput = e.target.value;
    s1Dest = e.target.value;
    s1AcSuggestions = filterAirports(e.target.value);
  }

  function pickDest(a) {
    s1Dest      = a.iata;
    s1DestInput = `${a.iata} – ${a.city}`;
    s1AcSuggestions = [];
  }

  function onHomeInput(e) {
    s1HomeInput  = e.target.value;
    s1Home       = e.target.value.slice(0, 3).toUpperCase();
    s1HomeAcSugg = filterAirports(e.target.value);
  }

  function pickHome(a) {
    s1Home      = a.iata;
    s1HomeInput = `${a.iata} – ${a.city}`;
    s1HomeAcSugg = [];
  }

  function applyLugPreset(preset) {
    s2LugPreset = preset;
    if (preset === 'short') {
      s2Lug10 = lugS10; s2Lug20 = lugS20; s2Lug23 = lugS23;
    } else if (preset === 'long') {
      s2Lug10 = lugL10; s2Lug20 = lugL20; s2Lug23 = lugL23;
    }
  }

  function toggleTripType(tt) {
    if (s2TripTypes.includes(tt)) {
      s2TripTypes = s2TripTypes.filter(x => x !== tt);
    } else {
      s2TripTypes = [...s2TripTypes, tt];
    }
  }

  function toStep2() {
    if (!s1Dest || !s1DateFrom) return;
    step = 2;
  }

  function toStep3() {
    step = 3;
  }

  function close() { open = false; }

  // Step indicator label
  const STEPS = ['Wohin & Wann', 'Art & Budget', 'Zusammenfassung'];

  // Summary helpers
  const luggageSummary = $derived.by(() => {
    const parts = [];
    if (s2Lug10 > 0) parts.push(`${s2Lug10}×10kg`);
    if (s2Lug20 > 0) parts.push(`${s2Lug20}×20kg`);
    if (s2Lug23 > 0) parts.push(`${s2Lug23}×23kg`);
    return parts.length ? parts.join(', ') : 'Kein Gepäck';
  });

  const tripTypesLabel = $derived(
    s2TripTypes.length
      ? s2TripTypes.map(tt => ({ flight: '✈️ Flug', hotel: '🏨 Hotel', camping: '⛺ Camping', car: '🚗 Mietwagen' }[tt] || tt)).join(' · ')
      : '—'
  );

  function startSearch() {
    priceradarParams.set({
      destination: s1Dest,
      dateFrom:    s1DateFrom,
      dateTo:      s1DateTo,
      adults:      s1Adults,
      children:    s1Children,
      homeAirport: s1Home,
      tripTypes:   s2TripTypes,
      budget:      s2Budget,
      lug10:       s2Lug10,
      lug20:       s2Lug20,
      lug23:       s2Lug23,
      depMin:      s2DepMin,
      depMax:      s2DepMax,
      arrMin:      s2ArrMin,
      arrMax:      s2ArrMax,
    });
    currentPage.set('priceradar');
    open = false;
  }
</script>

{#if open}
<!-- Backdrop -->
<div
  class="fixed inset-0 z-50 flex items-center justify-center"
  style="background:rgba(0,0,0,.5);backdrop-filter:blur(4px)"
  role="dialog"
  aria-modal="true">

  <!-- Modal -->
  <div class="fixed inset-0 md:inset-[5vh_10vw] flex flex-col rounded-none md:rounded-2xl overflow-hidden shadow-2xl"
    style="background:var(--ws-surface);border:1px solid var(--ws-border)">

    <!-- Header -->
    <div class="flex items-center gap-3 px-5 py-4 border-b shrink-0"
      style="border-color:var(--ws-border)">
      <span class="text-xl">🧙</span>
      <div class="flex-1">
        <h2 class="font-bold text-base" style="color:var(--ws-text)">WanderWizzard</h2>
        <p class="text-xs" style="color:var(--ws-muted)">Dein Reise-Assistent</p>
      </div>
      <button onclick={close}
        class="w-8 h-8 rounded-xl flex items-center justify-center text-lg transition-opacity hover:opacity-60"
        style="color:var(--ws-muted)">✕</button>
    </div>

    <!-- Step Indicator -->
    <div class="px-5 pt-4 pb-2 shrink-0">
      <div class="flex items-center gap-0">
        {#each STEPS as label, i}
          {@const idx = i + 1}
          {@const done = step > idx}
          {@const active = step === idx}
          <div class="flex items-center gap-0 flex-1 {i < STEPS.length - 1 ? '' : ''}">
            <div class="flex flex-col items-center gap-1 shrink-0">
              <div class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all"
                style={done   ? 'background:var(--ws-green);color:#fff'
                      : active ? 'background:var(--ws-accent);color:#fff5ec'
                      : 'background:var(--ws-surface2);border:1px solid var(--ws-border);color:var(--ws-muted)'}>
                {done ? '✓' : idx}
              </div>
              <span class="text-[10px] font-semibold whitespace-nowrap hidden sm:block"
                style="color:{active ? 'var(--ws-accent)' : done ? 'var(--ws-green)' : 'var(--ws-muted)'}">{label}</span>
            </div>
            {#if i < STEPS.length - 1}
              <div class="flex-1 h-0.5 mx-1 rounded"
                style="background:{done ? 'var(--ws-green)' : 'var(--ws-border)'}"></div>
            {/if}
          </div>
        {/each}
      </div>
    </div>

    <!-- Body (scrollable) -->
    <div class="flex-1 overflow-y-auto px-5 py-4 space-y-5">

      <!-- ── STEP 1: Wohin & Wann ──────────────────────────────────────── -->
      {#if step === 1}

        <!-- Destination -->
        <div class="relative">
          <label class={labelCls} style="color:var(--ws-muted)">🌍 Reiseziel / Zielflughafen</label>
          <input
            value={s1DestInput}
            oninput={onDestInput}
            placeholder="z.B. Barcelona, BGY, Mallorca…"
            class={inputCls} style={inputStyle}
            autocomplete="off"/>
          {#if s1AcSuggestions.length > 0}
            <div class="absolute z-10 left-0 right-0 top-full mt-1 rounded-xl shadow-xl overflow-hidden border"
              style="background:var(--ws-surface);border-color:var(--ws-border)">
              {#each s1AcSuggestions as a}
                <button onclick={() => pickDest(a)}
                  class="w-full text-left px-4 py-2.5 text-sm transition-colors hover:opacity-80"
                  style="color:var(--ws-text)">
                  <span class="font-mono font-bold text-xs mr-2" style="color:var(--ws-accent)">{a.iata}</span>
                  {a.city}
                  <span class="text-xs ml-1" style="color:var(--ws-muted)">{a.country}</span>
                </button>
              {/each}
            </div>
          {/if}
        </div>

        <!-- Dates -->
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class={labelCls} style="color:var(--ws-muted)">📅 Hinreise</label>
            <input type="date" bind:value={s1DateFrom} class={inputCls} style={inputStyle}/>
          </div>
          <div>
            <label class={labelCls} style="color:var(--ws-muted)">📅 Rückreise</label>
            <input type="date" bind:value={s1DateTo} class={inputCls} style={inputStyle}/>
          </div>
        </div>

        <!-- Personen -->
        <div>
          <label class={labelCls} style="color:var(--ws-muted)">👥 Reisende</label>
          <div class="grid grid-cols-2 gap-3">
            <!-- Erwachsene -->
            <div class="rounded-xl border p-3 flex flex-col items-center gap-2"
              style="background:var(--ws-surface2);border-color:var(--ws-border)">
              <div class="text-xs font-semibold" style="color:var(--ws-muted)">Erwachsene</div>
              <div class="flex items-center gap-3">
                <button onclick={() => s1Adults = Math.max(1, s1Adults - 1)}
                  class="w-8 h-8 rounded-xl border text-lg font-bold flex items-center justify-center"
                  style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">−</button>
                <span class="text-lg font-bold w-6 text-center" style="color:var(--ws-text)">{s1Adults}</span>
                <button onclick={() => s1Adults = Math.min(9, s1Adults + 1)}
                  class="w-8 h-8 rounded-xl border text-lg font-bold flex items-center justify-center"
                  style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
              </div>
            </div>
            <!-- Kinder -->
            <div class="rounded-xl border p-3 flex flex-col items-center gap-2"
              style="background:var(--ws-surface2);border-color:var(--ws-border)">
              <div class="text-xs font-semibold" style="color:var(--ws-muted)">Kinder (2–11 J.)</div>
              <div class="flex items-center gap-3">
                <button onclick={() => s1Children = Math.max(0, s1Children - 1)}
                  class="w-8 h-8 rounded-xl border text-lg font-bold flex items-center justify-center"
                  style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">−</button>
                <span class="text-lg font-bold w-6 text-center" style="color:var(--ws-text)">{s1Children}</span>
                <button onclick={() => s1Children = Math.min(8, s1Children + 1)}
                  class="w-8 h-8 rounded-xl border text-lg font-bold flex items-center justify-center"
                  style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Heimatflughafen -->
        <div class="relative">
          <label class={labelCls} style="color:var(--ws-muted)">🛫 Heimatflughafen</label>
          <input
            value={s1HomeInput}
            oninput={onHomeInput}
            placeholder="z.B. BGY – Bergamo / Mailand"
            class={inputCls} style={inputStyle}
            autocomplete="off"/>
          {#if s1HomeAcSugg.length > 0}
            <div class="absolute z-10 left-0 right-0 top-full mt-1 rounded-xl shadow-xl overflow-hidden border"
              style="background:var(--ws-surface);border-color:var(--ws-border)">
              {#each s1HomeAcSugg as a}
                <button onclick={() => pickHome(a)}
                  class="w-full text-left px-4 py-2.5 text-sm transition-colors hover:opacity-80"
                  style="color:var(--ws-text)">
                  <span class="font-mono font-bold text-xs mr-2" style="color:var(--ws-accent)">{a.iata}</span>
                  {a.city}
                  <span class="text-xs ml-1" style="color:var(--ws-muted)">{a.country}</span>
                </button>
              {/each}
            </div>
          {/if}
        </div>

      <!-- ── STEP 2: Art & Budget ─────────────────────────────────────────── -->
      {:else if step === 2}

        <!-- Trip-Typ -->
        <div>
          <label class={labelCls} style="color:var(--ws-muted)">🗂️ Art der Reise (Mehrfachauswahl)</label>
          <div class="grid grid-cols-2 gap-2">
            {#each [
              ['flight',  '✈️ Flug'],
              ['hotel',   '🏨 Hotel'],
              ['camping', '⛺ Camping'],
              ['car',     '🚗 Mietwagen'],
            ] as [val, label]}
              <button onclick={() => toggleTripType(val)}
                class="py-3 rounded-xl border text-sm font-semibold transition-all"
                style={s2TripTypes.includes(val)
                  ? 'background:var(--ws-accent);border-color:var(--ws-accent);color:#fff5ec'
                  : 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)'}>
                {label}
              </button>
            {/each}
          </div>
        </div>

        <!-- Budget -->
        <div>
          <label class={labelCls} style="color:var(--ws-muted)">💶 Budget (€ gesamt)</label>
          <div class="flex items-center gap-3">
            <input type="range" min="0" max="5000" step="50"
              value={s2Budget}
              oninput={(e) => s2Budget = parseInt(e.target.value)}
              class="flex-1 accent-[var(--ws-accent)]"/>
            <div class="flex items-center border rounded-xl overflow-hidden shrink-0"
              style="background:var(--ws-surface2);border-color:var(--ws-border)">
              <input type="number" min="0" step="50"
                value={s2Budget}
                oninput={(e) => s2Budget = parseInt(e.target.value) || 0}
                class="w-24 px-3 py-2 text-sm text-right bg-transparent focus:outline-none"
                style="color:var(--ws-text)"/>
              <span class="px-2 text-sm" style="color:var(--ws-muted)">€</span>
            </div>
          </div>
          {#if s2Budget > 0}
            <p class="text-xs mt-1" style="color:var(--ws-accent)">
              Max. {s2Budget} € für {s1Adults + s1Children} Person{s1Adults + s1Children !== 1 ? 'en' : ''}
              {#if s1Adults + s1Children > 1}
                · Ø {Math.round(s2Budget / (s1Adults + s1Children))} € / Person
              {/if}
            </p>
          {/if}
        </div>

        <!-- Gepäck-Schnellwahl -->
        <div>
          <label class={labelCls} style="color:var(--ws-muted)">🧳 Gepäck-Preset</label>
          <div class="grid grid-cols-2 gap-2 mb-3">
            <button onclick={() => applyLugPreset('short')}
              class="py-2.5 rounded-xl border text-sm font-semibold transition-all"
              style={s2LugPreset === 'short'
                ? 'background:var(--ws-accent);border-color:var(--ws-accent);color:#fff5ec'
                : 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)'}>
              ⚡ Kurztrip
            </button>
            <button onclick={() => applyLugPreset('long')}
              class="py-2.5 rounded-xl border text-sm font-semibold transition-all"
              style={s2LugPreset === 'long'
                ? 'background:var(--ws-accent);border-color:var(--ws-accent);color:#fff5ec'
                : 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)'}>
              🌍 Langtrip
            </button>
          </div>
          <!-- Gepäck Stepper -->
          <div class="rounded-xl border p-3 space-y-2" style="background:var(--ws-surface2);border-color:var(--ws-border)">
            {#each [
              ['10 kg', () => s2Lug10, v => { s2Lug10 = v; s2LugPreset = ''; }],
              ['20 kg', () => s2Lug20, v => { s2Lug20 = v; s2LugPreset = ''; }],
              ['23 kg', () => s2Lug23, v => { s2Lug23 = v; s2LugPreset = ''; }],
            ] as [lbl, getter, setter]}
              <div class="flex items-center justify-between gap-2">
                <span class="text-xs w-12 shrink-0" style="color:var(--ws-muted)">{lbl}</span>
                <div class="flex items-center gap-2">
                  <button onclick={() => setter(Math.max(0, getter() - 1))}
                    class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center"
                    style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">−</button>
                  <span class="w-5 text-center text-sm font-bold"
                    style="color:{getter() > 0 ? 'var(--ws-accent)' : 'var(--ws-muted)'}">{getter()}</span>
                  <button onclick={() => setter(Math.min(9, getter() + 1))}
                    class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center"
                    style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
                </div>
              </div>
            {/each}
          </div>
        </div>

        <!-- Flugzeit-Fenster -->
        <details class="rounded-xl border overflow-hidden" style="border-color:var(--ws-border)">
          <summary class="px-4 py-3 text-sm font-semibold cursor-pointer select-none"
            style="background:var(--ws-surface2);color:var(--ws-text);list-style:none">
            ⏱️ Flugzeit-Präferenzen
            {#if s2DepMin || s2DepMax || s2ArrMin || s2ArrMax}
              <span class="ml-2 text-xs px-2 py-0.5 rounded-full font-semibold"
                style="background:var(--ws-accent);color:#fff5ec">aktiv</span>
            {/if}
          </summary>
          <div class="p-4 grid grid-cols-2 gap-4" style="background:var(--ws-surface)">
            <div class="space-y-2">
              <div class="text-xs font-semibold" style="color:var(--ws-text)">🛫 Abflug</div>
              <div class="grid grid-cols-2 gap-2">
                <div>
                  <label class="block text-xs mb-1" style="color:var(--ws-muted)">ab</label>
                  <input type="time" bind:value={s2DepMin} class={inputCls} style={inputStyle}/>
                </div>
                <div>
                  <label class="block text-xs mb-1" style="color:var(--ws-muted)">bis</label>
                  <input type="time" bind:value={s2DepMax} class={inputCls} style={inputStyle}/>
                </div>
              </div>
            </div>
            <div class="space-y-2">
              <div class="text-xs font-semibold" style="color:var(--ws-text)">🛬 Ankunft</div>
              <div class="grid grid-cols-2 gap-2">
                <div>
                  <label class="block text-xs mb-1" style="color:var(--ws-muted)">ab</label>
                  <input type="time" bind:value={s2ArrMin} class={inputCls} style={inputStyle}/>
                </div>
                <div>
                  <label class="block text-xs mb-1" style="color:var(--ws-muted)">bis</label>
                  <input type="time" bind:value={s2ArrMax} class={inputCls} style={inputStyle}/>
                </div>
              </div>
            </div>
            <div class="col-span-2">
              <button onclick={() => { s2DepMin=''; s2DepMax=''; s2ArrMin=''; s2ArrMax=''; }}
                class="text-xs px-3 py-1.5 rounded-lg border transition-opacity hover:opacity-70"
                style="border-color:var(--ws-border);color:var(--ws-muted)">↺ Zurücksetzen</button>
            </div>
          </div>
        </details>

      <!-- ── STEP 3: Zusammenfassung ─────────────────────────────────────── -->
      {:else if step === 3}

        <div class="space-y-4">
          <h3 class="font-bold text-base" style="color:var(--ws-text)">📋 Deine Suche auf einen Blick</h3>

          <div class="rounded-xl border divide-y" style="border-color:var(--ws-border)">
            {#each [
              ['🌍 Ziel',         s1Dest || '—'],
              ['📅 Reisedaten',   s1DateFrom ? `${s1DateFrom}${s1DateTo ? ' → ' + s1DateTo : ''}` : '—'],
              ['👥 Reisende',     `${s1Adults} Erw.${s1Children > 0 ? ' · ' + s1Children + ' Kind.' : ''}`],
              ['🛫 Heimatflugh.', s1Home || '—'],
              ['🗂️ Art',          tripTypesLabel],
              ['💶 Budget',       s2Budget > 0 ? s2Budget + ' €' : 'Kein Limit'],
              ['🧳 Gepäck',       luggageSummary],
              ['⏱️ Abflug',       (s2DepMin || s2DepMax) ? `${s2DepMin || '—'} – ${s2DepMax || '—'}` : 'Keine Präferenz'],
              ['⏱️ Ankunft',      (s2ArrMin || s2ArrMax) ? `${s2ArrMin || '—'} – ${s2ArrMax || '—'}` : 'Keine Präferenz'],
            ] as [lbl, val]}
              <div class="flex justify-between items-center px-4 py-3 gap-4"
                style="border-color:var(--ws-border)">
                <span class="text-xs font-semibold shrink-0" style="color:var(--ws-muted)">{lbl}</span>
                <span class="text-sm font-medium text-right" style="color:var(--ws-text)">{val}</span>
              </div>
            {/each}
          </div>

          <p class="text-xs" style="color:var(--ws-muted)">
            💡 Nach dem Start kannst du die Ergebnisse im PriceRadar nach Anbieter filtern und als Tracker speichern.
          </p>
        </div>

      {/if}
    </div>

    <!-- Footer (Navigation) -->
    <div class="px-5 py-4 border-t shrink-0 flex gap-3" style="border-color:var(--ws-border)">
      {#if step === 1}
        <button onclick={close}
          class="flex-1 py-2.5 rounded-xl border text-sm font-semibold transition-opacity hover:opacity-70"
          style="border-color:var(--ws-border);color:var(--ws-muted)">Abbrechen</button>
        <button onclick={toStep2} disabled={!s1Dest || !s1DateFrom}
          class="flex-1 py-2.5 rounded-xl text-sm font-semibold transition-opacity hover:opacity-80 disabled:opacity-40"
          style="background:var(--ws-accent);color:#fff5ec">
          Weiter →
        </button>

      {:else if step === 2}
        <button onclick={() => step = 1}
          class="flex-1 py-2.5 rounded-xl border text-sm font-semibold transition-opacity hover:opacity-70"
          style="border-color:var(--ws-border);color:var(--ws-muted)">← Zurück</button>
        <button onclick={toStep3}
          class="flex-1 py-2.5 rounded-xl text-sm font-semibold transition-opacity hover:opacity-80"
          style="background:var(--ws-accent);color:#fff5ec">
          Zusammenfassung →
        </button>

      {:else if step === 3}
        <button onclick={() => step = 2}
          class="flex-1 py-2.5 rounded-xl border text-sm font-semibold transition-opacity hover:opacity-70"
          style="border-color:var(--ws-border);color:var(--ws-muted)">← Anpassen</button>
        <button onclick={startSearch}
          class="flex-1 py-2.5 rounded-xl text-sm font-semibold transition-opacity hover:opacity-80"
          style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
          🔍 Jetzt suchen
        </button>
      {/if}
    </div>

  </div>
</div>
{/if}

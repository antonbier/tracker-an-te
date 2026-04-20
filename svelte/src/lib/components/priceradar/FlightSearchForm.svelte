<script>
  import { get } from 'svelte/store';
  import { t } from '$lib/i18n.js';
  import { AIRPORTS, inputCls, inputStyle, labelCls } from './constants.js';
  import { dateOffset } from './helpers.js';

  const { searching, onsearch, prefillParams = null } = $props();

  // Auto-fill when prefillParams changes (from TripHub deep-link)
  $effect(() => {
    if (!prefillParams) return;
    const p = prefillParams;
    if (p.destination) { flDest = p.destination; }
    if (p.dateFrom)    { flOut  = p.dateFrom; }
    if (p.dateTo)      { flRet  = p.dateTo; }
    if (p.adults)      { flAdults = parseInt(p.adults) || 1; }
    if (p.homeAirport) { flOrigin = p.homeAirport; }
  });

  // ── Form state ────────────────────────────────────────────────────────────
  let flOrigin    = $state('BGY');
  let flDest      = $state('DUB');
  let flOut       = $state(dateOffset(30));
  let flRet       = $state('');
  let flAdults    = $state(1);
  let flChildren  = $state(0);
  let fl10kg      = $state(0);
  let fl20kg      = $state(0);
  let fl23kg      = $state(0);
  let fl10kgPrice = $state(0);
  let fl20kgPrice = $state(0);
  let fl23kgPrice = $state(0);
  let flSeatCost  = $state(0);
  let flDepFrom   = $state('');
  let flDepTo     = $state('');
  let flArrFrom   = $state('');
  let flArrTo     = $state('');
  let flMaxStops  = $state(-1);
  let acState     = $state({});

  // ── Derived ───────────────────────────────────────────────────────────────
  const flBaggageCost = $derived(fl10kg * fl10kgPrice + fl20kg * fl20kgPrice + fl23kg * fl23kgPrice);
  const flTotalPax    = $derived(flAdults + flChildren);
  const flExtrasLabel = $derived.by(() => {
  const parts = [];
  if (fl10kg > 0)     parts.push(fl10kg + '× 10kg');
  if (fl20kg > 0)     parts.push(fl20kg + '× 20kg');
  if (fl23kg > 0)     parts.push(fl23kg + '× 23kg');
  if (flSeatCost > 0) parts.push(get(t)('radarSeatBadge').replace('{n}', flSeatCost));
  return parts.join(' · ');
});

  // ── Autocomplete helpers ──────────────────────────────────────────────────
  function acFilter(key, value) {
    if (!value || value.length < 1) { acState = { ...acState, [key]: { open: false, items: [] } }; return; }
    const q = value.toLowerCase();
    const items = AIRPORTS.filter(a =>
      a.iata.toLowerCase().startsWith(q) ||
      a.city.toLowerCase().includes(q) ||
      a.country.toLowerCase().includes(q)
    ).slice(0, 8);
    acState = { ...acState, [key]: { open: items.length > 0, items } };
  }
  function acSelect(key, iata, setter) {
    setter(iata);
    acState = { ...acState, [key]: { open: false, items: [] } };
  }
  function acClose(key) {
    setTimeout(() => { acState = { ...acState, [key]: { open: false, items: [] } }; }, 150);
  }

  // ── Search ────────────────────────────────────────────────────────────────
  function handleSearch() {
    onsearch({
      origin:        flOrigin.toUpperCase(),
      destination:   flDest.toUpperCase(),
      outbound_date: flOut,
      return_date:   flRet || null,
      adults:        flAdults,
      children:      flChildren,
      baggage:       'none',
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
    });
  }
</script>

<div class="rounded-xl p-4 border space-y-4" style="background:var(--ws-surface);border-color:var(--ws-border)">
  <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">✈️ {$t('radarFlights')}</h2>

  <!-- Origin / Destination mit Autocomplete -->
  <div class="grid grid-cols-2 gap-3">
    <div class="relative">
      <label class="{labelCls}" style="color:var(--ws-muted)">{$t('radarDeparture')}</label>
      <input bind:value={flOrigin} placeholder="BGY" maxlength="3"
        class="{inputCls} font-mono uppercase" style={inputStyle}
        oninput={() => acFilter('flOrigin', flOrigin)}
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
        oninput={() => acFilter('flDest', flDest)}
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

  <!-- Akkordeon 1: Gepäck & Sitzplätze -->
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
        <!-- UX 4: Spalten-Header Gepäck-Stepper -->
        <div class="hidden sm:flex items-center gap-2 px-2.5 pt-1 pb-0.5">
          <span class="text-[10px] font-semibold w-10 shrink-0" style="color:var(--ws-muted)">Typ</span>
          <span class="text-[10px] font-semibold w-24 shrink-0 text-center" style="color:var(--ws-muted)">Anzahl</span>
          <span class="text-[10px] font-semibold flex-1 text-center" style="color:var(--ws-muted)">Aufpreis / Stück</span>
          <span class="text-[10px] font-semibold w-14 shrink-0 text-right" style="color:var(--ws-muted)">Total</span>
        </div>
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
                <input type="number"
                  value={pGetter()}
                  oninput={(e) => pSetter(parseFloat(e.currentTarget.value) || 0)}
                  min="0" step="0.01"
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

  <!-- Akkordeon 2: Zeiten & Stopps -->
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

  <!-- Extras-Vorschau + Suche-Button -->
  {#if flExtrasLabel}
    <div class="text-xs px-1" style="color:var(--ws-muted)">
      ℹ️ Aufschlag wird auf Flugpreis addiert: {flExtrasLabel()}
    </div>
  {/if}
  <button
    onclick={handleSearch}
    disabled={searching || !flOrigin || !flDest || !flOut}
    class="w-full py-2.5 rounded-xl font-semibold text-sm transition-opacity hover:opacity-80 disabled:opacity-50"
    style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
    {searching ? $t('radarSearching') : '🔍 ' + $t('radarSearch')}
  </button>
</div>

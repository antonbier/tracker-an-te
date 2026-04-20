<script>
  import { t } from '$lib/i18n.js';
  import {
    fmtDate, overnightSuffix, fmtLayoverDur, parseJsonField,
    chartPts, priceTrend, isTopPrice,
    trackerTitle, trackerSubtitle, trackerBadges, providerIcon, providerLabel, trackerBookingUrl,
  } from './helpers.js';
  import { inputStyle } from './constants.js';

  const {
    tr,
    chartData    = $bindable(),
    wishData     = $bindable(),
    stopsOpenMap = $bindable(),
    wsTrips      = [],
    ondelete,
    onscrape,
    onwishsave,
    ontogglerchart,
    onwishedit,
    onlinktrip,
  } = $props();

  const wKey       = $derived(`${tr._type}-${tr.id}`);
  const s          = $derived(tr.latest_snapshot);
  // Block 8: current_price (root-level, immer frisch vom Backend) als primäre
  // Quelle — fällt auf latest_snapshot.total_price zurück wenn nicht vorhanden
  const price      = $derived(tr.current_price ?? s?.total_price);
  const wish       = $derived(tr.wish_price);
  const wishMet    = $derived(wish && price && price <= wish);
  const badges     = $derived(trackerBadges(tr, $t));
  const bookingUrl = $derived(trackerBookingUrl(tr));
  const subtitle   = $derived(trackerSubtitle(tr, $t));
  const title      = $derived(trackerTitle(tr));

  // ── Gradient per type (TripCard DNA) ─────────────────────────────────────
  const heroBg = $derived.by(() => {
    if (tr._type === 'flight' || tr._type === 'google_flight')
      return 'linear-gradient(135deg,#1a2a4a 0%,var(--ws-accent) 70%,#b84928 100%)';
    if (tr._type === 'hotel')
      return 'linear-gradient(135deg,#2a1a3a 0%,#7c3aed 70%,#4c1d95 100%)';
    if (tr._type === 'camping')
      return 'linear-gradient(135deg,#1a3a2a 0%,#2d6a4f 60%,#1a4a3a 100%)';
    return 'linear-gradient(135deg,#1e293b,#374151)';
  });

  // ── Trip linking dropdown ─────────────────────────────────────────────────
  let linkDropdownOpen = $state(false);
  const linkedTrip = $derived(
    wsTrips.find(t => t.id === tr.trip_id) || null
  );

  function linkEndpoint(type, id) {
    const map = {
      flight:        `/api/trackers/${id}/link-trip`,
      google_flight: `/api/google-flights/${id}/link-trip`,
      camping:       `/api/accommodations/homair/${id}/link-trip`,
      hotel:         `/api/accommodations/booking/${id}/link-trip`,
    };
    return map[type];
  }
</script>

<div
  class="rounded-2xl border overflow-hidden flex flex-col transition-all h-full"
  style="border-color:{wishMet ? 'var(--ws-green)' : 'var(--ws-border)'};
         background:var(--ws-surface);
         {wishMet ? 'box-shadow:0 0 0 2px rgba(22,163,74,.2)' : ''}">

  <!-- ── Hero band (TripCard DNA) ─────────────────────────────────────────── -->
  <div class="relative px-4 py-3 flex items-start justify-between gap-2"
    style="background:{heroBg};min-height:72px">
    <div class="absolute inset-0 opacity-10"
      style="background-image:radial-gradient(circle at 80% 20%,rgba(255,255,255,.3) 0%,transparent 60%)"></div>
    <div class="relative z-10 flex-1 min-w-0">
      <!-- Provider + type badge -->
      <div class="flex items-center gap-1.5 mb-1">
        <span class="text-[10px] font-bold px-2 py-0.5 rounded-full"
          style="background:rgba(255,255,255,.18);color:#fff;backdrop-filter:blur(6px)">
          {providerIcon(tr._type)} {providerLabel(tr)}
        </span>
        {#if wishMet}
          <span class="text-[10px] font-bold px-2 py-0.5 rounded-full"
            style="background:rgba(22,163,74,.25);color:#86efac">
            🎯 {$t('radarWishMet')}
          </span>
        {/if}
      </div>
      <!-- Title -->
      <div class="font-bold text-sm leading-tight text-white" style="font-family:var(--ws-serif);text-shadow:0 1px 6px rgba(0,0,0,.4)">{title}</div>
      <div class="text-[11px] mt-0.5" style="color:rgba(255,255,255,.7)">{subtitle}</div>
    </div>
    <!-- Buchen button (top right) -->
    <div class="relative z-10 shrink-0 flex flex-col items-end gap-1.5">
      {#if bookingUrl}
        <a href={bookingUrl} target="_blank" rel="noopener noreferrer"
          class="text-xs px-2.5 py-1 rounded-lg font-semibold transition-opacity hover:opacity-80 whitespace-nowrap"
          style="background:rgba(255,255,255,.2);color:#fff;text-decoration:none;backdrop-filter:blur(6px)">
          {$t('hubSlotBook')} ↗
        </a>
      {/if}
    </div>
  </div>

  <!-- ── Body ──────────────────────────────────────────────────────────────── -->
  <div class="flex flex-col gap-3 p-4 flex-1">

    <!-- Flight detail info -->
    {#if tr._type === 'flight' || tr._type === 'google_flight'}
      {@const snap         = tr.latest_snapshot}
      {@const showAirline  = snap?.airline}
      {@const showFlight   = snap?.flight_number || snap?.outbound_flight}
      {@const showTimes    = snap?.departure_time && snap?.arrival_time}
      {@const showDuration = snap?.duration_min}
      {#if showAirline || showFlight || showTimes}
        <div class="flex items-center gap-1.5 flex-wrap">
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
            {@const onSfx = overnightSuffix(snap.departure_time, snap.arrival_time, snap.duration_min)}
            <span class="text-xs font-mono" style="color:var(--ws-muted)">
              {snap.departure_time.slice(0,5)} → {snap.arrival_time.slice(0,5)}{onSfx ? ' ' + onSfx : ''}
            </span>
          {/if}
          {#if showDuration}
            <span class="text-xs" style="color:var(--ws-muted)">({Math.floor(snap.duration_min/60)}h{snap.duration_min%60}m)</span>
          {/if}
          {#if (snap?.stops ?? 0) > 0}
            {@const stopKey = tr._type+'-'+tr.id}
            <button onclick={() => stopsOpenMap[stopKey] = !stopsOpenMap[stopKey]}
              class="text-xs px-1.5 py-0.5 rounded font-medium cursor-pointer transition-opacity hover:opacity-70"
              style="background:rgba(37,99,235,.1);color:#2563eb;border:none">
              {snap.stops} Stopp{snap.stops > 1 ? 's' : ''} {stopsOpenMap[stopKey] ? '▴' : '▾'}
            </button>
            {#if stopsOpenMap[stopKey]}
              {@const layAirports  = parseJsonField(snap?.layover_airports)}
              {@const layDurations = parseJsonField(snap?.layover_durations)}
              {#if layAirports.length > 0}
                <div class="flex flex-wrap gap-1" style="width:100%;margin-top:2px">
                  {#each layAirports as via, i}
                    {@const dur = layDurations[i]}
                    <span class="text-xs px-2 py-0.5 rounded font-mono"
                      style="background:var(--ws-surface2);color:var(--ws-muted)">
                      via {via}{dur ? ` (${fmtLayoverDur(dur)} Aufenthalt)` : ''}
                    </span>
                  {/each}
                </div>
              {/if}
            {/if}
          {:else if tr._type === 'google_flight'}
            <span class="text-xs px-1.5 py-0.5 rounded font-medium"
              style="background:rgba(22,163,74,.1);color:var(--ws-green)">Nonstop</span>
          {/if}
        </div>
      {:else}
        <div class="text-xs" style="color:var(--ws-muted)">
          ✈️ {tr._type === 'flight' ? 'Ryanair' : 'Google Flights'} · {$t('radarNoScanYet') || 'noch kein Preis-Scan'}
        </div>
      {/if}
    {/if}

    <!-- Inclusion badges -->
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

    <!-- Price row -->
    <div class="flex items-end justify-between gap-2">
      <div>
        <div class="flex items-center gap-1.5">
          <div class="text-xs" style="color:var(--ws-muted)">{$t('radarCurrentPrice') || 'Aktuell'}</div>
          {#if chartData?.history?.length >= 2}
            {@const trend = priceTrend(chartData.history)}
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
        {#if chartData?.history?.length >= 2 && isTopPrice(chartData.history, price)}
          <div class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold mt-0.5"
            style="background:rgba(234,179,8,.15);color:#ca8a04;border:1px solid rgba(234,179,8,.3)">
            🏆 Top Preis
          </div>
        {/if}
      </div>
      {#if s?.fetched_at}
        <div class="text-[10px] text-right" style="color:var(--ws-muted)">
          {$t('radarLastScan') || 'Stand'}<br>{fmtDate(s.fetched_at.slice(0, 10))}
        </div>
      {/if}
    </div>

    <!-- Wunschpreis -->
    <div class="rounded-xl border px-3 py-2" style="background:var(--ws-surface2);border-color:{wish ? 'var(--ws-accent)' : 'var(--ws-border)'}">
      <div class="flex items-center justify-between gap-2">
        <span class="text-xs" style="color:var(--ws-muted)">🎯 {$t('radarWishPrice')}</span>
        {#if !wishData?.editing}
          <div class="flex items-center gap-2">
            <span class="text-sm font-mono font-bold" style="color:{wish ? 'var(--ws-accent)' : 'var(--ws-muted)'}">
              {wish ? wish.toFixed(2) + ' €' : '–'}
            </span>
            <button
              onclick={() => onwishedit(true)}
              class="text-xs px-2 py-0.5 rounded-lg border"
              style="border-color:var(--ws-border);color:var(--ws-muted)">✏️ {$t('radarSet')}</button>
          </div>
        {/if}
      </div>
      {#if wishData?.editing}
        <div class="flex items-center gap-1 mt-1.5">
          <input
            type="number"
            bind:value={wishData.value}
            min="0" step="1"
            placeholder="Zielpreis in €"
            class="flex-1 min-w-0 px-2 py-1 rounded-lg border text-xs font-mono"
            style={inputStyle}
            onkeydown={(e) => e.key === 'Enter' && onwishsave(wishData.value)}
          />
          <button
            onclick={() => onwishsave(wishData.value)}
            disabled={wishData?.saving}
            class="px-2 py-1 rounded-lg text-xs font-semibold shrink-0"
            style="background:var(--ws-accent);color:#fff">✓</button>
          <button
            onclick={() => onwishedit(false)}
            class="px-2 py-1 rounded-lg text-xs shrink-0"
            style="background:var(--ws-surface2);color:var(--ws-muted)">✕</button>
        </div>
      {/if}
    </div>

    <!-- ── Link to Trip ──────────────────────────────────────────────────────── -->
    <div class="relative">
      {#if linkedTrip}
        <!-- Linked badge + unlink -->
        <div class="flex items-center gap-2 px-3 py-1.5 rounded-xl border"
          style="background:color-mix(in srgb,var(--ws-accent) 8%,var(--ws-surface2));border-color:color-mix(in srgb,var(--ws-accent) 30%,var(--ws-border))">
          <span class="text-xs">🔗</span>
          <span class="text-xs font-semibold flex-1 truncate" style="color:var(--ws-text)">
            {linkedTrip.title || linkedTrip.destination || 'Trip #' + linkedTrip.id}
          </span>
          <button onclick={() => onlinktrip(tr, null)}
            class="text-[10px] hover:opacity-70 shrink-0"
            style="color:var(--ws-muted)">✕</button>
        </div>
      {:else}
        <!-- Link dropdown trigger -->
        <div class="relative">
          <button
            onclick={() => linkDropdownOpen = !linkDropdownOpen}
            class="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-medium transition-all hover:opacity-80"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">
            🔗 {$t('trackerLinkTrip') || 'Zu Reise hinzufügen'} {linkDropdownOpen ? '▴' : '▾'}
          </button>
          {#if linkDropdownOpen && wsTrips.length > 0}
            <div class="absolute bottom-full mb-1 left-0 right-0 rounded-xl border shadow-xl overflow-hidden z-20"
              style="background:var(--ws-surface);border-color:var(--ws-border)">
              {#each wsTrips as trip}
                <button
                  onclick={() => { onlinktrip(tr, trip.id); linkDropdownOpen = false; }}
                  class="w-full flex items-center gap-2 px-3 py-2 text-xs text-left transition-all hover:opacity-80"
                  style="color:var(--ws-text);border-bottom:1px solid var(--ws-border)">
                  <span class="shrink-0">✈️</span>
                  <span class="flex-1 truncate font-medium">{trip.title || trip.destination || 'Trip #' + trip.id}</span>
                  {#if trip.start_date}
                    <span class="shrink-0 font-mono" style="color:var(--ws-muted)">{fmtDate(trip.start_date)}</span>
                  {/if}
                </button>
              {/each}
            </div>
          {:else if linkDropdownOpen && wsTrips.length === 0}
            <div class="absolute bottom-full mb-1 left-0 right-0 rounded-xl border shadow-xl p-3 text-xs text-center z-20"
              style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-muted)">
              {$t('trackerNoTrips') || 'Keine aktiven Reisen'}
            </div>
          {/if}
        </div>
      {/if}
    </div>

    <!-- Action buttons -->
    <div class="flex items-center gap-2 mt-auto pt-1">
      <button
        onclick={ontogglerchart}
        class="px-3 py-1.5 rounded-xl text-xs border transition-colors"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">
        {chartData?.open ? '▲' : '📉'} {$t('radarPriceHistory')}
      </button>
      <button
        onclick={onscrape}
        class="px-3 py-1.5 rounded-xl text-xs border transition-colors"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">
        ⟳
      </button>
      <button
        onclick={ondelete}
        class="ml-auto px-3 py-1.5 rounded-xl text-xs border transition-colors hover:border-red-400 hover:text-red-400"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">
        ✕
      </button>
    </div>

    <!-- Price history accordion -->
    {#if chartData?.open}
      <div class="pt-3 border-t" style="border-color:var(--ws-border)">
        {#if chartData?.loading}
          <div class="h-24 rounded animate-pulse" style="background:var(--ws-border)"></div>
        {:else if (chartData?.history?.length || 0) < 2}
          <p class="text-xs text-center py-4" style="color:var(--ws-muted)">{$t('radarTooFewData')}</p>
        {:else}
          {#each [chartPts(chartData.history, 290, 70, 5)] as cp}
            <div class="relative h-24">
              <svg viewBox="0 0 300 80" class="w-full h-full" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="cg-{tr._type}-{tr.id}" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%"   stop-color="var(--ws-accent)" stop-opacity="0.25"/>
                    <stop offset="100%" stop-color="var(--ws-accent)" stop-opacity="0"/>
                  </linearGradient>
                </defs>
                <line x1="0" y1="5" x2="300" y2="5" stroke="var(--ws-border)" stroke-width="0.5" stroke-dasharray="4,4"/>
                <line x1="0" y1="75" x2="300" y2="75" stroke="var(--ws-green)" stroke-width="0.5" stroke-dasharray="4,4" opacity="0.5"/>
                <polygon fill="url(#cg-{tr._type}-{tr.id})" points={cp.area}/>
                <polyline fill="none" stroke="var(--ws-accent)" stroke-width="2" stroke-linejoin="round" points={cp.polyline}/>
                <circle cx={cp.minPt.x} cy={cp.minPt.y} r="3" fill="var(--ws-green)" opacity="0.9"/>
                <circle cx={cp.maxPt.x} cy={cp.maxPt.y} r="3" fill="#ef4444" opacity="0.6"/>
              </svg>
              <div class="absolute top-0 right-0 text-[10px] font-mono" style="color:var(--ws-muted)">{cp.maxP.toFixed(0)}€</div>
              <div class="absolute bottom-0 right-0 text-[10px] font-mono" style="color:var(--ws-green)">{cp.minP.toFixed(0)}€ ↓min</div>
              <div class="absolute bottom-0 left-0 text-xs" style="color:var(--ws-muted)">
                {fmtDate(chartData.history[0].fetched_at.slice(0, 10))}
              </div>
            </div>
          {/each}
        {/if}
      </div>
    {/if}

  </div>
</div>

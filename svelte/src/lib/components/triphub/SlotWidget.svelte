<script>
  /**
   * SlotWidget.svelte
   * Smart action slots: empty / tracking / booked states.
   * Visible in planning phase only.
   */
  import { t } from '$lib/i18n.js';
  import { api } from '$lib/api.js';
  import { chartPts } from '$lib/components/priceradar/helpers.js';

  let {
    trip          = null,
    slots         = {},
    phase         = 'planning',
    onopenBook    = () => {},
    onunbook      = () => {},
    ongosearch    = () => {},
  } = $props();

  // Helper: tracker display name
  function trackerLabel(tr) {
    if (!tr) return '';
    if (tr._type === 'flight' || tr._type === 'google_flight') {
      const o = tr.origin      || '';
      const d = tr.destination || '';
      return o && d ? `${o} → ${d}` : (d || o || 'Flug');
    }
    if (tr._type === 'hotel')   return tr.destination || tr.hotel_name   || 'Hotel';
    if (tr._type === 'camping') return tr.region      || tr.campsite_name || 'Camping';
    return 'Tracker';
  }

  // Price chart per slot
  let chartOpen  = $state({ flight: false, hotel: false });
  let chartHist  = $state({ flight: [],    hotel: []    });
  let chartLoad  = $state({ flight: false, hotel: false });

  async function toggleChart(slotKey, trackerType, trackerId) {
    if (chartLoad[slotKey]) return;
    chartOpen = { ...chartOpen, [slotKey]: !chartOpen[slotKey] };
    if (chartOpen[slotKey] && chartHist[slotKey].length === 0) {
      chartLoad = { ...chartLoad, [slotKey]: true };
      try {
        const res = await api(`/api/prices/history/${trackerType}/${trackerId}`);
        chartHist = { ...chartHist, [slotKey]: res.history || [] };
      } catch { chartHist = { ...chartHist, [slotKey]: [] }; }
      chartLoad = { ...chartLoad, [slotKey]: false };
    }
  }

  function trackerDates(tr) {
    if (!tr) return '';
    const from = tr.outbound_date || tr.checkin_date  || tr.start_date || '';
    const to   = tr.return_date   || tr.checkout_date || tr.end_date   || '';
    if (!from) return '';
    return to && to !== from ? `${from} → ${to}` : from;
  }
</script>

{#if phase === 'planning'}
  <div class="grid grid-cols-2 gap-3">
    {#each [
      { key: 'flight', icon: '✈️', emptyLabel: $t('hubSlotFlightEmpty'), type: 'flight' },
      { key: 'hotel',  icon: '🏨', emptyLabel: $t('hubSlotHotelEmpty'),  type: 'hotel'  },
    ] as slot}
      {@const tracker     = slots[slot.key] || (slot.key === 'hotel' ? slots.camping : null)}
      {@const isBooked    = tracker?.is_booked}
      {@const trackerType = tracker?._type || slot.type}
      {@const isCarSlot   = slot.key === 'flight' && trip?.travel_mode === 'car' && !tracker}
      {@const hasPrice    = !!tracker?.latest_snapshot?.total_price}

      <div class="rounded-2xl border overflow-hidden transition-all {isCarSlot ? 'opacity-40 grayscale' : ''}"
        style="border-color:{isBooked ? 'var(--ws-green,#2d6a4f)' : tracker ? 'var(--ws-accent)' : 'var(--ws-border)'};background:var(--ws-surface2);{isBooked ? 'box-shadow:0 0 0 2px rgba(22,163,74,.15)' : tracker && !isBooked ? 'box-shadow:0 0 0 1px color-mix(in srgb,var(--ws-accent) 30%,transparent)' : ''}">

        <!-- ── State A: empty ── -->
        {#if !tracker}
          <button onclick={() => ongosearch(slot.type)}
            class="w-full flex flex-col items-center gap-2 p-5 transition-all hover:opacity-85 active:scale-[.98]">
            <span class="text-3xl">{slot.icon}</span>
            <span class="text-sm font-semibold text-center" style="color:var(--ws-text)">{slot.emptyLabel}</span>
            {#if trip?.start_date}
              <span class="text-[10px] px-2 py-0.5 rounded-full font-medium"
                style="background:color-mix(in srgb,var(--ws-accent) 12%,var(--ws-surface));color:var(--ws-accent)">
                {$t('hubSearchHint')}
              </span>
            {/if}
            <span class="text-xs" style="color:var(--ws-muted)">PriceRadar →</span>
          </button>

        <!-- ── State B: booked ── -->
        {:else if isBooked}
          <div class="p-4 space-y-2">
            <div class="flex items-center gap-2">
              <span class="text-xl">{slot.icon}</span>
              <span class="text-xs font-bold px-2 py-0.5 rounded-full"
                style="background:rgba(22,163,74,.15);color:var(--ws-green,#2d6a4f)">
                {$t('hubSlotBooked')}
              </span>
            </div>
            <div class="text-xs font-semibold truncate" style="color:var(--ws-muted)">{trackerLabel(tracker)}</div>
            <div class="text-xl font-bold font-mono" style="color:var(--ws-text)">
              {parseFloat(tracker.booked_price).toFixed(2)} €
            </div>
            {#if tracker.booking_url}
              <a href={tracker.booking_url} target="_blank" rel="noopener noreferrer"
                class="block text-center text-xs font-bold px-3 py-1.5 rounded-lg transition-opacity hover:opacity-80"
                style="background:var(--ws-accent);color:#fff5ec;text-decoration:none">
                {$t('hubSlotBook')} ↗
              </a>
            {/if}
            <button onclick={() => onunbook(tracker.id, trackerType)}
              class="text-[10px] w-full text-center hover:opacity-70 pt-1"
              style="color:var(--ws-muted)">↩ zurücksetzen</button>
          </div>

        <!-- ── State C: tracking (with or without price) ── -->
        {:else}
          <div class="p-4 space-y-3">
            <!-- Header row -->
            <div class="flex items-start justify-between gap-2">
              <div class="flex items-center gap-2">
                <span class="text-xl shrink-0">{slot.icon}</span>
                <div class="min-w-0">
                  <div class="text-xs font-semibold truncate" style="color:var(--ws-text)">
                    {trackerLabel(tracker)}
                  </div>
                  {#if trackerDates(tracker)}
                    <div class="text-[10px]" style="color:var(--ws-muted)">{trackerDates(tracker)}</div>
                  {/if}
                </div>
              </div>
              <span class="text-[10px] font-semibold px-2 py-0.5 rounded-full shrink-0 mt-0.5"
                style="background:color-mix(in srgb,var(--ws-accent) 12%,var(--ws-surface));color:var(--ws-accent)">
                {$t('hubSlotTracking')}
              </span>
            </div>

            <!-- Price (if available) -->
            {#if hasPrice}
              <div class="rounded-xl px-3 py-2" style="background:var(--ws-surface)">
                <div class="text-[10px] uppercase tracking-wide font-semibold" style="color:var(--ws-muted)">
                  {$t('hubSlotCurrentPrice')}
                </div>
                <div class="text-xl font-bold font-mono mt-0.5" style="color:var(--ws-text)">
                  {parseFloat(tracker.latest_snapshot.total_price).toFixed(2)} €
                </div>
              </div>
            {:else}
              <!-- No price yet — explain why -->
              <div class="rounded-xl px-3 py-2 text-center" style="background:var(--ws-surface)">
                <span class="text-xs" style="color:var(--ws-muted)">Preis wird beim nächsten Scan aktualisiert</span>
              </div>
            {/if}

            <!-- CTAs -->
            <div class="flex gap-2">
              {#if tracker.booking_url}
                <a href={tracker.booking_url} target="_blank" rel="noopener noreferrer"
                  class="flex-1 text-center text-xs font-bold px-2 py-2 rounded-lg transition-opacity hover:opacity-80"
                  style="background:var(--ws-accent);color:#fff5ec;text-decoration:none">
                  {$t('hubSlotBook')} ↗
                </a>
              {/if}
              <button onclick={() => onopenBook(tracker.id, trackerType, slot.key)}
                class="flex-1 text-xs font-semibold px-2 py-2 rounded-lg border transition-all hover:opacity-80"
                style="border-color:var(--ws-green,#2d6a4f);color:var(--ws-green,#2d6a4f)">
                {$t('hubSlotMarkBooked')}
              </button>
            </div>

            <!-- Price history accordion -->
            <button
              onclick={() => toggleChart(slot.key, trackerType, tracker.id)}
              class="w-full text-left text-xs px-2 py-1.5 rounded-lg flex items-center gap-1.5 hover:opacity-80 transition-opacity"
              style="color:var(--ws-muted)">
              <span>{chartOpen[slot.key] ? '▲' : '📉'}</span>
              <span>{chartOpen[slot.key] ? 'Verlauf ausblenden' : 'Preisverlauf'}</span>
              {#if chartLoad[slot.key]}
                <span class="ml-auto text-[10px]">⏳</span>
              {/if}
            </button>

            {#if chartOpen[slot.key]}
              <div class="pt-1 border-t" style="border-color:var(--ws-border)">
                {#if chartLoad[slot.key]}
                  <div class="h-16 rounded animate-pulse" style="background:var(--ws-border)"></div>
                {:else if chartHist[slot.key].length < 2}
                  <p class="text-[10px] text-center py-3" style="color:var(--ws-muted)">Noch zu wenig Daten</p>
                {:else}
                  {#each [chartPts(chartHist[slot.key], 260, 60, 4)] as cp}
                    <div class="relative" style="height:70px">
                      <svg viewBox="0 0 270 70" class="w-full h-full" preserveAspectRatio="none">
                        <defs>
                          <linearGradient id="sg-{slot.key}" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%"   stop-color="var(--ws-accent)" stop-opacity="0.2"/>
                            <stop offset="100%" stop-color="var(--ws-accent)" stop-opacity="0"/>
                          </linearGradient>
                        </defs>
                        <polygon fill="url(#sg-{slot.key})" points={cp.area}/>
                        <polyline fill="none" stroke="var(--ws-accent)" stroke-width="1.5"
                          stroke-linejoin="round" points={cp.polyline}/>
                        <circle cx={cp.minPt.x} cy={cp.minPt.y} r="2.5" fill="var(--ws-green)"/>
                        <circle cx={cp.maxPt.x} cy={cp.maxPt.y} r="2.5" fill="#ef4444" opacity="0.7"/>
                      </svg>
                      <div class="absolute top-0 right-0 text-[9px] font-mono" style="color:#ef4444">{cp.maxP.toFixed(0)}€</div>
                      <div class="absolute bottom-0 right-0 text-[9px] font-mono" style="color:var(--ws-green)">{cp.minP.toFixed(0)}€</div>
                    </div>
                  {/each}
                {/if}
              </div>
            {/if}
          </div>
        {/if}
      </div>
    {/each}
  </div>
{/if}

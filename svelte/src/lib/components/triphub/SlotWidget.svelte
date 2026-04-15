<script>
  /**
   * SlotWidget.svelte
   * Smart action slots: empty / tracking / booked states.
   * Visible in planning phase only.
   */
  import { t } from '$lib/i18n.js';

  let {
    trip          = null,
    slots         = {},
    phase         = 'planning',
    onopenBook    = () => {},  // (trackerId, trackerType, slotKey)
    onunbook      = () => {},  // (trackerId, trackerType)
    ongosearch    = () => {},  // (type)
  } = $props();
</script>

{#if phase === 'planning'}
  <div class="grid grid-cols-2 gap-3">
    {#each [
      { key: 'flight', icon: '✈️', emptyLabel: $t('hubSlotFlightEmpty'), type: 'flight' },
      { key: 'hotel',  icon: '🏨', emptyLabel: $t('hubSlotHotelEmpty'),  type: 'hotel'  },
    ] as slot}
      {@const tracker     = slots[slot.key] || slots.camping}
      {@const isBooked    = tracker?.is_booked}
      {@const trackerType = tracker?._type || slot.type}
      {@const isCarSlot   = slot.key === 'flight' && trip?.travel_mode === 'car'}

      <div class="rounded-2xl border overflow-hidden transition-all {isCarSlot ? 'opacity-40 grayscale' : ''}"
        style="border-color:{isBooked ? 'var(--ws-green,#2d6a4f)' : 'var(--ws-border)'};background:var(--ws-surface2);{isBooked ? 'box-shadow:0 0 0 2px rgba(22,163,74,.15)' : ''}">

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

        {:else if isBooked}
          <div class="p-4 space-y-2">
            <div class="flex items-center gap-2">
              <span class="text-xl">{slot.icon}</span>
              <span class="text-xs font-bold px-2 py-0.5 rounded-full"
                style="background:rgba(22,163,74,.15);color:var(--ws-green,#2d6a4f)">{$t('hubSlotBooked')}</span>
            </div>
            <div class="text-lg font-bold font-mono" style="color:var(--ws-text)">{parseFloat(tracker.booked_price).toFixed(2)} €</div>
            {#if tracker.booking_url}
              <a href={tracker.booking_url} target="_blank" rel="noopener noreferrer"
                class="block text-center text-xs font-bold px-3 py-1.5 rounded-lg transition-opacity hover:opacity-80"
                style="background:var(--ws-accent);color:#fff5ec;text-decoration:none">{$t('hubSlotBook')}</a>
            {/if}
            <button onclick={() => onunbook(tracker.id, trackerType)}
              class="text-[10px] w-full text-center hover:opacity-70" style="color:var(--ws-muted)">↩ zurücksetzen</button>
          </div>

        {:else}
          <div class="p-4 space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xl">{slot.icon}</span>
              <span class="text-[10px] font-semibold px-2 py-0.5 rounded-full"
                style="background:color-mix(in srgb,var(--ws-accent) 12%,var(--ws-surface));color:var(--ws-accent)">{$t('hubSlotTracking')}</span>
            </div>
            {#if tracker.latest_snapshot?.total_price}
              <div>
                <div class="text-xs" style="color:var(--ws-muted)">{$t('hubSlotCurrentPrice')}</div>
                <div class="text-lg font-bold font-mono" style="color:var(--ws-text)">{parseFloat(tracker.latest_snapshot.total_price).toFixed(2)} €</div>
              </div>
            {/if}
            <div class="flex gap-2">
              {#if tracker.booking_url}
                <a href={tracker.booking_url} target="_blank" rel="noopener noreferrer"
                  class="flex-1 text-center text-xs font-bold px-2 py-1.5 rounded-lg transition-opacity hover:opacity-80"
                  style="background:var(--ws-accent);color:#fff5ec;text-decoration:none">{$t('hubSlotBook')}</a>
              {/if}
              <button onclick={() => onopenBook(tracker.id, trackerType, slot.key)}
                class="flex-1 text-xs font-semibold px-2 py-1.5 rounded-lg border transition-all hover:opacity-80"
                style="border-color:var(--ws-green,#2d6a4f);color:var(--ws-green,#2d6a4f)">{$t('hubSlotMarkBooked')}</button>
            </div>
          </div>
        {/if}
      </div>
    {/each}
  </div>
{/if}

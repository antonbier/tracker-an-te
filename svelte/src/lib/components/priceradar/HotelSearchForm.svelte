<script>
  import { t } from '$lib/i18n.js';
  import { DESTINATIONS, inputCls, inputStyle, labelCls } from './constants.js';
  import { dateOffset } from './helpers.js';

  const { searching, onsearch } = $props();

  let htCity     = $state('');
  let htIn       = $state(dateOffset(30));
  let htOut      = $state(dateOffset(37));
  let htAdults   = $state(2);
  let htChildren = $state(0);
  let htRooms    = $state(1);
  let acState    = $state({});

  function acFilter(key, value) {
    if (!value || value.length < 1) { acState = { ...acState, [key]: { open: false, items: [] } }; return; }
    const q = value.toLowerCase();
    const items = DESTINATIONS.filter(d => d.toLowerCase().includes(q)).slice(0, 8);
    acState = { ...acState, [key]: { open: items.length > 0, items } };
  }
  function acSelect(key, dest, setter) {
    setter(dest);
    acState = { ...acState, [key]: { open: false, items: [] } };
  }
  function acClose(key) {
    setTimeout(() => { acState = { ...acState, [key]: { open: false, items: [] } }; }, 150);
  }

  function handleSearch() {
    onsearch({
      destination:   htCity,
      checkin_date:  htIn,
      checkout_date: htOut,
      adults:        htAdults,
      children:      htChildren,
      rooms:         htRooms,
    });
  }
</script>

<div class="rounded-xl p-4 border space-y-4" style="background:var(--ws-surface);border-color:var(--ws-border)">
  <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">🏨 {$t('radarHotels')}</h2>

  <!-- City autocomplete -->
  <div class="relative">
    <label class="{labelCls}" style="color:var(--ws-muted)">{$t('radarCity')}</label>
    <input bind:value={htCity} placeholder="z.B. Barcelona, Wien, Kreta…"
      class="{inputCls}" style={inputStyle}
      oninput={() => acFilter('htCity', htCity)}
      onblur={() => acClose('htCity')}/>
    {#if acState.htCity?.open}
      <div class="absolute z-50 left-0 right-0 top-full mt-1 rounded-xl border shadow-lg overflow-hidden" style="background:var(--ws-surface);border-color:var(--ws-border)">
        {#each acState.htCity.items as dest}
          <button class="w-full text-left px-3 py-2 text-xs hover:bg-[var(--ws-surface2)]"
            style="color:var(--ws-text)"
            onmousedown={() => acSelect('htCity', dest, v => htCity = v)}>
            {dest}
          </button>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Dates -->
  <div class="grid grid-cols-2 gap-3">
    <div>
      <label class="{labelCls}" style="color:var(--ws-muted)">{$t('radarCheckin')}</label>
      <input type="date" bind:value={htIn} class="{inputCls}" style={inputStyle}/>
    </div>
    <div>
      <label class="{labelCls}" style="color:var(--ws-muted)">{$t('radarCheckout')}</label>
      <input type="date" bind:value={htOut} class="{inputCls}" style={inputStyle}/>
    </div>
  </div>

  <!-- Personen-Split Erw./Kinder + Zimmer -->
  <div class="grid grid-cols-3 gap-2">
    {#each [
      [() => htAdults,   v => htAdults   = v, 1, 9, $t('radarAdults'),      null],
      [() => htChildren, v => htChildren = v, 0, 8, $t('radarChildren'),    null],
      [() => htRooms,    v => htRooms    = v, 1, 4, $t('radarRoomsLabel'),  null],
    ] as [getter, setter, min, max, label]}
      <div class="rounded-xl border p-2.5 flex flex-col items-center gap-1.5"
        style="background:var(--ws-surface2);border-color:var(--ws-border)">
        <div class="text-[10px] font-semibold" style="color:var(--ws-muted)">{label}</div>
        <div class="flex items-center gap-1.5">
          <button onclick={() => setter(Math.max(min, getter()-1))}
            class="w-6 h-6 rounded-lg border text-sm font-bold flex items-center justify-center"
            style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">−</button>
          <span class="text-sm font-bold w-4 text-center" style="color:var(--ws-text)">{getter()}</span>
          <button onclick={() => setter(Math.min(max, getter()+1))}
            class="w-6 h-6 rounded-lg border text-sm font-bold flex items-center justify-center"
            style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
        </div>
      </div>
    {/each}
  </div>

  <button
    onclick={handleSearch}
    disabled={searching || !htCity || !htIn || !htOut}
    class="w-full py-2.5 rounded-xl font-semibold text-sm hover:opacity-80 disabled:opacity-50"
    style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
    {searching ? $t('radarSearching') : '🔍 ' + $t('radarSearch')}
  </button>
</div>

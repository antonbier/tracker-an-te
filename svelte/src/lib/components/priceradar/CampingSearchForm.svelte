<script>
  import { t } from '$lib/i18n.js';
  import { DESTINATIONS, inputCls, inputStyle, labelCls } from './constants.js';
  import { dateOffset } from './helpers.js';

  const { searching, onsearch } = $props();

  let cpRegion     = $state('');
  let cpIn         = $state(dateOffset(30));
  let cpOut        = $state(dateOffset(37));
  let cpAdults     = $state(2);
  let cpChildren   = $state(0);
  let cpAccomType  = $state('mobilheim');
  let cpAccomOptions = $state([
    { value: 'mobilheim',         label: 'Mobilheim (Standard)' },
    { value: 'mobilheim-premium', label: 'Mobilheim (Premium)' },
    { value: 'glamping',          label: 'Glamping' },
    { value: 'stellplatz',        label: 'Stellplatz' },
  ]);
  let cpBedrooms   = $state('1');
  let cpAircon     = $state(false);
  let cpPets       = $state(false);
  let cpTerrace    = $state(false);
  let cpFinalClean = $state(false);
  let acState      = $state({});

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
      destination:        cpRegion,
      checkin_date:       cpIn,
      checkout_date:      cpOut,
      adults:             cpAdults,
      children:           cpChildren,
      accommodation_type: cpAccomType,
      bedrooms:           cpBedrooms,
      aircon:             cpAircon,
      pets:               cpPets,
      covered_terrace:    cpTerrace,
      final_cleaning:     cpFinalClean,
    });
  }
</script>

<div class="rounded-xl p-4 border space-y-4" style="background:var(--ws-surface);border-color:var(--ws-border)">
  <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">⛺ {$t('radarCamping')}</h2>

  <!-- Region autocomplete -->
  <div class="relative">
    <label class="{labelCls}" style="color:var(--ws-muted)">{$t('radarRegionOrPlace')}</label>
    <input bind:value={cpRegion} placeholder="z.B. Côte d'Azur, Toskana, Kroatien…"
      class="{inputCls}" style={inputStyle}
      oninput={() => acFilter('cpRegion', cpRegion)}
      onblur={() => acClose('cpRegion')}/>
    {#if acState.cpRegion?.open}
      <div class="absolute z-50 left-0 right-0 top-full mt-1 rounded-xl border shadow-lg overflow-hidden" style="background:var(--ws-surface);border-color:var(--ws-border)">
        {#each acState.cpRegion.items as dest}
          <button class="w-full text-left px-3 py-2 text-xs hover:bg-[var(--ws-surface2)]"
            style="color:var(--ws-text)"
            onmousedown={() => acSelect('cpRegion', dest, v => cpRegion = v)}>
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
      <input type="date" bind:value={cpIn} class="{inputCls}" style={inputStyle}/>
    </div>
    <div>
      <label class="{labelCls}" style="color:var(--ws-muted)">{$t('radarCheckout')}</label>
      <input type="date" bind:value={cpOut} class="{inputCls}" style={inputStyle}/>
    </div>
  </div>

  <!-- Personen-Split Erw./Kinder -->
  <div>
    <label class="{labelCls}" style="color:var(--ws-muted)">👥 {$t('radarPassengers')}</label>
    <div class="grid grid-cols-2 gap-2 mt-1">
      <div class="rounded-xl border p-2.5 flex items-center justify-between"
        style="background:var(--ws-surface2);border-color:var(--ws-border)">
        <div class="text-xs font-semibold" style="color:var(--ws-text)">{$t('radarAdults')}</div>
        <div class="flex items-center gap-2">
          <button onclick={() => cpAdults = Math.max(1, cpAdults-1)}
            class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center"
            style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">−</button>
          <span class="w-5 text-center text-sm font-bold" style="color:var(--ws-text)">{cpAdults}</span>
          <button onclick={() => cpAdults = Math.min(9, cpAdults+1)}
            class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center"
            style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
        </div>
      </div>
      <div class="rounded-xl border p-2.5 flex items-center justify-between"
        style="background:var(--ws-surface2);border-color:var(--ws-border)">
        <div>
          <div class="text-xs font-semibold" style="color:var(--ws-text)">{$t('radarChildren')}</div>
          <div class="text-[10px]" style="color:var(--ws-muted)">bis 17 J.</div>
        </div>
        <div class="flex items-center gap-2">
          <button onclick={() => cpChildren = Math.max(0, cpChildren-1)}
            class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center"
            style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">−</button>
          <span class="w-5 text-center text-sm font-bold" style="color:var(--ws-text)">{cpChildren}</span>
          <button onclick={() => cpChildren = Math.min(8, cpChildren+1)}
            class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center"
            style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Accommodation type -->
  <div>
    <label class="{labelCls}" style="color:var(--ws-muted)">{$t('radarAccomType')}</label>
    <select bind:value={cpAccomType} class="{inputCls}" style={inputStyle}>
      {#each cpAccomOptions as opt}
        <option value={opt.value}>{opt.label}</option>
      {/each}
    </select>
  </div>

  <!-- Bedrooms -->
  <div>
    <label class="{labelCls}" style="color:var(--ws-muted)">{$t('radarBedrooms')}</label>
    <select bind:value={cpBedrooms} class="{inputCls}" style={inputStyle}>
      <option value="1">1 Schlafzimmer</option>
      <option value="2">2 Schlafzimmer</option>
      <option value="3">3+ Schlafzimmer</option>
    </select>
  </div>

  <!-- Extras checkboxes -->
  <div>
    <label class="{labelCls}" style="color:var(--ws-muted)">{$t('radarExtras')}</label>
    <div class="mt-1.5 space-y-2">
      {#each [
        [() => cpAircon,     v => cpAircon     = v, 'radarAircon'],
        [() => cpPets,       v => cpPets       = v, 'radarPetsAllowed'],
        [() => cpTerrace,    v => cpTerrace    = v, 'radarCoveredTerrace'],
        [() => cpFinalClean, v => cpFinalClean = v, 'radarFinalCleaning'],
      ] as [getter, setter, key]}
        <button onclick={() => setter(!getter())}
          class="w-full flex items-center gap-3 px-3 py-2 rounded-xl border text-sm text-left transition-colors"
          style={getter()
            ? 'background:rgba(196,98,45,.1);border-color:var(--ws-accent);color:var(--ws-text)'
            : 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)'}>
          <span class="w-4 h-4 rounded border flex items-center justify-center text-xs shrink-0"
            style="border-color:{getter() ? 'var(--ws-accent)' : 'var(--ws-border)'}">
            {getter() ? '✓' : ''}
          </span>
          {$t(key)}
        </button>
      {/each}
    </div>
  </div>

  <button
    onclick={handleSearch}
    disabled={searching || !cpRegion || !cpIn || !cpOut}
    class="w-full py-2.5 rounded-xl font-semibold text-sm hover:opacity-80 disabled:opacity-50"
    style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec">
    {searching ? $t('radarSearching') : '🔍 ' + $t('radarSearch')}
  </button>
</div>

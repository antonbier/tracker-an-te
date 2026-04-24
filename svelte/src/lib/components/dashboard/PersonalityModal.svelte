<script>
  /**
   * PersonalityModal.svelte — Temporäre oder permanente Reisepersönlichkeit-Einstellungen
   * für die KI-Discovery-Vorschläge.
   * 
   * Logik:
   *   savePermantly=false → Settings per POST an /api/discovery/refresh (nur diese Sitzung)
   *   savePermanently=true  → PUT /api/settings/user + dann /api/discovery/refresh
   */
  import { t }    from '$lib/i18n.js';
  import { api }  from '$lib/api.js';
  import { toast } from '$lib/toast.js';
  import { apiUrl } from '$lib/stores.js';

  let { open = $bindable(false), onrefreshed } = $props();

  // ── Formular-State ───────────────────────────────────────────────────────
  let travel_style   = $state('');
  let climate_pref   = $state('');
  let landscape_pref = $state('');
  let companions     = $state('');
  let wish_text      = $state('');
  let travel_mode    = $state('flight');
  let max_travel_time = $state('any');
  let savePermanently = $state(false);
  let loading        = $state(false);

  // Beim Öffnen aktuelle Settings laden
  $effect(() => {
    if (open && $apiUrl) loadCurrentSettings();
  });

  async function loadCurrentSettings() {
    try {
      const s = await api('/api/settings/user');
      travel_style    = s.travel_style    || '';
      climate_pref    = s.climate_pref    || '';
      landscape_pref  = s.landscape_pref  || '';
      companions      = s.companions      || '';
      wish_text       = s.wish_text       || '';
      travel_mode     = s.travel_mode     || 'flight';
      max_travel_time = s.max_travel_time || 'any';
    } catch { /* Defaults ok */ }
  }

  async function apply() {
    loading = true;
    try {
      const personality = {
        travel_style:    travel_style    || null,
        climate_pref:    climate_pref    || null,
        landscape_pref:  landscape_pref  || null,
        companions:      companions      || null,
        wish_text:       wish_text       || null,
        travel_mode:     travel_mode     || null,
        max_travel_time: max_travel_time || null,
      };

      if (savePermanently) {
        // Dauerhaft in DB speichern
        await api('/api/settings/user', {
          method: 'POST',
          body: JSON.stringify(personality),
        });
        toast('✓ Einstellungen dauerhaft gespeichert', 'success');
      }

      // Vorschläge mit diesen Settings (temporär oder permanent) neu laden
      const data = await api('/api/discovery/refresh?count=3', {
        method: 'POST',
        body: JSON.stringify(savePermanently ? {} : personality),
      });

      open = false;
      onrefreshed?.(data);
    } catch (e) {
      toast(e?.message || $t('toastError') || 'Fehler', 'error');
    }
    loading = false;
  }

  const STYLES     = [{v:'',l:$t('personalityModalEgal')||'Egal'},{v:'adventure',l:'🏔️ Abenteuer'},{v:'relaxation',l:'🌅 Entspannung'},{v:'culture',l:'🏛️ Kultur'},{v:'nature',l:'🌿 Natur'},{v:'city',l:'🏙️ City-Trip'}];
  const CLIMATES   = [{v:'',l:$t('personalityModalEgal')||'Egal'},{v:'warm',l:'☀️ Warm'},{v:'mild',l:'🌤️ Mild'},{v:'cold',l:'❄️ Kalt'}];
  const LANDSCAPES = [{v:'',l:$t('personalityModalEgal')||'Egal'},{v:'mountains',l:'⛰️ Berge'},{v:'sea',l:'🏖️ Meer'},{v:'forest',l:'🌲 Wald'},{v:'city',l:'🏙️ Stadt'},{v:'mix',l:'🌍 Mix'}];
  const COMPANIONS = [{v:'',l:$t('personalityModalEgal')||'Egal'},{v:'solo',l:'🧍 Solo'},{v:'couple',l:'👫 Pärchen'},{v:'familie_kleinkinder',l:'👨‍👩‍👧 Familie (Kleinkinder)'},{v:'familie_teenager',l:'👨‍👩‍👦 Familie (Teenager)'},{v:'friends',l:'👯 Freunde'}];
  const MODES      = [{v:'flight',l:'✈️ Flug'},{v:'car',l:'🚗 Auto'}];
  const TIMES      = [{v:'any',l:$t('personalityModalEgal')||'Keine Beschränkung'},{v:'2h',l:'bis 2 Stunden'},{v:'4h',l:'bis 4 Stunden'},{v:'6h',l:'bis 6 Stunden'},{v:'8h',l:'bis 8 Stunden'},{v:'12h',l:'bis 12 Stunden'}];

  const sel = 'w-full px-3 py-2 rounded-xl border text-sm focus:outline-none';
  const selSt = 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)';
</script>

{#if open}
<div class="fixed inset-0 z-50 flex items-end sm:items-center justify-center"
  style="background:rgba(0,0,0,.55);backdrop-filter:blur(4px)"
  role="dialog" aria-modal="true">
  <div class="w-full max-w-md mx-4 mb-4 sm:mb-0 rounded-2xl border shadow-2xl overflow-hidden"
    style="background:var(--ws-surface);border-color:var(--ws-border);max-height:90vh;overflow-y:auto">

    <!-- Header -->
    <div class="px-5 py-4 border-b flex items-center justify-between"
      style="border-color:var(--ws-border)">
      <div>
        <h3 class="font-bold text-base" style="color:var(--ws-text)">
          🧭 {$t('personalityModalTitle')}
        </h3>
        <p class="text-xs mt-0.5" style="color:var(--ws-muted)">
          {$t('personalityModalSubtitle')}
        </p>
      </div>
      <button onclick={() => open = false}
        class="text-lg leading-none hover:opacity-60 transition-opacity"
        style="color:var(--ws-muted)">✕</button>
    </div>

    <!-- Form -->
    <div class="p-5 space-y-4">

      <!-- Reisestil -->
      <div>
        <label class="block text-xs font-bold uppercase tracking-wider mb-1"
          style="color:var(--ws-muted)">{$t('defaultsTravelStyle')}</label>
        <select bind:value={travel_style} class={sel} style={selSt}>
          {#each STYLES as o}<option value={o.v}>{o.l}</option>{/each}
        </select>
      </div>

      <!-- Klima + Landschaft -->
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider mb-1"
            style="color:var(--ws-muted)">{$t('defaultsClimate')}</label>
          <select bind:value={climate_pref} class={sel} style={selSt}>
            {#each CLIMATES as o}<option value={o.v}>{o.l}</option>{/each}
          </select>
        </div>
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider mb-1"
            style="color:var(--ws-muted)">{$t('defaultsLandscape')}</label>
          <select bind:value={landscape_pref} class={sel} style={selSt}>
            {#each LANDSCAPES as o}<option value={o.v}>{o.l}</option>{/each}
          </select>
        </div>
      </div>

      <!-- Begleitung -->
      <div>
        <label class="block text-xs font-bold uppercase tracking-wider mb-1"
          style="color:var(--ws-muted)">{$t('defaultsCompanions')}</label>
        <select bind:value={companions} class={sel} style={selSt}>
          {#each COMPANIONS as o}<option value={o.v}>{o.l}</option>{/each}
        </select>
      </div>

      <!-- Reisemodus + Zeit -->
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider mb-1"
            style="color:var(--ws-muted)">{$t('defaultsTravelMode')}</label>
          <select bind:value={travel_mode} class={sel} style={selSt}>
            {#each MODES as o}<option value={o.v}>{o.l}</option>{/each}
          </select>
        </div>
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider mb-1"
            style="color:var(--ws-muted)">
            {travel_mode === 'car' ? $t('wwMaxTravelTimeCar') : $t('wwMaxTravelTime')}
          </label>
          <select bind:value={max_travel_time} class={sel} style={selSt}>
            {#each TIMES as o}<option value={o.v}>{o.l}</option>{/each}
          </select>
        </div>
      </div>

      <!-- Wunsch-Freitext -->
      <div>
        <label class="block text-xs font-bold uppercase tracking-wider mb-1"
          style="color:var(--ws-muted)">{$t('personalityModalFreitext')}</label>
        <textarea bind:value={wish_text} rows="2"
          placeholder={$t('personalityModalFreitextPh')||'z.B. Strände mit türkisem Wasser…'}
          class="w-full px-3 py-2 rounded-xl border text-sm focus:outline-none resize-none"
          style={selSt + ';font-family:inherit'}
          maxlength="500"></textarea>
        <div class="text-right text-[10px] mt-0.5" style="color:var(--ws-muted)">{(wish_text||'').length}/500</div>
      </div>

      <!-- Dauerhaft-Checkbox -->
      <label class="flex items-center gap-2.5 cursor-pointer select-none p-3 rounded-xl border"
        style="border-color:var(--ws-border);background:var(--ws-surface2)">
        <input type="checkbox" bind:checked={savePermanently}
          class="w-4 h-4 rounded accent-[var(--ws-accent)]" />
        <div>
          <div class="text-sm font-semibold" style="color:var(--ws-text)">
            {$t('personalityModalSavePerm')}
          </div>
          <div class="text-xs" style="color:var(--ws-muted)">
            {$t('personalityModalSaveHint')}
          </div>
        </div>
      </label>
    </div>

    <!-- Footer -->
    <div class="px-5 py-4 border-t flex gap-3" style="border-color:var(--ws-border)">
      <button onclick={() => open = false}
        class="flex-1 py-2.5 rounded-xl border text-sm font-semibold hover:opacity-70"
        style="border-color:var(--ws-border);color:var(--ws-muted)">
        {$t('personalityModalCancel')}
      </button>
      <button onclick={apply} disabled={loading}
        class="flex-1 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-40 flex items-center justify-center gap-1.5"
        style="background:var(--ws-accent);color:#fff5ec">
        {#if loading}
          <span class="animate-spin">⏳</span> {$t('personalityModalLoading')}
        {:else}
          🤖 {$t('personalityModalGenerate')}
        {/if}
      </button>
    </div>

  </div>
</div>
{/if}

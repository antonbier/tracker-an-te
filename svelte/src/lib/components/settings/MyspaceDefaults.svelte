<script>
  import { t } from '$lib/i18n.js';
  import AIRPORTS from '$lib/data/airports.json';

  const inputCls   = 'w-full px-3 py-2 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ws-accent)]';
  const inputStyle = 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)';
  const labelCls   = 'block text-xs font-bold uppercase tracking-wider mb-1';

  let {
    defAdults     = $bindable(),
    defChildren   = $bindable(),
    homeAirport   = $bindable(),
    lugS10        = $bindable(),
    lugS20        = $bindable(),
    lugS23        = $bindable(),
    lugL10        = $bindable(),
    lugL20        = $bindable(),
    lugL23        = $bindable(),
    fDepMin       = $bindable(),
    fDepMax       = $bindable(),
    fArrMin       = $bindable(),
    fArrMax       = $bindable(),
    travelStyle   = $bindable(),
    climatePref   = $bindable(),
    landscapePref = $bindable(),
    companions    = $bindable(),
    wishText      = $bindable(),
    travelMode    = $bindable(),
    maxTravelTime = $bindable(),
    historyMode   = $bindable(),
  } = $props();

  // Accordion open state
  let openLogistik     = $state(true);
  let openPersoenlich  = $state(false);
</script>

<div class="space-y-3 mt-1">

  <!-- ══════════════════════════════════════════════════════════════════════ -->
  <!-- Akkordeon 1: Logistik                                                  -->
  <!-- ══════════════════════════════════════════════════════════════════════ -->
  <div class="rounded-2xl border overflow-hidden" style="border-color:var(--ws-border)">
    <button
      onclick={() => openLogistik = !openLogistik}
      class="w-full flex items-center justify-between px-4 py-3 text-left transition-opacity hover:opacity-80"
      style="background:var(--ws-surface2)">
      <div class="flex items-center gap-2">
        <span class="text-base">🧳</span>
        <span class="text-sm font-bold" style="color:var(--ws-text)">{$t('defaultsAccLogistikTitle')}</span>
        <span class="text-xs px-2 py-0.5 rounded-full" style="background:rgba(196,98,45,.1);color:var(--ws-accent)">
          {$t('defaultsAccLogistikSub')}
        </span>
      </div>
      <span class="text-xs transition-transform" style="color:var(--ws-muted);transform:{openLogistik ? 'rotate(180deg)' : 'rotate(0deg)'}">▼</span>
    </button>

    {#if openLogistik}
      <div class="px-4 py-4 space-y-5 border-t" style="border-color:var(--ws-border)">

        <!-- Reisende -->
        <div>
          <div class="text-xs font-bold uppercase tracking-wider mb-3" style="color:var(--ws-muted)">👥 {$t('defaultsTravelers')}</div>
          <div class="grid grid-cols-3 gap-3">

            <div class="rounded-xl border p-3 flex flex-col items-center gap-2"
              style="background:var(--ws-surface);border-color:var(--ws-border)">
              <div class="text-xs font-semibold" style="color:var(--ws-muted)">{$t('wwAdults')}</div>
              <div class="flex items-center gap-2">
                <button onclick={() => defAdults = Math.max(1, defAdults - 1)}
                  class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center"
                  style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)">−</button>
                <span class="text-sm font-bold w-5 text-center" style="color:var(--ws-text)">{defAdults}</span>
                <button onclick={() => defAdults = Math.min(9, defAdults + 1)}
                  class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center"
                  style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
              </div>
            </div>

            <div class="rounded-xl border p-3 flex flex-col items-center gap-2"
              style="background:var(--ws-surface);border-color:var(--ws-border)">
              <div class="text-xs font-semibold" style="color:var(--ws-muted)">{$t('wwChildren')}</div>
              <div class="flex items-center gap-2">
                <button onclick={() => defChildren = Math.max(0, defChildren - 1)}
                  class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center"
                  style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)">−</button>
                <span class="text-sm font-bold w-5 text-center" style="color:var(--ws-text)">{defChildren}</span>
                <button onclick={() => defChildren = Math.min(8, defChildren + 1)}
                  class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center"
                  style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
              </div>
            </div>

            <div class="rounded-xl border p-3 flex flex-col gap-1"
              style="background:var(--ws-surface);border-color:var(--ws-border)">
              <div class="text-xs font-semibold" style="color:var(--ws-muted)">{$t('wwHomeAirportShort')}</div>
              <input bind:value={homeAirport} maxlength="3" placeholder="BGY"
                class="w-full px-2 py-1 rounded-lg border text-sm font-mono uppercase text-center focus:outline-none focus:ring-2 focus:ring-[var(--ws-accent)]"
                style={inputStyle}/>
            </div>

          </div>
        </div>

        <hr style="border-color:var(--ws-border)"/>

        <!-- Gepäck -->
        <div>
          <div class="text-xs font-bold uppercase tracking-wider mb-3" style="color:var(--ws-muted)">🧳 {$t('defaultsLuggage')}</div>
          <div class="grid grid-cols-2 gap-4">

            <div class="rounded-xl border p-3 space-y-2" style="background:var(--ws-surface);border-color:var(--ws-border)">
              <div class="text-xs font-semibold mb-2" style="color:var(--ws-text)">⚡ {$t('wwLugShort')}</div>
              {#each [
                ['10 kg', () => lugS10, v => lugS10 = v],
                ['20 kg', () => lugS20, v => lugS20 = v],
                ['23 kg', () => lugS23, v => lugS23 = v],
              ] as [label, getter, setter]}
                <div class="flex items-center justify-between gap-2">
                  <span class="text-xs w-10 shrink-0" style="color:var(--ws-muted)">{label}</span>
                  <div class="flex items-center gap-1.5">
                    <button onclick={() => setter(Math.max(0, getter() - 1))}
                      class="w-6 h-6 rounded border text-sm font-bold flex items-center justify-center"
                      style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)">−</button>
                    <span class="w-4 text-center text-sm font-bold" style="color:{getter()>0?'var(--ws-accent)':'var(--ws-muted)'}">{getter()}</span>
                    <button onclick={() => setter(Math.min(9, getter() + 1))}
                      class="w-6 h-6 rounded border text-sm font-bold flex items-center justify-center"
                      style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
                  </div>
                </div>
              {/each}
            </div>

            <div class="rounded-xl border p-3 space-y-2" style="background:var(--ws-surface);border-color:var(--ws-border)">
              <div class="text-xs font-semibold mb-2" style="color:var(--ws-text)">🌍 {$t('wwLugLong')}</div>
              {#each [
                ['10 kg', () => lugL10, v => lugL10 = v],
                ['20 kg', () => lugL20, v => lugL20 = v],
                ['23 kg', () => lugL23, v => lugL23 = v],
              ] as [label, getter, setter]}
                <div class="flex items-center justify-between gap-2">
                  <span class="text-xs w-10 shrink-0" style="color:var(--ws-muted)">{label}</span>
                  <div class="flex items-center gap-1.5">
                    <button onclick={() => setter(Math.max(0, getter() - 1))}
                      class="w-6 h-6 rounded border text-sm font-bold flex items-center justify-center"
                      style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)">−</button>
                    <span class="w-4 text-center text-sm font-bold" style="color:{getter()>0?'var(--ws-accent)':'var(--ws-muted)'}">{getter()}</span>
                    <button onclick={() => setter(Math.min(9, getter() + 1))}
                      class="w-6 h-6 rounded border text-sm font-bold flex items-center justify-center"
                      style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
                  </div>
                </div>
              {/each}
            </div>

          </div>
        </div>

        <hr style="border-color:var(--ws-border)"/>

        <!-- Flugzeiten -->
        <div>
          <div class="text-xs font-bold uppercase tracking-wider mb-3" style="color:var(--ws-muted)">⏱️ {$t('defaultsFlightTimes')}</div>
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <div class="text-xs font-semibold" style="color:var(--ws-text)">🛫 {$t('wwDepLabel')}</div>
              <div class="grid grid-cols-2 gap-2">
                <div>
                  <label class={labelCls} style="color:var(--ws-muted)">{$t('wwTimeFrom')}</label>
                  <input type="time" bind:value={fDepMin} class={inputCls} style={inputStyle}/>
                </div>
                <div>
                  <label class={labelCls} style="color:var(--ws-muted)">{$t('wwTimeTo')}</label>
                  <input type="time" bind:value={fDepMax} class={inputCls} style={inputStyle}/>
                </div>
              </div>
            </div>
            <div class="space-y-2">
              <div class="text-xs font-semibold" style="color:var(--ws-text)">🛬 {$t('wwArrLabel')}</div>
              <div class="grid grid-cols-2 gap-2">
                <div>
                  <label class={labelCls} style="color:var(--ws-muted)">{$t('wwTimeFrom')}</label>
                  <input type="time" bind:value={fArrMin} class={inputCls} style={inputStyle}/>
                </div>
                <div>
                  <label class={labelCls} style="color:var(--ws-muted)">{$t('wwTimeTo')}</label>
                  <input type="time" bind:value={fArrMax} class={inputCls} style={inputStyle}/>
                </div>
              </div>
            </div>
          </div>
          <p class="text-xs mt-2" style="color:var(--ws-muted)">{$t('defaultsFlightTimesHint')}</p>
        </div>

      </div>
    {/if}
  </div>

  <!-- ══════════════════════════════════════════════════════════════════════ -->
  <!-- Akkordeon 2: Reisepersönlichkeit                                        -->
  <!-- ══════════════════════════════════════════════════════════════════════ -->
  <div class="rounded-2xl border overflow-hidden" style="border-color:var(--ws-border)">
    <button
      onclick={() => openPersoenlich = !openPersoenlich}
      class="w-full flex items-center justify-between px-4 py-3 text-left transition-opacity hover:opacity-80"
      style="background:var(--ws-surface2)">
      <div class="flex items-center gap-2">
        <span class="text-base">🧭</span>
        <span class="text-sm font-bold" style="color:var(--ws-text)">{$t('defaultsAccPersonalityTitle')}</span>
        <span class="text-xs px-2 py-0.5 rounded-full" style="background:rgba(196,98,45,.1);color:var(--ws-accent)">
          {$t('defaultsAccPersonalitySub')}
        </span>
      </div>
      <span class="text-xs transition-transform" style="color:var(--ws-muted);transform:{openPersoenlich ? 'rotate(180deg)' : 'rotate(0deg)'}">▼</span>
    </button>

    {#if openPersoenlich}
      <div class="px-4 py-4 space-y-4 border-t" style="border-color:var(--ws-border)">

        <!-- Reisestil -->
        <div>
          <div class="text-xs font-semibold mb-2" style="color:var(--ws-text)">✈️ {$t('defaultsTravelStyle')}</div>
          <div class="flex flex-wrap gap-2">
            {#each [
              ['adventure',  '🏔️ ' + $t('wwVibeAdventure').replace('🧗 ','')],
              ['relaxation', '🏖️ ' + $t('wwVibeRelax').replace('🧘 ','')],
              ['culture',    '🏛️ ' + $t('wwVibeCulture').replace('🏛️ ','')],
              ['nature',     '🌿 ' + $t('wwVibeNature').replace('🌿 ','')],
              ['city',       '🌆 ' + $t('wwVibeCity').replace('🌆 ','')],
            ] as [val, label]}
              <button onclick={() => travelStyle = travelStyle === val ? '' : val}
                class="px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all"
                style={travelStyle === val
                  ? 'background:var(--ws-accent);border-color:var(--ws-accent);color:#fff5ec'
                  : 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)'}>
                {label}
              </button>
            {/each}
          </div>
        </div>

        <!-- Klima -->
        <div>
          <div class="text-xs font-semibold mb-2" style="color:var(--ws-text)">🌡️ {$t('defaultsClimate')}</div>
          <div class="flex flex-wrap gap-2">
            {#each [
              ['warm', '☀️ ' + $t('defaultsClimateWarm')],
              ['mild', '🌤️ ' + $t('defaultsClimateMild')],
              ['cold', '❄️ ' + $t('defaultsClimateCold')],
              ['any',  '🌍 ' + $t('defaultsClimateAny')],
            ] as [val, label]}
              <button onclick={() => climatePref = climatePref === val ? '' : val}
                class="px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all"
                style={climatePref === val
                  ? 'background:var(--ws-accent);border-color:var(--ws-accent);color:#fff5ec'
                  : 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)'}>
                {label}
              </button>
            {/each}
          </div>
        </div>

        <!-- Landschaft -->
        <div>
          <div class="text-xs font-semibold mb-2" style="color:var(--ws-text)">🗺️ {$t('defaultsLandscape')}</div>
          <div class="flex flex-wrap gap-2">
            {#each [
              ['mountains', '⛰️ ' + $t('defaultsLandMountains')],
              ['sea',       '🌊 ' + $t('defaultsLandSea')],
              ['forest',    '🌲 ' + $t('defaultsLandForest')],
              ['city',      '🏙️ ' + $t('defaultsLandCity')],
              ['mix',       '🎲 ' + $t('defaultsLandMix')],
            ] as [val, label]}
              <button onclick={() => landscapePref = landscapePref === val ? '' : val}
                class="px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all"
                style={landscapePref === val
                  ? 'background:var(--ws-accent);border-color:var(--ws-accent);color:#fff5ec'
                  : 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)'}>
                {label}
              </button>
            {/each}
          </div>
        </div>

        <!-- Reisebegleitung -->
        <div>
          <div class="text-xs font-semibold mb-2" style="color:var(--ws-text)">👥 {$t('defaultsCompanions')}</div>
          <div class="flex flex-wrap gap-2">
            {#each [
              ['solo',    '🧍 ' + $t('defaultsCompSolo')],
              ['couple',  '👫 ' + $t('defaultsCompCouple')],
              ['family_kids',  '👶 ' + $t('defaultsCompFamilyKids')],
              ['family_teens', '🧒 ' + $t('defaultsCompFamilyTeens')],
              ['friends', '👯 ' + $t('defaultsCompFriends')],
            ] as [val, label]}
              <button onclick={() => companions = companions === val ? '' : val}
                class="px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all"
                style={companions === val
                  ? 'background:var(--ws-accent);border-color:var(--ws-accent);color:#fff5ec'
                  : 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)'}>
                {label}
              </button>
            {/each}
          </div>
        </div>

        <hr style="border-color:var(--ws-border)"/>

        <!-- Reisemodus -->
        <div>
          <div class="text-xs font-semibold mb-2" style="color:var(--ws-text)">🚗 {$t('defaultsTravelMode')}</div>
          <div class="flex gap-2">
            {#each [
              ['flight', '✈️ ' + $t('wwModeFlugTitle')],
              ['car',    '🚗 ' + $t('wwModeAutoTitle')],
            ] as [val, label]}
              <button onclick={() => travelMode = val}
                class="flex-1 py-2 rounded-xl border text-xs font-semibold transition-all"
                style={travelMode === val
                  ? 'background:var(--ws-accent);border-color:var(--ws-accent);color:#fff5ec'
                  : 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)'}>
                {label}
              </button>
            {/each}
          </div>
          <p class="text-xs mt-1.5" style="color:var(--ws-muted)">
            {travelMode === 'car' ? $t('defaultsTravelModeCarHint') : $t('defaultsTravelModeFlightHint')}
          </p>
        </div>

        <!-- Max. Reisezeit -->
        <div>
          <div class="text-xs font-semibold mb-2" style="color:var(--ws-text)">
            ⏳ {$t('defaultsMaxTime')}
            <span class="font-normal ml-1" style="color:var(--ws-muted)">
              ({travelMode === 'car' ? $t('wwMaxTravelTimeCar') : $t('wwMaxTravelTime')})
            </span>
          </div>
          <div class="flex flex-wrap gap-2">
            {#each [['2h','2 h'],['4h','4 h'],['8h','8 h'],['12h','12 h'],['12h+','12 h+'],['any',$t('wwMaxTimeAny')]] as [val, label]}
              <button onclick={() => maxTravelTime = val}
                class="px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all"
                style={maxTravelTime === val
                  ? 'background:var(--ws-accent);border-color:var(--ws-accent);color:#fff5ec'
                  : 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)'}>
                {label}
              </button>
            {/each}
          </div>
        </div>

        <!-- History-Modus -->
        <div>
          <div class="text-xs font-semibold mb-2" style="color:var(--ws-text)">🗂️ {$t('defaultsHistoryMode')}</div>
          <div class="flex gap-2">
            {#each [
              ['blacklist', '🚫 ' + $t('defaultsHistoryBlacklist')],
              ['context',   '💡 ' + $t('defaultsHistoryContext')],
            ] as [val, label]}
              <button onclick={() => historyMode = val}
                class="flex-1 py-2 rounded-xl border text-xs font-semibold transition-all"
                style={historyMode === val
                  ? 'background:var(--ws-accent);border-color:var(--ws-accent);color:#fff5ec'
                  : 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)'}>
                {label}
              </button>
            {/each}
          </div>
          <p class="text-xs mt-1.5" style="color:var(--ws-muted)">
            {historyMode === 'context' ? $t('defaultsHistoryContextHint') : $t('defaultsHistoryBlacklistHint')}
          </p>
        </div>

        <!-- Wunschtext -->
        <div>
          <div class="text-xs font-semibold mb-2" style="color:var(--ws-text)">💭 {$t('defaultsWishText')}</div>
          <textarea bind:value={wishText} maxlength="500" rows="3"
            placeholder={$t('defaultsWishPlaceholder')}
            class="w-full px-3 py-2 rounded-xl border text-sm resize-none focus:outline-none focus:ring-2 focus:ring-[var(--ws-accent)]"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"></textarea>
          <div class="text-xs mt-1 text-right" style="color:var(--ws-muted)">{(wishText||'').length}/500</div>
        </div>

      </div>
    {/if}
  </div>

</div>

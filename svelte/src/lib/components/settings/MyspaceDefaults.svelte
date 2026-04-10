<script>
  const inputCls   = 'w-full px-3 py-2 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ws-accent)]';
  const inputStyle = 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)';
  const labelCls   = 'block text-xs font-bold uppercase tracking-wider mb-1';

  let {
    defAdults   = $bindable(),
    defChildren = $bindable(),
    homeAirport = $bindable(),
    lugS10      = $bindable(),
    lugS20      = $bindable(),
    lugS23      = $bindable(),
    lugL10      = $bindable(),
    lugL20      = $bindable(),
    lugL23      = $bindable(),
    fDepMin     = $bindable(),
    fDepMax     = $bindable(),
    fArrMin     = $bindable(),
    fArrMax     = $bindable(),
    travelStyle   = $bindable(),
    climatePref   = $bindable(),
    landscapePref = $bindable(),
    companions    = $bindable(),
    wishText      = $bindable(),
  } = $props();

  function stepper(getter, setter, min = 0, max = 9) {
    return {
      dec: () => setter(Math.max(min, getter() - 1)),
      inc: () => setter(Math.min(max, getter() + 1)),
    };
  }
</script>

<div class="space-y-5 mt-1">

  <!-- ── Reisende ── -->
  <div>
    <div class="text-xs font-bold uppercase tracking-wider mb-3" style="color:var(--ws-muted)">👥 Standard-Reisende</div>
    <div class="grid grid-cols-3 gap-3">

      <!-- Erwachsene -->
      <div class="rounded-xl border p-3 flex flex-col items-center gap-2"
        style="background:var(--ws-surface2);border-color:var(--ws-border)">
        <div class="text-xs font-semibold" style="color:var(--ws-muted)">Erwachsene</div>
        <div class="flex items-center gap-2">
          <button onclick={() => defAdults = Math.max(1, defAdults - 1)}
            class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center"
            style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">−</button>
          <span class="text-sm font-bold w-5 text-center" style="color:var(--ws-text)">{defAdults}</span>
          <button onclick={() => defAdults = Math.min(9, defAdults + 1)}
            class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center"
            style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
        </div>
      
  <hr style="border-color:var(--ws-border)"/>

  <!-- ── Reisepersönlichkeit ── -->
  <div>
    <div class="text-xs font-bold uppercase tracking-wider mb-3" style="color:var(--ws-muted)">🧭 Reisepersönlichkeit</div>

    <!-- Reisestil -->
    <div class="mb-4">
      <div class="text-xs font-semibold mb-2" style="color:var(--ws-text)">✈️ Reisestil</div>
      <div class="flex flex-wrap gap-2">
        {#each [
          ['adventure',   '🏔️ Abenteuer'],
          ['relaxation',  '🏖️ Entspannung'],
          ['culture',     '🏛️ Kultur'],
          ['nature',      '🌿 Natur'],
          ['city',        '🌆 City'],
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
    <div class="mb-4">
      <div class="text-xs font-semibold mb-2" style="color:var(--ws-text)">🌡️ Klimapräferenz</div>
      <div class="flex flex-wrap gap-2">
        {#each [
          ['warm', '☀️ Warm'],
          ['mild', '🌤️ Mild'],
          ['cold', '❄️ Kalt'],
          ['any',  '🌍 Egal'],
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
    <div class="mb-4">
      <div class="text-xs font-semibold mb-2" style="color:var(--ws-text)">🗺️ Landschaft</div>
      <div class="flex flex-wrap gap-2">
        {#each [
          ['mountains', '⛰️ Berge'],
          ['sea',       '🌊 Meer'],
          ['forest',    '🌲 Wald'],
          ['city',      '🏙️ Stadt'],
          ['mix',       '🎲 Mix'],
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
    <div class="mb-4">
      <div class="text-xs font-semibold mb-2" style="color:var(--ws-text)">👥 Reisebegleitung</div>
      <div class="flex flex-wrap gap-2">
        {#each [
          ['solo',    '🧍 Solo'],
          ['couple',  '👫 Pärchen'],
          ['family',  '👨‍👩‍👧 Familie'],
          ['friends', '👯 Freunde'],
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

    <!-- Wunschtext -->
    <div>
      <div class="text-xs font-semibold mb-2" style="color:var(--ws-text)">💭 Reisewunsch (Freitext)</div>
      <textarea bind:value={wishText} maxlength="500" rows="3"
        placeholder="Beschreibe deinen Traumurlaub… z.B. Strand, Sonne, gutes Essen, keine Touristenmassen"
        class="w-full px-3 py-2 rounded-xl border text-sm resize-none focus:outline-none focus:ring-2 focus:ring-[var(--ws-accent)]"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"></textarea>
      <div class="text-xs mt-1 text-right" style="color:var(--ws-muted)">{(wishText||'').length}/500</div>
    </div>
  </div>

</div>

      <!-- Kinder -->
      <div class="rounded-xl border p-3 flex flex-col items-center gap-2"
        style="background:var(--ws-surface2);border-color:var(--ws-border)">
        <div class="text-xs font-semibold" style="color:var(--ws-muted)">Kinder</div>
        <div class="flex items-center gap-2">
          <button onclick={() => defChildren = Math.max(0, defChildren - 1)}
            class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center"
            style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">−</button>
          <span class="text-sm font-bold w-5 text-center" style="color:var(--ws-text)">{defChildren}</span>
          <button onclick={() => defChildren = Math.min(8, defChildren + 1)}
            class="w-7 h-7 rounded-lg border text-base font-bold flex items-center justify-center"
            style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
        </div>
      </div>

      <!-- Heimatflughafen -->
      <div class="rounded-xl border p-3 flex flex-col gap-1"
        style="background:var(--ws-surface2);border-color:var(--ws-border)">
        <div class="text-xs font-semibold" style="color:var(--ws-muted)">Heimatflughafen</div>
        <input bind:value={homeAirport} maxlength="3" placeholder="BGY"
          class="w-full px-2 py-1 rounded-lg border text-sm font-mono uppercase text-center focus:outline-none focus:ring-2 focus:ring-[var(--ws-accent)]"
          style={inputStyle}/>
      </div>

    </div>
  </div>

  <hr style="border-color:var(--ws-border)"/>

  <!-- ── Gepäck-Matrix ── -->
  <div>
    <div class="text-xs font-bold uppercase tracking-wider mb-3" style="color:var(--ws-muted)">🧳 Standard-Gepäck</div>
    <div class="grid grid-cols-2 gap-4">

      <!-- Kurztrip -->
      <div class="rounded-xl border p-3 space-y-2" style="background:var(--ws-surface2);border-color:var(--ws-border)">
        <div class="text-xs font-semibold mb-2" style="color:var(--ws-text)">⚡ Kurztrip (1–3 Tage)</div>
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
                style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">−</button>
              <span class="w-4 text-center text-sm font-bold" style="color:{getter()>0?'var(--ws-accent)':'var(--ws-muted)'}">{getter()}</span>
              <button onclick={() => setter(Math.min(9, getter() + 1))}
                class="w-6 h-6 rounded border text-sm font-bold flex items-center justify-center"
                style="background:var(--ws-accent);border-color:var(--ws-accent);color:#fff">+</button>
            </div>
          </div>
        {/each}
      </div>

      <!-- Langtrip -->
      <div class="rounded-xl border p-3 space-y-2" style="background:var(--ws-surface2);border-color:var(--ws-border)">
        <div class="text-xs font-semibold mb-2" style="color:var(--ws-text)">🌍 Langtrip (4+ Tage)</div>
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
                style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)">−</button>
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

  <!-- ── Flugzeit-Fenster ── -->
  <div>
    <div class="text-xs font-bold uppercase tracking-wider mb-3" style="color:var(--ws-muted)">⏱️ Bevorzugte Flugzeiten</div>
    <div class="grid grid-cols-2 gap-4">
      <div class="space-y-2">
        <div class="text-xs font-semibold" style="color:var(--ws-text)">🛫 Abflug</div>
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="{labelCls}" style="color:var(--ws-muted)">ab</label>
            <input type="time" bind:value={fDepMin} class={inputCls} style={inputStyle}/>
          </div>
          <div>
            <label class="{labelCls}" style="color:var(--ws-muted)">bis</label>
            <input type="time" bind:value={fDepMax} class={inputCls} style={inputStyle}/>
          </div>
        </div>
      </div>
      <div class="space-y-2">
        <div class="text-xs font-semibold" style="color:var(--ws-text)">🛬 Ankunft</div>
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="{labelCls}" style="color:var(--ws-muted)">ab</label>
            <input type="time" bind:value={fArrMin} class={inputCls} style={inputStyle}/>
          </div>
          <div>
            <label class="{labelCls}" style="color:var(--ws-muted)">bis</label>
            <input type="time" bind:value={fArrMax} class={inputCls} style={inputStyle}/>
          </div>
        </div>
      </div>
    </div>
    <p class="text-xs mt-2" style="color:var(--ws-muted)">Wird im WanderWizzard als Vorauswahl verwendet — jederzeit pro Suche überschreibbar.</p>
  </div>

</div>

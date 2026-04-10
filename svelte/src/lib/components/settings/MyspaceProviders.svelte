<script>
  let {
    providers        = $bindable(),
    providerKeys     = $bindable(),
    providersLoading,
    providersSaving,
    onsave,
  } = $props();
</script>

<div class="space-y-3 mt-1">
  <div class="text-xs" style="color:var(--ws-muted)">
    Aktiviere die gewünschten Flug-Suchmaschinen. Deaktivierte Provider werden bei der Suche übersprungen.
  </div>

  {#if providersLoading}
    <div class="space-y-2">
      {#each [1,2,3,4] as _}
        <div class="h-16 rounded-xl animate-pulse" style="background:var(--ws-border)"></div>
      {/each}
    </div>
  {:else if providers.length === 0}
    <div class="text-xs py-4 text-center" style="color:var(--ws-muted)">
      Backend nicht erreichbar — Provider-Einstellungen nicht verfügbar.
    </div>
  {:else}
    {#each providers as provider (provider.name)}
      <div class="rounded-xl border p-3 space-y-2"
        style="background:var(--ws-surface2);border-color:{provider.enabled ? 'var(--ws-accent)' : 'var(--ws-border)'};">

        <!-- Provider header row: icon + name + toggle -->
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-2">
            <span class="text-base">{provider.icon}</span>
            <div>
              <div class="text-xs font-semibold" style="color:var(--ws-text)">{provider.label}</div>
              <div class="flex items-center gap-1.5 mt-0.5">
                {#if provider.has_key && provider.key_required}
                  <span class="text-[10px] px-1.5 py-0.5 rounded-full font-medium"
                    style="background:rgba(22,163,74,.12);color:var(--ws-green)">✓ Key gesetzt</span>
                {:else if provider.key_required && !provider.has_key}
                  <span class="text-[10px] px-1.5 py-0.5 rounded-full font-medium"
                    style="background:rgba(220,38,38,.1);color:#dc2626">Key fehlt</span>
                {:else if !provider.key_required}
                  <span class="text-[10px] px-1.5 py-0.5 rounded-full font-medium"
                    style="background:rgba(37,99,235,.1);color:#2563eb">Kein Key nötig</span>
                {/if}
                {#if provider.name === 'duffel' && provider.test_mode}
                  <span class="text-[10px] px-1.5 py-0.5 rounded-full font-medium"
                    style="background:rgba(234,179,8,.15);color:#ca8a04">🧪 Test-Mode</span>
                {/if}
              </div>
            </div>
          </div>
          <!-- Toggle switch -->
          <button
            onclick={() => { provider.enabled = !provider.enabled; providers = [...providers]; }}
            class="relative w-10 h-6 rounded-full transition-colors shrink-0"
            style="background:{provider.enabled ? 'var(--ws-accent)' : 'var(--ws-border)'}">
            <span class="absolute top-1 w-4 h-4 rounded-full bg-white transition-all"
              style="left:{provider.enabled ? '22px' : '4px'}"></span>
          </button>
        </div>

        <!-- Key input (only if key required + enabled) -->
        {#if provider.key_required && provider.enabled}
          <input
            type="password"
            value={providerKeys[provider.name] ?? ''}
            oninput={(e) => { providerKeys = { ...providerKeys, [provider.name]: e.target.value }; }}
            placeholder={provider.has_key ? '••••••••  (leer lassen = nicht ändern)' : 'API Key eingeben'}
            class="w-full px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text)"/>
          {#if provider.name === 'google_flights'}
            <div class="text-[10px]" style="color:var(--ws-muted)">
              SerpAPI Key: <a href="https://serpapi.com/manage-api-key" target="_blank" rel="noopener" style="color:var(--ws-accent)">serpapi.com ↗</a>
              · Wird auch für Hotel- &amp; Camping-Suche verwendet
            </div>
          {:else if provider.name === 'kiwi'}
            <div class="text-[10px]" style="color:var(--ws-muted)">
              Tequila API Key: <a href="https://tequila.kiwi.com/" target="_blank" rel="noopener" style="color:var(--ws-accent)">tequila.kiwi.com ↗</a>
              · Kostenlos bis 500 Suchen/Monat · Liefert mehrere Flüge/Tag
            </div>
          {:else if provider.name === 'duffel'}
            <div class="text-[10px]" style="color:var(--ws-muted)">
              Duffel API Key: <a href="https://app.duffel.com/join" target="_blank" rel="noopener" style="color:var(--ws-accent)">app.duffel.com ↗</a>
              · Test-Key beginnt mit <code>duffel_test_</code>
            </div>
          {/if}
        {/if}

        <!-- Duffel test mode toggle -->
        {#if provider.name === 'duffel' && provider.enabled}
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" bind:checked={provider.test_mode}
              onchange={() => { providers = [...providers]; }}
              class="w-4 h-4 accent-[var(--ws-accent)]"/>
            <span class="text-xs" style="color:var(--ws-muted)">
              🧪 Test-Mode — simulierte Preise, werden mit Badge markiert und nicht in Tracker-Snapshots gespeichert
            </span>
          </label>
        {/if}

      </div>
    {/each}
  {/if}

  {#if providers.length > 0}
    <button onclick={onsave} disabled={providersSaving}
      class="w-full py-2 rounded-xl text-xs font-semibold border transition-opacity hover:opacity-80 disabled:opacity-50"
      style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)">
      {providersSaving ? '⏳ Speichern…' : '💾 Suchmaschinen speichern'}
    </button>
  {/if}
</div>

<script>
  let { open = $bindable(false) } = $props();
  let activeTab = $state('start');

  const tabs = [
    { id: 'start',    label: '🚀 Start' },
    { id: 'radar',    label: '🎯 Preis-Radar' },
    { id: 'reisen',   label: '🎒 Reisen' },
    { id: 'apis',     label: '🔑 API Keys' },
  ];
</script>

{#if open}
  <div class="fixed inset-0 z-40 bg-black/40"
    onclick={() => open = false}
    onkeydown={(e) => e.key==='Escape' && (open=false)}
    role="button" tabindex="-1" aria-label="Schließen">
  </div>

  <div class="fixed inset-y-0 right-0 z-50 w-full max-w-lg flex flex-col shadow-2xl"
    style="background:var(--ws-surface)">

    <div class="flex items-center justify-between px-5 py-4 border-b" style="border-color:var(--ws-border)">
      <div>
        <h2 class="font-bold text-lg italic" style="font-family:var(--ws-serif)">📖 Feldführer</h2>
        <p class="text-xs mt-0.5" style="color:var(--ws-muted)">Alles was du wissen musst</p>
      </div>
      <button onclick={() => open=false} class="p-1.5 rounded-lg hover:opacity-60 text-lg">✕</button>
    </div>

    <div class="flex border-b px-2 gap-0.5 pt-2 overflow-x-auto shrink-0" style="border-color:var(--ws-border)">
      {#each tabs as tab}
        <button onclick={() => activeTab=tab.id}
          class="px-3 py-2 text-xs rounded-t-lg font-medium whitespace-nowrap shrink-0"
          style={activeTab===tab.id
            ? 'color:var(--ws-accent);border-bottom:2px solid var(--ws-accent)'
            : 'color:var(--ws-muted)'}>
          {tab.label}
        </button>
      {/each}
    </div>

    <div class="flex-1 overflow-y-auto p-5 space-y-4 text-sm">

      {#if activeTab==='start'}
        <h3 class="font-bold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">Willkommen bei WanderSuite 👋</h3>
        <p style="color:var(--ws-muted)">WanderSuite ist dein self-hosted Reise-Tracker. Alle Daten bleiben auf deinem eigenen Server.</p>

        <div class="rounded-xl p-3 border space-y-2" style="background:var(--ws-surface2);border-color:var(--ws-border)">
          <div class="font-semibold text-xs uppercase tracking-wider" style="color:var(--ws-muted)">Schnellstart</div>
          <div class="space-y-1.5 text-xs" style="color:var(--ws-text)">
            <div>1. ⚙️ Einstellungen öffnen → Backend-URL eintragen</div>
            <div>2. 🎯 Preis-Radar → ersten Ryanair Tracker anlegen</div>
            <div>3. 🔑 API Keys hinterlegen für Google Flights & KI</div>
            <div>4. 🧭 Dawarich verbinden für automatisches Reisetagebuch</div>
          </div>
        </div>

        <div class="rounded-xl p-3 border" style="background:var(--ws-surface2);border-color:var(--ws-border)">
          <div class="font-semibold text-xs uppercase tracking-wider mb-1.5" style="color:var(--ws-muted)">Täglicher Scheduler</div>
          <p class="text-xs" style="color:var(--ws-text)">WanderSuite scrapt alle aktiven Tracker täglich um <strong>07:00 Uhr</strong> (Europe/Rome) automatisch. Manuelle Abfrage jederzeit über den ⟳-Button.</p>
        </div>

      {:else if activeTab==='radar'}
        <h3 class="font-bold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">Preis-Radar 🎯</h3>

        <div class="space-y-3">
          <div class="rounded-xl p-3 border" style="background:var(--ws-surface2);border-color:var(--ws-border)">
            <div class="font-semibold text-xs mb-1">🟠 Ryanair</div>
            <p class="text-xs" style="color:var(--ws-muted)">Direkte API — kein Key nötig. IATA-Codes eingeben (z.B. BGY = Bergamo, DUB = Dublin). Gepäck und Sitzplatz als Pauschale konfigurierbar.</p>
          </div>
          <div class="rounded-xl p-3 border" style="background:var(--ws-surface2);border-color:var(--ws-border)">
            <div class="font-semibold text-xs mb-1">🔵 Google Flights</div>
            <p class="text-xs" style="color:var(--ws-muted)">Nutzt SerpAPI. Zeigt Airline, Flugnummer und Zeiten. Free Plan: 100 Suchen/Monat.</p>
          </div>
          <div class="rounded-xl p-3 border" style="background:var(--ws-surface2);border-color:var(--ws-border)">
            <div class="font-semibold text-xs mb-1">⛺ Homair / 🏨 Booking</div>
            <p class="text-xs" style="color:var(--ws-muted)">Homair via HTML-Scraping (kein Key). Booking via SerpAPI Google Hotels (selber Key wie Google Flights).</p>
          </div>
          <div class="rounded-xl p-3 border" style="background:var(--ws-surface2);border-color:var(--ws-border)">
            <div class="font-semibold text-xs mb-1">IATA-Codes finden</div>
            <p class="text-xs" style="color:var(--ws-muted)">Auf <strong>iata.org</strong> oder Google: "IATA Code [Stadt]". Beispiele: BGY=Bergamo, VIE=Wien, MUC=München, DUB=Dublin, FCO=Rom.</p>
          </div>
        </div>

      {:else if activeTab==='reisen'}
        <h3 class="font-bold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">Meine Reisen & Tagebuch 🎒</h3>

        <div class="space-y-3">
          <div class="rounded-xl p-3 border" style="background:var(--ws-surface2);border-color:var(--ws-border)">
            <div class="font-semibold text-xs mb-1">📓 Reisetagebuch (Dawarich)</div>
            <p class="text-xs" style="color:var(--ws-muted)">Verbindet sich mit deiner Dawarich-Instanz und erkennt automatisch Übernacht-Reisen: Punkte &gt;50km von Home, mind. 2 aufeinanderfolgende Tage. Reverse Geocoding via OpenStreetMap.</p>
          </div>
          <div class="rounded-xl p-3 border" style="background:var(--ws-surface2);border-color:var(--ws-border)">
            <div class="font-semibold text-xs mb-1">💶 Budget</div>
            <p class="text-xs" style="color:var(--ws-muted)">Jahresbudget manuell setzen oder via ActualBudget synchronisieren. Reisen mit Kosten erfassen für Fortschrittsanzeige im Dashboard.</p>
          </div>
          <div class="rounded-xl p-3 border" style="background:var(--ws-surface2);border-color:var(--ws-border)">
            <div class="font-semibold text-xs mb-1">✨ KI-Inspiration (Discover)</div>
            <p class="text-xs" style="color:var(--ws-muted)">Beschreibe was du suchst — die KI (Gemini oder OpenAI) gibt 5 Reiseziele mit Begründung, Reisezeit, Budget und Top-Aktivität zurück.</p>
          </div>
        </div>

      {:else if activeTab==='apis'}
        <h3 class="font-bold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">API Keys hinterlegen 🔑</h3>

        <div class="space-y-3">
          {#each [
            { name:'SerpAPI', url:'serpapi.com', free:'100 Suchen/Monat', use:'Google Flights + Booking' },
            { name:'Google Gemini', url:'aistudio.google.com', free:'kostenlos', use:'KI-Reiseempfehlungen' },
            { name:'OpenAI', url:'platform.openai.com', free:'~$0.00015/1k Tokens', use:'KI-Reiseempfehlungen (Alternative)' },
          ] as api}
            <div class="rounded-xl p-3 border" style="background:var(--ws-surface2);border-color:var(--ws-border)">
              <div class="flex justify-between items-start">
                <div class="font-semibold text-xs">{api.name}</div>
                <span class="text-xs px-1.5 py-0.5 rounded font-mono" style="background:rgba(58,140,98,.15);color:var(--ws-green)">{api.free}</span>
              </div>
              <p class="text-xs mt-1" style="color:var(--ws-muted)">{api.use}</p>
              <div class="text-xs mt-1 font-mono" style="color:var(--ws-accent2)">→ {api.url}</div>
            </div>
          {/each}
          <div class="rounded-xl p-3 border" style="background:var(--ws-surface2);border-color:var(--ws-border)">
            <div class="font-semibold text-xs mb-1">💶 ActualBudget</div>
            <p class="text-xs" style="color:var(--ws-muted)">Self-hosted. URL + Server-Passwort als Token. Kategorienamen für Reise-Ausgaben konfigurieren (z.B. "Holiday, Flights, Hotel").</p>
            <div class="mt-2 text-xs font-semibold" style="color:var(--ws-text)">Budget-Dateiname finden:</div>
            <ol class="text-xs mt-1 space-y-0.5 list-decimal list-inside" style="color:var(--ws-muted)">
              <li>ActualBudget öffnen → oben links auf den Budget-Namen klicken</li>
              <li>In der URL erscheint die Budget-ID, z.B. <code class="font-mono px-1 rounded" style="background:var(--ws-surface);color:var(--ws-accent2)">My-Finances-abc123</code></li>
              <li>Alternativ: <strong>Settings → Advanced → Budget ID</strong> (neuere Versionen)</li>
              <li>Diesen Namen (ohne .blob) in WanderSuite eintragen</li>
            </ol>
          </div>
        </div>
      {/if}

    </div>
  </div>
{/if}

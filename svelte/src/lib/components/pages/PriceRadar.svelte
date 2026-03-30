<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';
  import { apiUrl } from '$lib/stores.js';
  import { toast } from '$lib/toast.js';

  let activeTab  = $state('ryanair');
  let trackers   = $state([]);
  let loading    = $state(true);

  // Ryanair form
  let origin       = $state('BGY');
  let destination  = $state('DUB');
  const today = new Date();
  const d30 = new Date(today); d30.setDate(d30.getDate() + 30);
  const d37 = new Date(today); d37.setDate(d37.getDate() + 37);
  let outbound  = $state(d30.toISOString().slice(0,10));
  let returnDate = $state(d37.toISOString().slice(0,10));
  let adults    = $state(2);
  let children  = $state(0);
  let seatCost  = $state(0);
  let bags      = $state([]);
  let adding    = $state(false);

  const bagOptions = [
    { type: '10kg', label: '10 kg Check-in Koffer' },
    { type: '20kg', label: '20 kg Check-in Koffer' },
    { type: '23kg', label: '23 kg Koffer (Large)' },
  ];

  function toggleBag(type) {
    bags = bags.includes(type) ? bags.filter(b => b !== type) : [...bags, type];
  }

  onMount(loadTrackers);

  async function loadTrackers() {
    if (!$apiUrl) { loading = false; return; }
    try {
      trackers = await api('/api/trackers');
    } catch(e) { toast('Fehler beim Laden', 'error'); }
    loading = false;
  }

  async function addTracker() {
    if (!origin || !destination || !outbound) { toast('Bitte alle Pflichtfelder ausfüllen', 'error'); return; }
    if (!$apiUrl) { toast('Backend-URL fehlt', 'warning'); return; }
    adding = true;
    try {
      await api('/api/trackers', {
        method: 'POST',
        body: JSON.stringify({
          origin: origin.toUpperCase(),
          destination: destination.toUpperCase(),
          outbound_date: outbound,
          return_date: returnDate || null,
          adults, children,
          baggage: bags.map(type => ({ type, per_person: true })),
          seat_cost: parseFloat(seatCost) || 0,
        }),
      });
      toast('Tracker angelegt ✓', 'success');
      await loadTrackers();
    } catch(e) { toast(e.message, 'error'); }
    adding = false;
  }

  async function scrapeNow(id) {
    toast('Preis wird abgerufen…', 'warning');
    try {
      const res = await api(`/api/trackers/${id}/scrape`, { method: 'POST' });
      toast(`Aktuell: ${res.snapshot?.total_price?.toFixed(2)} €`, 'success');
      await loadTrackers();
    } catch(e) { toast(e.message, 'error'); }
  }

  async function deleteTracker(id) {
    if (!confirm('Tracker wirklich löschen?')) return;
    await api(`/api/trackers/${id}`, { method: 'DELETE' });
    await loadTrackers();
  }

  const tabs = [
    { id: 'ryanair', label: '🟠 Ryanair' },
    { id: 'gflights', label: '🔵 Google Flights' },
    { id: 'homair',   label: '⛺ Homair' },
    { id: 'booking',  label: '🏨 Booking' },
  ];
</script>

<div class="space-y-4">
  <h1 class="text-2xl font-bold italic" style="font-family:var(--ws-serif)">🎯 Preis-Radar</h1>

  <!-- Tabs -->
  <div class="flex gap-1 overflow-x-auto pb-1">
    {#each tabs as tab}
      <button
        onclick={() => activeTab = tab.id}
        class="px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all border"
        style={activeTab === tab.id
          ? 'background:var(--ws-accent);color:#fff5ec;border-color:var(--ws-accent)'
          : 'background:var(--ws-surface);color:var(--ws-muted);border-color:var(--ws-border)'}
      >{tab.label}</button>
    {/each}
  </div>

  {#if activeTab === 'ryanair'}
  <div class="grid md:grid-cols-2 gap-4">

    <!-- Add form -->
    <div class="rounded-xl p-4 border space-y-3" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">Neuen Tracker anlegen</h2>

      <div class="grid grid-cols-2 gap-2">
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Von (IATA)</label>
          <input bind:value={origin} maxlength="3" placeholder="BGY"
            class="w-full mt-1 px-3 py-2 rounded-xl border text-sm font-mono uppercase"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
        </div>
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Nach (IATA)</label>
          <input bind:value={destination} maxlength="3" placeholder="DUB"
            class="w-full mt-1 px-3 py-2 rounded-xl border text-sm font-mono uppercase"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-2">
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Hinflug</label>
          <input type="date" bind:value={outbound}
            class="w-full mt-1 px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
        </div>
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Rückflug (opt.)</label>
          <input type="date" bind:value={returnDate}
            class="w-full mt-1 px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-2">
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Erwachsene</label>
          <select bind:value={adults}
            class="w-full mt-1 px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)">
            {#each [1,2,3,4,5,6] as n}<option value={n}>{n}</option>{/each}
          </select>
        </div>
        <div>
          <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">Kinder</label>
          <select bind:value={children}
            class="w-full mt-1 px-3 py-2 rounded-xl border text-sm"
            style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)">
            {#each [0,1,2,3,4] as n}<option value={n}>{n}</option>{/each}
          </select>
        </div>
      </div>

      <!-- Baggage -->
      <div>
        <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">🧳 Gepäck (pro Person)</label>
        <div class="mt-1.5 space-y-1.5">
          {#each bagOptions as b}
            <button
              onclick={() => toggleBag(b.type)}
              class="w-full flex items-center gap-3 px-3 py-2 rounded-xl border text-sm transition-colors text-left"
              style={bags.includes(b.type)
                ? 'background:rgba(196,98,45,.1);border-color:var(--ws-accent);color:var(--ws-text)'
                : 'background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)'}
            >
              <span class="w-4 h-4 rounded border flex items-center justify-center text-xs"
                style="border-color:{bags.includes(b.type) ? 'var(--ws-accent)' : 'var(--ws-border)'}">
                {bags.includes(b.type) ? '✓' : ''}
              </span>
              {b.label}
            </button>
          {/each}
        </div>
      </div>

      <!-- Seat cost -->
      <div>
        <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">🪑 Sitzplatz (€/Person/Flug)</label>
        <input type="number" bind:value={seatCost} min="0" step="0.01" placeholder="0.00"
          class="w-full mt-1 px-3 py-2 rounded-xl border text-sm"
          style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      </div>

      <button
        onclick={addTracker}
        disabled={adding}
        class="w-full py-2.5 rounded-xl font-semibold text-sm transition-opacity hover:opacity-80 disabled:opacity-50"
        style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec"
      >
        {adding ? '⏳ Erstelle…' : '+ Tracker starten'}
      </button>
    </div>

    <!-- Tracker list -->
    <div class="space-y-3">
      <h2 class="text-sm font-semibold italic" style="font-family:var(--ws-serif);color:var(--ws-accent2)">Aktive Tracker</h2>
      {#if loading}
        <p class="text-xs" style="color:var(--ws-muted)">Lade…</p>
      {:else if trackers.length === 0}
        <p class="text-xs" style="color:var(--ws-muted)">Noch keine Ryanair Tracker.</p>
      {:else}
        {#each trackers as tr}
          {@const snap = tr.latest_snapshot}
          <div class="rounded-xl p-3 border" style="background:var(--ws-surface);border-color:var(--ws-border)">
            <div class="flex items-start justify-between">
              <div>
                <div class="font-bold font-mono text-sm" style="color:var(--ws-text)">{tr.origin} → {tr.destination}</div>
                <div class="text-xs mt-0.5 font-mono" style="color:var(--ws-muted)">{tr.outbound_date}{tr.return_date ? ' ⇄ ' + tr.return_date : ''}</div>
              </div>
              <div class="text-right">
                <div class="font-bold font-mono text-sm" style="color:var(--ws-green)">{snap?.total_price ? snap.total_price.toFixed(2) + ' €' : '–'}</div>
                <div class="text-xs font-mono" style="color:var(--ws-muted)">{snap?.fetched_at?.slice(0,10) ?? 'Noch nicht abgerufen'}</div>
              </div>
            </div>
            <div class="flex gap-2 mt-2.5">
              <button onclick={() => scrapeNow(tr.id)}
                class="flex-1 py-1.5 rounded-lg text-xs border transition-colors hover:border-[var(--ws-accent)]"
                style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">
                ⟳ Jetzt
              </button>
              <button onclick={() => deleteTracker(tr.id)}
                class="px-3 py-1.5 rounded-lg text-xs border transition-colors hover:border-red-400"
                style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-muted)">
                ✕
              </button>
            </div>
          </div>
        {/each}
      {/if}
    </div>
  </div>

  {:else}
    <div class="rounded-xl p-8 border text-center" style="background:var(--ws-surface);border-color:var(--ws-border)">
      <div class="text-3xl mb-2">{tabs.find(t => t.id === activeTab)?.label.split(' ')[0]}</div>
      <div class="font-semibold italic mb-1" style="font-family:var(--ws-serif);color:var(--ws-text)">
        {tabs.find(t => t.id === activeTab)?.label.slice(2)}
      </div>
      <div class="text-xs" style="color:var(--ws-muted)">Migration in nächster Iteration</div>
      <span class="inline-block mt-3 px-3 py-1 rounded-full text-xs font-mono"
        style="background:rgba(232,160,32,.12);color:var(--ws-accent2);border:1px solid rgba(232,160,32,.25)">
        Coming next
      </span>
    </div>
  {/if}
</div>

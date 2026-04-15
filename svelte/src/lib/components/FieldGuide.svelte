<script>
  import { t } from '$lib/i18n.js';

  let {
    open        = $bindable(false),
    initialTab  = 'vision',   // allow deep-link from wizard
  } = $props();

  let activeTab = $state(initialTab);

  // Sync if parent changes initialTab after mount (wizard step links)
  $effect(() => { if (open) activeTab = initialTab; });

  const tabs = $derived([
    { id: 'vision',   label: $t('fgTabVision') },
    { id: 'wizard',   label: $t('fgTabWizard') },
    { id: 'radar',    label: $t('fgTabRadar') },
    { id: 'trips',    label: $t('fgTabTrips') },
    { id: 'bridges',  label: $t('fgTabBridges') },
    { id: 'apis',     label: $t('fgTabApis') },
  ]);
</script>

{#if open}
  <div class="fixed inset-0 z-40 bg-black/40"
    onclick={() => open = false}
    onkeydown={(e) => e.key === 'Escape' && (open = false)}
    role="button" tabindex="-1" aria-label={$t('settingsClose')}>
  </div>

  <div class="fixed inset-0 md:inset-[5vh_10vw] md:rounded-2xl z-50 flex flex-col shadow-2xl overflow-hidden"
    style="background:var(--ws-surface)">

    <!-- Header -->
    <div class="flex items-center justify-between px-5 py-4 border-b" style="border-color:var(--ws-border)">
      <div>
        <h2 class="font-bold text-lg italic" style="font-family:var(--ws-serif)">{$t('fgTitle')}</h2>
        <p class="text-xs mt-0.5" style="color:var(--ws-muted)">{$t('fgSubtitle')}</p>
      </div>
      <button onclick={() => open = false} class="p-1.5 rounded-lg hover:opacity-60 text-lg">✕</button>
    </div>

    <!-- Tabs -->
    <div class="flex border-b px-2 gap-0.5 pt-2 overflow-x-auto shrink-0" style="border-color:var(--ws-border)">
      {#each tabs as tab}
        <button onclick={() => activeTab = tab.id}
          class="px-3 py-2 text-xs rounded-t-lg font-medium whitespace-nowrap shrink-0 transition-colors"
          style={activeTab === tab.id
            ? 'color:var(--ws-accent);border-bottom:2px solid var(--ws-accent)'
            : 'color:var(--ws-muted)'}>
          {tab.label}
        </button>
      {/each}
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto p-5 space-y-4 text-sm">

      {#if activeTab === 'vision'}
        <!-- ── Vision & Überblick ── -->
        <h3 class="font-bold italic text-base" style="font-family:var(--ws-serif);color:var(--ws-accent2)">{$t('fgVisionTitle')}</h3>
        <p style="color:var(--ws-muted)">{$t('fgVisionDesc')}</p>

        <div class="space-y-3">
          {#each [
            { phase: '1', icon: '✈️', key: 'fgPhase1', colorVar: '--ws-accent' },
            { phase: '2', icon: '🌍', key: 'fgPhase2', colorVar: '--ws-green' },
            { phase: '3', icon: '📓', key: 'fgPhase3', colorVar: '--ws-muted' },
          ] as p}
            <div class="rounded-xl border p-3.5" style="background:var(--ws-surface2);border-color:var(--ws-border)">
              <div class="flex items-center gap-2 mb-1.5">
                <span class="text-base">{p.icon}</span>
                <span class="font-bold text-xs uppercase tracking-wider" style="color:var(--{p.colorVar})">{$t(p.key + 'Title')}</span>
              </div>
              <p class="text-xs leading-relaxed" style="color:var(--ws-muted)">{$t(p.key + 'Desc')}</p>
              <ul class="mt-2 space-y-1">
                {#each ($t(p.key + 'Features') || '').split('|').filter(Boolean) as f}
                  <li class="text-xs flex gap-1.5" style="color:var(--ws-text)">
                    <span style="color:var(--ws-accent)">→</span> {f}
                  </li>
                {/each}
              </ul>
            </div>
          {/each}
        </div>

        <div class="rounded-xl border p-3.5" style="background:var(--ws-surface2);border-color:var(--ws-border)">
          <div class="font-semibold text-xs uppercase tracking-wider mb-2" style="color:var(--ws-muted)">{$t('fgQuickstartTitle')}</div>
          <ol class="space-y-1.5">
            {#each ($t('fgQuickstartSteps') || '').split('|').filter(Boolean) as step, i}
              <li class="text-xs flex gap-2" style="color:var(--ws-text)">
                <span class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0"
                  style="background:var(--ws-accent);color:#fff5ec">{i + 1}</span>
                {step}
              </li>
            {/each}
          </ol>
        </div>

      {:else if activeTab === 'wizard'}
        <!-- ── Setup Wizard ── -->
        <h3 class="font-bold italic text-base" style="font-family:var(--ws-serif);color:var(--ws-accent2)">{$t('fgWizardTitle')}</h3>
        <p style="color:var(--ws-muted)">{$t('fgWizardDesc')}</p>

        <div class="space-y-2">
          {#each [
            { step: 1, icon: '⚙️', key: 'fgWizardStep1' },
            { step: 2, icon: '🔗', key: 'fgWizardStep2' },
            { step: 3, icon: '🧳', key: 'fgWizardStep3' },
            { step: 4, icon: '🤖', key: 'fgWizardStep4' },
            { step: 5, icon: '🎉', key: 'fgWizardStep5' },
          ] as s}
            <div class="flex gap-3 rounded-xl border p-3" style="background:var(--ws-surface2);border-color:var(--ws-border)">
              <div class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5"
                style="background:var(--ws-accent);color:#fff5ec">{s.step}</div>
              <div>
                <div class="font-semibold text-xs mb-0.5" style="color:var(--ws-text)">{s.icon} {$t(s.key + 'Title')}</div>
                <p class="text-xs leading-relaxed" style="color:var(--ws-muted)">{$t(s.key + 'Desc')}</p>
              </div>
            </div>
          {/each}
        </div>

        <div class="rounded-xl border p-3" style="background:rgba(196,98,45,.06);border-color:var(--ws-border)">
          <p class="text-xs" style="color:var(--ws-muted)">💡 {$t('fgWizardTip')}</p>
        </div>

      {:else if activeTab === 'radar'}
        <!-- ── Preis-Radar ── -->
        <h3 class="font-bold italic text-base" style="font-family:var(--ws-serif);color:var(--ws-accent2)">{$t('fgRadarTitle')}</h3>
        <p style="color:var(--ws-muted)">{$t('fgRadarDesc')}</p>

        <div class="space-y-3">
          {#each [
            { icon: '🟠', name: 'Ryanair', key: 'fgRadarRyanair', free: true },
            { icon: '🔵', name: 'Google Flights', key: 'fgRadarGoogleFlights', free: false },
            { icon: '⛺', name: 'Homair', key: 'fgRadarHomair', free: true },
            { icon: '🏨', name: 'Booking.com', key: 'fgRadarBooking', free: false },
          ] as src}
            <div class="rounded-xl border p-3" style="background:var(--ws-surface2);border-color:var(--ws-border)">
              <div class="flex items-center justify-between mb-1">
                <span class="font-semibold text-xs">{src.icon} {src.name}</span>
                {#if src.free}
                  <span class="text-[10px] px-2 py-0.5 rounded-full font-bold" style="background:rgba(45,106,79,.15);color:var(--ws-green)">{$t('fgNoKeyNeeded')}</span>
                {:else}
                  <span class="text-[10px] px-2 py-0.5 rounded-full font-bold" style="background:rgba(196,98,45,.12);color:var(--ws-accent)">{$t('fgKeyRequired')}</span>
                {/if}
              </div>
              <p class="text-xs leading-relaxed" style="color:var(--ws-muted)">{$t(src.key)}</p>
            </div>
          {/each}
        </div>

        <div class="rounded-xl border p-3" style="background:var(--ws-surface2);border-color:var(--ws-border)">
          <div class="font-semibold text-xs mb-1.5" style="color:var(--ws-muted)">{$t('fgIataTitle')}</div>
          <p class="text-xs" style="color:var(--ws-text)">BGY = Bergamo · VIE = Wien · MUC = München · DUB = Dublin · FCO = Rom · BCN = Barcelona · LPA = Gran Canaria</p>
          <p class="text-xs mt-1" style="color:var(--ws-muted)">{$t('fgIataHint')}</p>
        </div>

      {:else if activeTab === 'trips'}
        <!-- ── Reisen & Trip Hub ── -->
        <h3 class="font-bold italic text-base" style="font-family:var(--ws-serif);color:var(--ws-accent2)">{$t('fgTripsTitle')}</h3>
        <p style="color:var(--ws-muted)">{$t('fgTripsDesc')}</p>

        <div class="space-y-3">
          <div class="rounded-xl border p-3" style="background:var(--ws-surface2);border-color:var(--ws-border)">
            <div class="font-semibold text-xs mb-1.5" style="color:var(--ws-text)">🪄 {$t('fgWanderWizzardTitle')}</div>
            <p class="text-xs leading-relaxed" style="color:var(--ws-muted)">{$t('fgWanderWizzardDesc')}</p>
          </div>
          <div class="rounded-xl border p-3" style="background:var(--ws-surface2);border-color:var(--ws-border)">
            <div class="font-semibold text-xs mb-1.5" style="color:var(--ws-text)">🗺️ {$t('fgTripHubTitle')}</div>
            <p class="text-xs leading-relaxed" style="color:var(--ws-muted)">{$t('fgTripHubDesc')}</p>
            <ul class="mt-2 space-y-1">
              {#each ($t('fgTripHubWidgets') || '').split('|').filter(Boolean) as w}
                <li class="text-xs flex gap-1.5" style="color:var(--ws-text)"><span style="color:var(--ws-accent)">→</span> {w}</li>
              {/each}
            </ul>
          </div>
          <div class="rounded-xl border p-3" style="background:var(--ws-surface2);border-color:var(--ws-border)">
            <div class="font-semibold text-xs mb-1.5" style="color:var(--ws-text)">📊 {$t('fgDashboardTitle')}</div>
            <p class="text-xs leading-relaxed" style="color:var(--ws-muted)">{$t('fgDashboardDesc')}</p>
          </div>
          <div class="rounded-xl border p-3" style="background:var(--ws-surface2);border-color:var(--ws-border)">
            <div class="font-semibold text-xs mb-1.5" style="color:var(--ws-text)">💶 {$t('fgBudgetTitle')}</div>
            <p class="text-xs leading-relaxed" style="color:var(--ws-muted)">{$t('fgBudgetDesc')}</p>
          </div>
        </div>

      {:else if activeTab === 'bridges'}
        <!-- ── Self-Hosted Bridges ── -->
        <h3 class="font-bold italic text-base" style="font-family:var(--ws-serif);color:var(--ws-accent2)">{$t('fgBridgesTitle')}</h3>
        <p style="color:var(--ws-muted)">{$t('fgBridgesDesc')}</p>

        <div class="space-y-3">
          <div class="rounded-xl border p-3" style="background:var(--ws-surface2);border-color:var(--ws-border)">
            <div class="font-semibold text-xs mb-1.5" style="color:var(--ws-text)">📡 Dawarich</div>
            <p class="text-xs leading-relaxed" style="color:var(--ws-muted)">{$t('fgDawarichDesc')}</p>
            <div class="mt-2 text-xs font-semibold" style="color:var(--ws-text)">{$t('fgDawarichSetup')}</div>
            <ol class="mt-1 space-y-0.5 list-decimal list-inside text-xs" style="color:var(--ws-muted)">
              {#each ($t('fgDawarichSteps') || '').split('|').filter(Boolean) as s}
                <li>{s}</li>
              {/each}
            </ol>
          </div>
          <div class="rounded-xl border p-3" style="background:var(--ws-surface2);border-color:var(--ws-border)">
            <div class="font-semibold text-xs mb-1.5" style="color:var(--ws-text)">📸 Immich</div>
            <p class="text-xs leading-relaxed" style="color:var(--ws-muted)">{$t('fgImmichDesc')}</p>
            <div class="mt-2 text-xs font-semibold" style="color:var(--ws-text)">{$t('fgImmichSetup')}</div>
            <ol class="mt-1 space-y-0.5 list-decimal list-inside text-xs" style="color:var(--ws-muted)">
              {#each ($t('fgImmichSteps') || '').split('|').filter(Boolean) as s}
                <li>{s}</li>
              {/each}
            </ol>
          </div>
          <div class="rounded-xl border p-3" style="background:var(--ws-surface2);border-color:var(--ws-border)">
            <div class="font-semibold text-xs mb-1.5" style="color:var(--ws-text)">💳 ActualBudget</div>
            <p class="text-xs leading-relaxed" style="color:var(--ws-muted)">{$t('fgActualDesc')}</p>
            <div class="mt-2 text-xs font-semibold" style="color:var(--ws-text)">{$t('fgActualSetup')}</div>
            <ol class="mt-1 space-y-0.5 list-decimal list-inside text-xs" style="color:var(--ws-muted)">
              {#each ($t('fgActualSteps') || '').split('|').filter(Boolean) as s}
                <li>{s}</li>
              {/each}
            </ol>
          </div>
        </div>

      {:else if activeTab === 'apis'}
        <!-- ── API Keys ── -->
        <h3 class="font-bold italic text-base" style="font-family:var(--ws-serif);color:var(--ws-accent2)">{$t('fgApisTitle')}</h3>
        <p style="color:var(--ws-muted)">{$t('fgApisDesc')}</p>

        <div class="space-y-3">
          {#each [
            { name: 'SerpAPI',        url: 'serpapi.com/manage-api-key', free: '100 {$t("fgSearchesMonth")}', key: 'fgSerpApiDesc' },
            { name: 'Google Gemini',  url: 'aistudio.google.com/app/apikey', free: $t('fgFree'), key: 'fgGeminiDesc' },
            { name: 'OpenAI',         url: 'platform.openai.com/api-keys', free: '~$0.00015/1k tokens', key: 'fgOpenAiDesc' },
          ] as api}
            <div class="rounded-xl border p-3" style="background:var(--ws-surface2);border-color:var(--ws-border)">
              <div class="flex justify-between items-start mb-1">
                <span class="font-semibold text-xs">{api.name}</span>
                <span class="text-[10px] px-1.5 py-0.5 rounded font-mono" style="background:rgba(45,106,79,.15);color:var(--ws-green)">{api.free}</span>
              </div>
              <p class="text-xs" style="color:var(--ws-muted)">{$t(api.key)}</p>
              <div class="text-xs mt-1 font-mono" style="color:var(--ws-accent2)">→ {api.url}</div>
            </div>
          {/each}
          <div class="rounded-xl border p-3" style="background:rgba(196,98,45,.06);border-color:var(--ws-border)">
            <p class="text-xs" style="color:var(--ws-muted)">💡 {$t('fgApisTip')}</p>
          </div>
        </div>
      {/if}

    </div>
  </div>
{/if}

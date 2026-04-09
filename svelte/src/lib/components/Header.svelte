<script>
  import { isDark, lang, appVersion } from '$lib/stores.js';
  import { setLang, allLocales, localeLabels } from '$lib/i18n.js';
  let { onFieldGuide, onSettings, onToggleDark } = $props();

  // Verfügbare Sprachen dynamisch aus allLocales ableiten
  // Neue Sprache: JSON in locales/ + Import in i18n.js → erscheint hier automatisch
  const availableLangs = Object.keys(allLocales);
</script>

<header class="flex items-center justify-between px-4 h-14 border-b shrink-0"
  style="background:var(--ws-surface);border-color:var(--ws-border)">

  <div class="flex items-center gap-2">
    <span class="text-xl">🧭</span>
    <span class="font-semibold tracking-tight" style="color:var(--ws-accent)">WanderSuite</span>
    <!-- BETA badge — only in beta branch -->
    <span style="font-size:0.6rem;font-weight:700;letter-spacing:0.05em;padding:2px 6px;border-radius:4px;background:var(--ws-accent);color:#fff;opacity:0.85;vertical-align:middle">
      BETA
    </span>
    {#if $appVersion}
      <span style="font-size:0.6rem;font-family:monospace;color:var(--ws-muted);margin-left:2px">
        {$appVersion}
      </span>
    {/if}
  </div>

  <div class="flex items-center gap-2">
    <!-- Sprachauswahl: dynamisches <select> aus allLocales -->
    <select
      value={$lang}
      onchange={(e) => setLang(e.currentTarget.value)}
      class="text-xs font-bold rounded-lg px-2 py-1.5 border cursor-pointer transition-colors"
      style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-accent);outline:none;appearance:none;-webkit-appearance:none;padding-right:1.5rem;background-image:url('data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%228%22 height=%225%22 viewBox=%220 0 8 5%22><path d=%22M0 0l4 5 4-5z%22 fill=%22%23999%22/></svg>');background-repeat:no-repeat;background-position:right 0.4rem center"
      title="Sprache wählen">
      {#each availableLangs as l}
        <option value={l}>{localeLabels[l] ?? l.toUpperCase()}</option>
      {/each}
    </select>

    <button onclick={onToggleDark}
      class="p-2 rounded-lg hover:opacity-70 transition-opacity text-base" title="Dark Mode">
      {$isDark ? '☀️' : '🌙'}
    </button>
    <button onclick={onFieldGuide}
      class="p-2 rounded-lg hover:opacity-70 transition-opacity text-base" title="Feldführer">
      📖
    </button>
    <button onclick={onSettings}
      class="p-2 rounded-lg hover:opacity-70 transition-opacity text-base" title="Einstellungen">
      ⚙️
    </button>
  </div>
</header>

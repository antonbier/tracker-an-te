<script>
  import { isDark, lang, appVersion } from '$lib/stores.js';
  import { setLang, allLocales, localeLabels } from '$lib/i18n.js';
  let { onFieldGuide, onSettings, onToggleDark } = $props();

  // Verfügbare Sprachen dynamisch aus allLocales ableiten
  const availableLangs = Object.keys(allLocales);

  // select-Stil als JS-Konstante — verhindert Parser-Fehler durch
  // spitze Klammern (z.B. SVG-Data-URIs) in style=""-HTML-Attributen
  const selectStyle = [
    'background:var(--ws-surface2)',
    'border-color:var(--ws-border)',
    'color:var(--ws-accent)',
    'outline:none',
    'appearance:none',
    '-webkit-appearance:none',
    'padding:0.25rem 0.5rem',
    'border-radius:0.5rem',
    'border-width:1px',
    'border-style:solid',
    'font-size:0.75rem',
    'font-weight:700',
    'cursor:pointer',
  ].join(';');
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
      style={selectStyle}
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

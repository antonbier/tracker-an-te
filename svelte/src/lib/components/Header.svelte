<script>
  import { isDark, lang, appVersion } from '$lib/stores.js';
  import { setLang, allLocales } from '$lib/i18n.js';
  let { onFieldGuide, onSettings, onToggleDark } = $props();
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
    <!-- Lang switcher — dynamisch aus allLocales -->
    <div class="flex gap-0.5 rounded-lg p-0.5 border text-xs font-bold"
      style="background:var(--ws-surface2);border-color:var(--ws-border)">
      {#each Object.keys(allLocales) as l}
        <button
          onclick={() => setLang(l)}
          class="px-2 py-1 rounded-md transition-all uppercase"
          style={$lang === l
            ? 'background:var(--ws-surface);color:var(--ws-accent);box-shadow:0 1px 3px rgba(0,0,0,.1)'
            : 'color:var(--ws-muted)'}
        >{l}</button>
      {/each}
    </div>

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

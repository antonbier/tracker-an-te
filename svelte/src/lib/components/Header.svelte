<script>
  import { isDark, lang } from '$lib/stores.js';
  import { setLang } from '$lib/i18n.js';
  let { onFieldGuide, onSettings, onToggleDark } = $props();
</script>

<header class="flex items-center justify-between px-4 h-14 border-b shrink-0"
  style="background:var(--ws-surface);border-color:var(--ws-border)">

  <div class="flex items-center gap-2">
    <span class="text-xl">🧭</span>
    <span class="font-semibold tracking-tight" style="color:var(--ws-accent)">WanderSuite</span>
  </div>

  <div class="flex items-center gap-2">
    <!-- Lang switcher -->
    <div class="flex gap-0.5 rounded-lg p-0.5 border text-xs font-bold"
      style="background:var(--ws-surface2);border-color:var(--ws-border)">
      {#each ['de','it','en'] as l}
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

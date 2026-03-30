<script>
  import { isDark } from '$lib/stores.js';

  let { onFieldGuide, onSettings, onToggleDark } = $props();
</script>

<header class="flex items-center justify-between px-4 h-14 border-b shrink-0"
  style="background:var(--ws-surface);border-color:var(--ws-border)">

  <div class="flex items-center gap-2">
    <span class="text-xl">🧭</span>
    <span class="font-semibold tracking-tight" style="color:var(--ws-accent)">WanderSuite</span>
  </div>

  <div class="flex items-center gap-1">
    <button
      onclick={onToggleDark}
      class="p-2 rounded-lg hover:opacity-70 transition-opacity"
      title="Dark Mode umschalten"
    >
      {$isDark ? '☀️' : '🌙'}
    </button>
    <button
      onclick={onFieldGuide}
      class="p-2 rounded-lg hover:opacity-70 transition-opacity"
      title="Hilfe"
    >
      📖
    </button>
    <button
      onclick={onSettings}
      class="p-2 rounded-lg hover:opacity-70 transition-opacity"
      title="Einstellungen"
    >
      ⚙️
    </button>
  </div>
</header>

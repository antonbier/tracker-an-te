<script>
  import { api } from '$lib/api.js';
  import { t } from '$lib/i18n.js';
  import { apiUrl } from '$lib/stores.js';
  import { toast } from '$lib/toast.js';

  let query      = $state('');
  let provider   = $state('gemini');
  let results    = $state([]);
  let loading    = $state(false);
  let geminiKey  = $state(typeof localStorage !== 'undefined' ? localStorage.getItem('s-geminiKey') || '' : '');
  let openaiKey  = $state(typeof localStorage !== 'undefined' ? localStorage.getItem('s-openaiKey') || '' : '');

  async function generate() {
    if (!query.trim()) { toast('Bitte beschreibe was du suchst', 'warning'); return; }
    const key = provider === 'openai' ? openaiKey : geminiKey;
    loading = true; results = [];
    try {
      const data = await api('/api/discover', {
        method: 'POST',
        body: JSON.stringify({ query, provider, api_key: key || undefined, lang: 'de' }),
      });
      if (data.error) throw new Error(data.error);
      results = data.recommendations || [];
    } catch(e) { toast(e.message, 'error'); }
    loading = false;
  }
</script>

<div class="space-y-4">
  <h1 class="text-2xl font-bold italic" style="font-family:var(--ws-serif)">{$t('discoverTitle')}</h1>

  <div class="rounded-xl p-4 border space-y-3" style="background:var(--ws-surface);border-color:var(--ws-border)">
    <div class="grid grid-cols-2 gap-2">
      <div>
        <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('discoverProvider')}</label>
        <select bind:value={provider}
          class="w-full mt-1 px-3 py-2 rounded-xl border text-sm"
          style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)">
          <option value="gemini">Google Gemini</option>
          <option value="openai">OpenAI</option>
        </select>
      </div>
    </div>

    <div>
      <label class="text-xs font-bold uppercase tracking-wider" style="color:var(--ws-muted)">{$t('discoverQuery')}</label>
      <textarea
        bind:value={query}
        placeholder={$t('discoverPlaceholder')}
        rows="3"
        class="w-full mt-1 px-3 py-2 rounded-xl border text-sm resize-none"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"
      ></textarea>
    </div>

    <button
      onclick={generate}
      disabled={loading}
      class="w-full py-2.5 rounded-xl font-semibold text-sm transition-opacity hover:opacity-80 disabled:opacity-50"
      style="background:linear-gradient(135deg,var(--ws-accent),#b84928);color:#fff5ec"
    >
      {loading ? $t('discoverLoading') : $t('discoverBtn')}
    </button>
  </div>

  {#if results.length > 0}
    <div class="space-y-3">
      {#each results as r}
        <div class="rounded-xl p-4 border" style="background:var(--ws-surface);border-color:var(--ws-border)">
          <div class="font-bold text-base italic mb-1" style="font-family:var(--ws-serif);color:var(--ws-text)">
            🌍 {r.destination}
          </div>
          <p class="text-sm mb-2" style="color:var(--ws-muted)">{r.why}</p>
          <div class="flex flex-wrap gap-2 text-xs font-mono">
            <span style="color:var(--ws-accent2)">📅 {r.best_time}</span>
            <span style="color:var(--ws-green)">💶 {r.estimated_budget}</span>
            <span style="color:var(--ws-text)">⭐ {r.highlight}</span>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

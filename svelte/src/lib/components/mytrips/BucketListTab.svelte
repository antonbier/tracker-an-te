<script>
  import { bucketlist } from '$lib/stores.js';
  import { t } from '$lib/i18n.js';

  let { onadd, ontoggle, onremove } = $props();

  // Modal state
  let modalOpen  = $state(false);
  let bucketItem = $state('');
  let bucketDest = $state('');

  function openModal()  { bucketItem = ''; bucketDest = ''; modalOpen = true; }
  function closeModal() { modalOpen = false; }

  function handleAdd() {
    if (!bucketItem.trim()) return;
    onadd(bucketItem.trim(), bucketDest.trim());
    closeModal();
  }

  const doneCount  = $derived($bucketlist.filter(x => x.done).length);
  const totalCount = $derived($bucketlist.length);
</script>

<!-- ── Add modal ──────────────────────────────────────────────────────────── -->
{#if modalOpen}
  <div class="fixed inset-0 z-50 flex items-center justify-center"
    style="background:rgba(0,0,0,.45);backdrop-filter:blur(4px)"
    role="dialog" aria-modal="true">
    <div class="w-full max-w-sm mx-4 rounded-2xl shadow-2xl border p-6 space-y-4"
      style="background:var(--ws-surface);border-color:var(--ws-border)">
      <h3 class="font-bold text-base" style="color:var(--ws-text)">{$t('bucketModalTitle')}</h3>
      <input
        bind:value={bucketItem}
        placeholder={$t('bucketModalItem')}
        onkeydown={(e) => e.key === 'Enter' && handleAdd()}
        class="w-full px-3 py-2.5 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ws-accent)]"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      <input
        bind:value={bucketDest}
        placeholder={$t('bucketModalDest')}
        onkeydown={(e) => e.key === 'Enter' && handleAdd()}
        class="w-full px-3 py-2.5 rounded-xl border text-sm focus:outline-none"
        style="background:var(--ws-surface2);border-color:var(--ws-border);color:var(--ws-text)"/>
      <div class="flex gap-3">
        <button onclick={closeModal}
          class="flex-1 py-2.5 rounded-xl border text-sm font-semibold hover:opacity-70 transition-opacity"
          style="border-color:var(--ws-border);color:var(--ws-muted)">{$t('bucketModalCancel')}</button>
        <button onclick={handleAdd} disabled={!bucketItem.trim()}
          class="flex-1 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-40 transition-opacity"
          style="background:var(--ws-accent);color:#fff5ec">{$t('bucketModalSave')}</button>
      </div>
    </div>
  </div>
{/if}

<!-- ── Header with action button ──────────────────────────────────────────── -->
<div class="flex items-center justify-between mb-4">
  <div>
    {#if totalCount > 0}
      <span class="text-xs" style="color:var(--ws-muted)">{doneCount}/{totalCount}{$t('bucketDone')}</span>
    {/if}
  </div>
  <button onclick={openModal}
    class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all hover:opacity-85 active:scale-[.98]"
    style="background:var(--ws-accent);color:#fff5ec">
    {$t('bucketAddBtn')}
  </button>
</div>

<!-- ── Grid ──────────────────────────────────────────────────────────────── -->
{#if totalCount === 0}
  <div class="rounded-2xl border p-12 text-center space-y-3"
    style="background:var(--ws-surface2);border-color:var(--ws-border)">
    <div class="text-5xl">🌍</div>
    <p class="text-sm" style="color:var(--ws-muted)">{$t('bucketEmpty')}</p>
    <button onclick={openModal}
      class="px-5 py-2 rounded-xl text-sm font-semibold"
      style="background:var(--ws-accent);color:#fff5ec">{$t('bucketAddBtn')}</button>
  </div>
{:else}
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
    {#each $bucketlist as item, i}
      <div
        class="group relative rounded-2xl border overflow-hidden transition-all hover:shadow-md"
        style="background:var(--ws-surface2);border-color:var(--ws-border);{item.done ? 'opacity:0.55' : ''}">

        <!-- Hero strip -->
        <div class="h-2 w-full"
          style="background:{item.done
            ? 'var(--ws-green,#2d6a4f)'
            : 'linear-gradient(90deg,var(--ws-accent),#b84928)'}">
        </div>

        <div class="p-4">
          <!-- Top row: icon + actions -->
          <div class="flex items-start justify-between mb-2">
            <span class="text-2xl">🌟</span>
            <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <!-- Toggle done -->
              <button onclick={() => ontoggle(i)}
                class="w-7 h-7 rounded-full border-2 flex items-center justify-center text-xs transition-all"
                style="border-color:{item.done ? 'var(--ws-green,#2d6a4f)' : 'var(--ws-border)'};
                       background:{item.done ? 'var(--ws-green,#2d6a4f)' : 'transparent'};
                       color:#fff">
                {item.done ? '✓' : ''}
              </button>
              <!-- Remove -->
              <button onclick={() => onremove(i)}
                class="w-7 h-7 rounded-full border flex items-center justify-center text-xs transition-all hover:border-red-300"
                style="border-color:var(--ws-border);color:var(--ws-muted)">✕</button>
            </div>
          </div>

          <!-- Title -->
          <div class="text-sm font-semibold leading-snug"
            style="font-family:var(--ws-serif);color:var(--ws-text);{item.done ? 'text-decoration:line-through' : ''}">
            {item.item}
          </div>

          {#if item.dest}
            <div class="text-xs mt-1" style="color:var(--ws-muted)">📍 {item.dest}</div>
          {/if}
          <div class="text-xs mt-2 font-mono" style="color:var(--ws-muted)">{item.created}</div>
        </div>
      </div>
    {/each}
  </div>
{/if}

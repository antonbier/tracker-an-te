<script>
  import { bucketlist } from '$lib/stores.js';
  import { t } from '$lib/i18n.js';

  let {
    bucketItem = $bindable(),
    bucketDest = $bindable(),
    card,
    inp,
    btn,
    onadd,
    ontoggle,
    onremove,
  } = $props();
</script>

<div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
  <div class="lg:col-span-1">
    <div class={card}>
      <h3 class="text-sm font-semibold mb-3">🌟 {$t('mytripsBucketAdd')}</h3>
      <div class="space-y-2.5">
        <input bind:value={bucketItem} placeholder={$t('mytripsBucketItemPlaceholder')} class={inp} />
        <input bind:value={bucketDest} placeholder={$t('mytripsBucketDestPlaceholder')} class={inp} />
        <button onclick={onadd} class={btn} style="background:linear-gradient(135deg,#c4622d,#b84928)">{$t('mytripsAddBtn')}</button>
      </div>
      {#if $bucketlist.length > 0}
        <div class="mt-4 pt-4 border-t text-xs" style="border-color:var(--ws-border);color:var(--ws-muted)">
          {$bucketlist.filter(x=>x.done).length} / {$bucketlist.length} erledigt
        </div>
      {/if}
    </div>
  </div>

  <div class="lg:col-span-2">
    {#if $bucketlist.length === 0}
      <div class="{card} text-center py-14">
        <div class="text-5xl mb-3">🌍</div>
        <p class="text-sm" style="color:var(--ws-muted)">{$t('mytripsBucketEmpty')}</p>
      </div>
    {:else}
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {#each $bucketlist as item, i}
          <div class="group relative {card} transition-all hover:shadow-md" class:opacity-50={item.done}>
            <button onclick={() => ontoggle(i)}
              class="absolute top-4 right-4 w-6 h-6 rounded-full border-2 flex items-center justify-center text-xs transition-all"
              style="border-color:{item.done?'#059669':'#d1d5db'};background:{item.done?'#059669':'transparent'};color:white">
              {item.done?'✓':''}
            </button>
            <button onclick={() => onremove(i)}
              class="absolute top-4 right-12 w-6 h-6 rounded-full border flex items-center justify-center text-xs
                     hover:text-red-500 hover:border-red-200 opacity-0 group-hover:opacity-100 transition-all">✕</button>
            <div class="text-2xl mb-2">🌟</div>
            <div class="text-sm font-semibold pr-14" style="font-family:var(--ws-serif);color:var(--ws-text)"
              class:line-through={item.done}>{item.item}</div>
            {#if item.dest}
              <div class="text-xs mt-1" style="color:var(--ws-muted)">📍 {item.dest}</div>
            {/if}
            <div class="text-xs mt-2 font-mono">{item.created}</div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>

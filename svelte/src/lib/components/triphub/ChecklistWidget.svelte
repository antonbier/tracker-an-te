<script>
  /**
   * ChecklistWidget.svelte
   * Trip to-do checklist. Regen button available in ALL phases.
   */
  import { t } from '$lib/i18n.js';

  let {
    trip         = null,
    todos        = $bindable([]),
    phase        = 'planning',
    regenLoading = false,
    onregenerate = () => {},
    ontoggle     = () => {},
    onadd        = () => {},
    ondelete     = () => {},
  } = $props();

  let newTask = $state('');

  const isArchived = $derived(phase === 'archived');
  const donePct    = $derived(todos.length ? Math.round(todos.filter(t => t.is_done).length / todos.length * 100) : 0);

  function catIcon(cat) {
    return { booking: '🎫', documents: '📄', packing: '🧳', general: '✅' }[cat] || '✅';
  }

  function handleAdd() {
    if (!newTask.trim()) return;
    onadd(newTask.trim());
    newTask = '';
  }
</script>

<div class="rounded-2xl border overflow-hidden" style="border-color:var(--ws-border)">
  <!-- Header -->
  <div class="flex items-center justify-between px-5 py-3.5 border-b"
    style="background:var(--ws-surface2);border-color:var(--ws-border)">
    <div class="flex items-center gap-2">
      <span class="font-bold text-sm" style="color:var(--ws-text)">{$t('tripHubTodos')}</span>
      {#if todos.length > 0}
        <span class="text-xs px-2 py-0.5 rounded-full font-semibold"
          style="background:color-mix(in srgb,var(--ws-accent) 15%,var(--ws-surface));color:var(--ws-accent)">
          {todos.filter(t => t.is_done).length}/{todos.length}
        </span>
      {/if}
    </div>
    <div class="flex items-center gap-2">
      {#if todos.length > 0}
        <div class="w-24 h-1.5 rounded-full overflow-hidden" style="background:var(--ws-border)">
          <div class="h-full rounded-full transition-all duration-500"
            style="width:{donePct}%;background:{donePct === 100 ? 'var(--ws-green)' : 'var(--ws-accent)'}"></div>
        </div>
        <span class="text-xs font-mono" style="color:var(--ws-muted)">{donePct}%</span>
      {/if}
      <!-- FIX: Regen button visible in ALL phases -->
      <button onclick={onregenerate} disabled={regenLoading}
        class="text-xs px-2 py-1 rounded-lg border transition-all hover:opacity-80 disabled:opacity-40"
        style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-muted)">
        {regenLoading ? '⏳' : ($t('hubRegenTodos') || '🔄')}
      </button>
    </div>
  </div>

  <!-- List -->
  <div class="divide-y" style="border-color:var(--ws-border)">
    {#if todos.length === 0}
      <div class="px-5 py-8 text-center text-sm" style="color:var(--ws-muted)">{$t('tripHubNoTodos')}</div>
    {:else}
      {#each todos as todo}
        <div class="flex items-center gap-3 px-5 py-3"
          style="background:var(--ws-surface);{todo.is_done ? 'opacity:0.5' : ''}">
          <button onclick={() => !isArchived && ontoggle(todo)}
            class="w-5 h-5 rounded-md border-2 flex items-center justify-center shrink-0 transition-all {isArchived ? 'cursor-default' : ''}"
            style={todo.is_done ? 'background:var(--ws-green);border-color:var(--ws-green)' : 'background:transparent;border-color:var(--ws-border)'}>
            {#if todo.is_done}<span class="text-[10px] text-white font-bold">✓</span>{/if}
          </button>
          <span class="text-base shrink-0">{catIcon(todo.category)}</span>
          <span class="flex-1 text-sm" style="color:var(--ws-text);{todo.is_done ? 'text-decoration:line-through' : ''}">{todo.task}</span>
          {#if !isArchived}
            <button onclick={() => ondelete(todo)} class="text-sm shrink-0 px-1 hover:opacity-70" style="color:var(--ws-muted)">✕</button>
          {/if}
        </div>
      {/each}
    {/if}
  </div>

  <!-- Add row (non-archived only) -->
  {#if !isArchived}
    <div class="flex items-center gap-2 px-4 py-3 border-t"
      style="border-color:var(--ws-border);background:var(--ws-surface2)">
      <input bind:value={newTask} placeholder={$t('tripHubTodoPlaceholder')}
        onkeydown={(e) => e.key === 'Enter' && handleAdd()}
        class="flex-1 px-3 py-1.5 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ws-accent)] bg-transparent"
        style="border-color:var(--ws-border);color:var(--ws-text)"/>
      <button onclick={handleAdd} disabled={!newTask.trim()}
        class="px-3 py-1.5 rounded-xl text-xs font-bold disabled:opacity-40"
        style="background:var(--ws-accent);color:#fff5ec">+</button>
    </div>
  {/if}
</div>

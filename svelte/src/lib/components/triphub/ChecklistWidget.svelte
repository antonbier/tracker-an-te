<script>
  /**
   * ChecklistWidget.svelte
   * Trip to-do checklist with due_date support.
   * Regen button available in ALL phases.
   */
  import { t } from '$lib/i18n.js';
  import { api } from '$lib/api.js';
  import { toast } from '$lib/toast.js';

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

  let newTask    = $state('');
  let newDueDate = $state('');
  let duePicker  = $state(null);   // todo.id whose picker is open

  const isArchived = $derived(phase === 'archived');
  const today      = new Date().toISOString().slice(0, 10);
  const donePct    = $derived(
    todos.length ? Math.round(todos.filter(t => t.is_done).length / todos.length * 100) : 0
  );

  function catIcon(cat) {
    return { booking: '🎫', documents: '📄', packing: '🧳', general: '✅' }[cat] || '✅';
  }

  function isOverdue(todo) {
    return !todo.is_done && todo.due_date && todo.due_date < today;
  }

  function isDueToday(todo) {
    return !todo.is_done && todo.due_date === today;
  }

  function handleAdd() {
    if (!newTask.trim()) return;
    onadd(newTask.trim(), newDueDate || null);
    newTask = '';
    newDueDate = '';
  }

  async function saveDueDate(todo, val) {
    if (!trip?.id) return;
    const due = val || null;
    try {
      await api(`/api/ws-trips/${trip.id}/todos/${todo.id}/due`, {
        method: 'PATCH',
        body: JSON.stringify({ due_date: due }),
      });
      // Update local todos array reactively
      todos = todos.map(t => t.id === todo.id ? { ...t, due_date: due } : t);
      toast(due ? `📅 Fälligkeit gesetzt` : 'Fälligkeit entfernt', 'success');
    } catch (e) { toast(e.message || 'Fehler', 'error'); }
    duePicker = null;
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
        <!-- overdue badge -->
        {@const overdueCount = todos.filter(t => isOverdue(t)).length}
        {#if overdueCount > 0}
          <span class="text-xs px-2 py-0.5 rounded-full font-semibold"
            style="background:rgba(239,68,68,.15);color:#ef4444">
            ⚠️ {overdueCount} überfällig
          </span>
        {/if}
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
      <!-- Regen button — ALL phases -->
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
      {#each todos as todo (todo.id)}
        {@const overdue   = isOverdue(todo)}
        {@const dueToday  = isDueToday(todo)}
        <div class="flex items-center gap-3 px-5 py-3"
          style="background:{overdue ? 'color-mix(in srgb,#ef4444 6%,var(--ws-surface))' : 'var(--ws-surface)'};{todo.is_done ? 'opacity:0.5' : ''}">

          <!-- Checkbox -->
          <button onclick={() => !isArchived && ontoggle(todo)}
            class="w-5 h-5 rounded-md border-2 flex items-center justify-center shrink-0 transition-all {isArchived ? 'cursor-default' : ''}"
            style={todo.is_done ? 'background:var(--ws-green);border-color:var(--ws-green)' : 'background:transparent;border-color:var(--ws-border)'}>
            {#if todo.is_done}<span class="text-[10px] text-white font-bold">✓</span>{/if}
          </button>

          <!-- Category icon -->
          <span class="text-base shrink-0">{catIcon(todo.category)}</span>

          <!-- Task + due date -->
          <div class="flex-1 min-w-0">
            <span class="text-sm block" style="color:var(--ws-text);{todo.is_done ? 'text-decoration:line-through' : ''}">{todo.task}</span>
            {#if todo.due_date}
              <span class="text-[10px] font-semibold"
                style="color:{overdue ? '#ef4444' : dueToday ? 'var(--ws-accent)' : 'var(--ws-muted)'}">
                {overdue ? '⚠️ überfällig · ' : dueToday ? '📅 heute · ' : '📅 '}{todo.due_date}
              </span>
            {/if}
          </div>

          <!-- Due date picker (non-archived) -->
          {#if !isArchived}
            <div class="relative shrink-0">
              {#if duePicker === todo.id}
                <!-- inline date input -->
                <input type="date"
                  value={todo.due_date || ''}
                  min={today}
                  onchange={(e) => saveDueDate(todo, e.target.value)}
                  onblur={() => duePicker = null}
                  class="text-xs px-2 py-0.5 rounded-lg border focus:outline-none"
                  style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text);width:130px"
                  autofocus />
              {:else}
                <button
                  onclick={() => duePicker = todo.id}
                  title="Fälligkeit setzen"
                  class="text-sm px-1 hover:opacity-70 transition-opacity"
                  style="color:{todo.due_date ? (overdue ? '#ef4444' : 'var(--ws-accent)') : 'var(--ws-muted)'}">
                  📅
                </button>
              {/if}
            </div>
            <!-- Delete -->
            <button onclick={() => ondelete(todo)} class="text-sm shrink-0 px-1 hover:opacity-70" style="color:var(--ws-muted)">✕</button>
          {/if}
        </div>
      {/each}
    {/if}
  </div>

  <!-- Add row (non-archived) -->
  {#if !isArchived}
    <div class="flex items-center gap-2 px-4 py-3 border-t"
      style="border-color:var(--ws-border);background:var(--ws-surface2)">
      <input bind:value={newTask}
        placeholder={$t('tripHubTodoPlaceholder')}
        onkeydown={(e) => e.key === 'Enter' && handleAdd()}
        class="flex-1 px-3 py-1.5 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ws-accent)] bg-transparent"
        style="border-color:var(--ws-border);color:var(--ws-text)"/>
      <!-- optional due date on new task -->
      <input type="date"
        bind:value={newDueDate}
        min={today}
        title="Fälligkeit (optional)"
        class="px-2 py-1.5 rounded-xl border text-xs focus:outline-none"
        style="background:var(--ws-surface);border-color:var(--ws-border);color:var(--ws-text);width:130px"/>
      <button onclick={handleAdd} disabled={!newTask.trim()}
        class="px-3 py-1.5 rounded-xl text-xs font-bold disabled:opacity-40"
        style="background:var(--ws-accent);color:#fff5ec">+</button>
    </div>
  {/if}
</div>

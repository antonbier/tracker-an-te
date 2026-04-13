<script>
  import { onMount } from 'svelte';
  import { t } from '$lib/i18n.js';
  import { api } from '$lib/api.js';
  import { toast } from '$lib/toast.js';
  import { currentPage, activeWsTripId } from '$lib/stores.js';

  // ── State ──────────────────────────────────────────────────────────────────
  let trip    = $state(null);
  let todos   = $state([]);
  let loading = $state(true);
  let newTask = $state('');
  let addingTodo = $state(false);

  // ── Load trip ──────────────────────────────────────────────────────────────
  onMount(async () => {
    const id = $activeWsTripId;
    if (!id) { loading = false; return; }
    try {
      const res = await api(`/api/ws-trips/${id}`);
      trip  = res;
      todos = res.todos || [];
    } catch (e) {
      toast('Trip konnte nicht geladen werden', 'error');
    }
    loading = false;
  });

  // ── Countdown ──────────────────────────────────────────────────────────────
  const countdown = $derived.by(() => {
    if (!trip?.start_date) return null;
    const diff = Math.ceil((new Date(trip.start_date) - new Date()) / 86400000);
    if (diff === 0) return $t('tripHubToday');
    if (diff === 1) return $t('tripHubTomorrow');
    if (diff > 0)   return $t('tripHubCountdown').replace('{n}', diff);
    return null;
  });

  // ── Status badge ───────────────────────────────────────────────────────────
  const statusLabel = $derived.by(() => {
    if (!trip) return '';
    return { planning: $t('tripHubStatusPlanning'), booked: $t('tripHubStatusBooked'), completed: $t('tripHubStatusDone') }[trip.status] || trip.status;
  });
  const statusColor = $derived.by(() => {
    return { planning: 'var(--ws-accent)', booked: 'var(--ws-green)', completed: 'var(--ws-muted)' }[trip?.status] || 'var(--ws-muted)';
  });

  // ── Todo actions ───────────────────────────────────────────────────────────
  async function toggleTodo(todo) {
    try {
      await api(`/api/ws-trips/${trip.id}/todos/${todo.id}/toggle`, { method: 'PATCH' });
      todos = todos.map(t => t.id === todo.id ? { ...t, is_done: t.is_done ? 0 : 1 } : t);
    } catch { toast('Fehler', 'error'); }
  }

  async function addTodo() {
    if (!newTask.trim() || addingTodo) return;
    addingTodo = true;
    try {
      await api(`/api/ws-trips/${trip.id}/todos`, { method: 'POST', body: JSON.stringify({ task: newTask.trim(), category: 'general' }) });
      todos = [...todos, { id: Date.now(), task: newTask.trim(), category: 'general', is_done: 0 }];
      newTask = '';
    } catch { toast('Fehler', 'error'); }
    addingTodo = false;
  }

  async function deleteTodo(todo) {
    try {
      await api(`/api/ws-trips/${trip.id}/todos/${todo.id}`, { method: 'DELETE' });
      todos = todos.filter(t => t.id !== todo.id);
    } catch { toast('Fehler', 'error'); }
  }

  // ── PriceRadar navigation ──────────────────────────────────────────────────
  function goSearch(type) {
    currentPage.set('priceradar');
  }

  // ── Hero gradient by travel_mode ───────────────────────────────────────────
  const heroBg = $derived.by(() => {
    if (!trip) return 'linear-gradient(135deg,#1e293b,#374151)';
    return trip.travel_mode === 'car'
      ? 'linear-gradient(135deg,#1a3a2a 0%,#2d6a4f 60%,#1a4a3a 100%)'
      : 'linear-gradient(135deg,#1a2a4a 0%,var(--ws-accent) 70%,#b84928 100%)';
  });

  // ── Category icon ──────────────────────────────────────────────────────────
  function catIcon(cat) {
    return { booking: '🎫', documents: '📄', packing: '🧳', general: '✅' }[cat] || '✅';
  }

  const donePct = $derived(todos.length ? Math.round(todos.filter(t => t.is_done).length / todos.length * 100) : 0);
</script>

<div class="max-w-2xl mx-auto space-y-5 pb-10">

  <!-- ── Back button ──────────────────────────────────────────────────────── -->
  <button onclick={() => currentPage.set('home')}
    class="flex items-center gap-1.5 text-sm font-semibold hover:opacity-70 transition-opacity"
    style="color:var(--ws-muted)">
    {$t('tripHubBack')}
  </button>

  {#if loading}
    <!-- Skeleton -->
    <div class="rounded-2xl animate-pulse h-52" style="background:var(--ws-surface2)"></div>
    <div class="rounded-2xl animate-pulse h-32" style="background:var(--ws-surface2)"></div>
  {:else if !trip}
    <div class="rounded-2xl p-10 text-center" style="background:var(--ws-surface2)">
      <p class="text-4xl mb-3">🗺️</p>
      <p class="font-semibold" style="color:var(--ws-text)">Kein Trip gefunden</p>
      <button onclick={() => currentPage.set('home')} class="mt-4 text-sm" style="color:var(--ws-accent)">Zurück</button>
    </div>
  {:else}

    <!-- ── Hero Banner ──────────────────────────────────────────────────────── -->
    <div class="relative rounded-2xl overflow-hidden" style="min-height:200px;background:{heroBg}">
      <!-- Texture -->
      <div class="absolute inset-0 opacity-10" style="background-image:radial-gradient(circle at 20% 80%,rgba(255,255,255,.2) 0%,transparent 50%)"></div>

      <div class="relative z-10 p-6 flex flex-col justify-between" style="min-height:200px">
        <!-- Top: status + countdown -->
        <div class="flex items-start justify-between">
          <div class="flex flex-col gap-2">
            <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold"
              style="background:rgba(255,255,255,.15);color:#fff;backdrop-filter:blur(8px)">
              <span class="w-1.5 h-1.5 rounded-full" style="background:{statusColor}"></span>
              {statusLabel}
            </span>
            {#if countdown}
              <span class="text-sm font-semibold" style="color:rgba(255,255,255,.85)">{countdown}</span>
            {/if}
          </div>
          <!-- Travel mode badge -->
          <span class="text-2xl">{trip.travel_mode === 'car' ? '🚗' : '✈️'}</span>
        </div>

        <!-- Bottom: title + dates -->
        <div>
          <h1 class="text-2xl font-bold leading-tight mb-1"
            style="font-family:var(--ws-serif);color:#fff;text-shadow:0 2px 12px rgba(0,0,0,.4)">
            {trip.title || trip.destination || $t('tripHubTitle')}
          </h1>
          <div class="flex items-center gap-3 flex-wrap">
            {#if trip.destination}
              <span class="text-sm font-mono" style="color:rgba(255,255,255,.75)">📍 {trip.destination}</span>
            {/if}
            {#if trip.start_date}
              <span class="text-sm font-mono" style="color:rgba(255,255,255,.65)">
                📅 {trip.start_date}{trip.end_date && trip.end_date !== trip.start_date ? ' → ' + trip.end_date : ''}
              </span>
            {/if}
            {#if trip.budget}
              <span class="text-sm font-mono font-bold" style="color:rgba(255,255,255,.9)">💶 {trip.budget} €</span>
            {/if}
          </div>
        </div>
      </div>
    </div>

    <!-- ── Action Slots ──────────────────────────────────────────────────────── -->
    <div class="grid grid-cols-2 gap-3">
      <button onclick={() => goSearch('flight')}
        class="flex flex-col items-center gap-2 rounded-2xl p-5 border transition-all hover:opacity-85 active:scale-[.98]"
        style="background:var(--ws-surface2);border-color:var(--ws-border)">
        <span class="text-3xl">✈️</span>
        <span class="text-sm font-semibold text-center" style="color:var(--ws-text)">{$t('tripHubPlanArrival')}</span>
        <span class="text-xs" style="color:var(--ws-muted)">PriceRadar →</span>
      </button>
      <button onclick={() => goSearch('hotel')}
        class="flex flex-col items-center gap-2 rounded-2xl p-5 border transition-all hover:opacity-85 active:scale-[.98]"
        style="background:var(--ws-surface2);border-color:var(--ws-border)">
        <span class="text-3xl">🏨</span>
        <span class="text-sm font-semibold text-center" style="color:var(--ws-text)">{$t('tripHubFindAccom')}</span>
        <span class="text-xs" style="color:var(--ws-muted)">PriceRadar →</span>
      </button>
    </div>

    <!-- ── Checkliste ────────────────────────────────────────────────────────── -->
    <div class="rounded-2xl border overflow-hidden" style="border-color:var(--ws-border)">

      <!-- Header -->
      <div class="flex items-center justify-between px-5 py-3.5 border-b" style="background:var(--ws-surface2);border-color:var(--ws-border)">
        <div class="flex items-center gap-2">
          <span class="font-bold text-sm" style="color:var(--ws-text)">{$t('tripHubTodos')}</span>
          {#if todos.length > 0}
            <span class="text-xs px-2 py-0.5 rounded-full font-semibold"
              style="background:color-mix(in srgb,var(--ws-accent) 15%,var(--ws-surface));color:var(--ws-accent)">
              {todos.filter(t => t.is_done).length}/{todos.length}
            </span>
          {/if}
        </div>
        {#if todos.length > 0}
          <!-- Progress bar -->
          <div class="flex items-center gap-2">
            <div class="w-24 h-1.5 rounded-full overflow-hidden" style="background:var(--ws-border)">
              <div class="h-full rounded-full transition-all duration-500"
                style="width:{donePct}%;background:{donePct === 100 ? 'var(--ws-green)' : 'var(--ws-accent)'}"></div>
            </div>
            <span class="text-xs font-mono" style="color:var(--ws-muted)">{donePct}%</span>
          </div>
        {/if}
      </div>

      <!-- Todo items -->
      <div class="divide-y" style="border-color:var(--ws-border)">
        {#if todos.length === 0}
          <div class="px-5 py-8 text-center text-sm" style="color:var(--ws-muted)">{$t('tripHubNoTodos')}</div>
        {:else}
          {#each todos as todo}
            <div class="flex items-center gap-3 px-5 py-3 transition-opacity"
              style="background:var(--ws-surface);{todo.is_done ? 'opacity:0.5' : ''}">
              <!-- Checkbox -->
              <button onclick={() => toggleTodo(todo)}
                class="w-5 h-5 rounded-md border-2 flex items-center justify-center shrink-0 transition-all"
                style={todo.is_done
                  ? 'background:var(--ws-green);border-color:var(--ws-green)'
                  : 'background:transparent;border-color:var(--ws-border)'}>
                {#if todo.is_done}<span class="text-[10px] text-white font-bold">✓</span>{/if}
              </button>
              <!-- Category icon -->
              <span class="text-base shrink-0">{catIcon(todo.category)}</span>
              <!-- Task text -->
              <span class="flex-1 text-sm" style="color:var(--ws-text);{todo.is_done ? 'text-decoration:line-through' : ''}">{todo.task}</span>
              <!-- Delete -->
              <button onclick={() => deleteTodo(todo)}
                class="opacity-0 hover:opacity-100 group-hover:opacity-40 text-sm shrink-0 transition-opacity hover:opacity-100 px-1"
                style="color:var(--ws-muted)">✕</button>
            </div>
          {/each}
        {/if}
      </div>

      <!-- Add todo -->
      <div class="flex items-center gap-2 px-4 py-3 border-t" style="border-color:var(--ws-border);background:var(--ws-surface2)">
        <input
          bind:value={newTask}
          placeholder={$t('tripHubTodoPlaceholder')}
          onkeydown={(e) => e.key === 'Enter' && addTodo()}
          class="flex-1 px-3 py-1.5 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ws-accent)] bg-transparent"
          style="border-color:var(--ws-border);color:var(--ws-text)"/>
        <button onclick={addTodo} disabled={!newTask.trim() || addingTodo}
          class="px-3 py-1.5 rounded-xl text-xs font-bold disabled:opacity-40 transition-opacity"
          style="background:var(--ws-accent);color:#fff5ec">
          {addingTodo ? '⏳' : '+'}
        </button>
      </div>
    </div>

  {/if}
</div>

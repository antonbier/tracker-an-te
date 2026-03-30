<script>
  import { toasts } from '$lib/toast.js';

  const typeStyles = {
    success: 'bg-green-600',
    error:   'bg-red-600',
    warning: 'bg-amber-500',
    info:    'bg-blue-600',
  };
</script>

<div class="fixed bottom-20 md:bottom-6 right-4 z-50 flex flex-col gap-2 pointer-events-none">
  {#each $toasts as t (t.id)}
    <div
      class="px-4 py-2.5 rounded-xl text-white text-sm font-medium shadow-lg pointer-events-auto
             {typeStyles[t.type] ?? typeStyles.info}"
    >
      {t.message}
    </div>
  {/each}
</div>

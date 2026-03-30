import { writable } from 'svelte/store';

export const toasts = writable([]);

let _id = 0;

/**
 * Show a toast notification.
 * @param {string} message
 * @param {'success'|'error'|'info'|'warning'} type
 * @param {number} duration ms
 */
export function toast(message, type = 'info', duration = 3500) {
  const id = ++_id;
  toasts.update((t) => [...t, { id, message, type }]);
  setTimeout(() => {
    toasts.update((t) => t.filter((x) => x.id !== id));
  }, duration);
}

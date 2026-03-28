// frontend/js/ui/toast.js
export function toast(msg, type = 'success') {
  const c = document.getElementById('toastContainer');
  const icons = { success: '✓', error: '✕', warning: '⚠' };
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${icons[type] || '•'}</span> ${msg}`;
  c.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

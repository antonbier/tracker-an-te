// frontend/js/ui/nav.js
import { setCurrentPage } from '../core/state.js';

export function navigate(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('page-' + page)?.classList.add('active');
  document.getElementById('nav-' + page)?.classList.add('active');
  setCurrentPage(page);
  if (window.innerWidth < 900) closeSidebar();
  // Lazy-init je Seite (dynamisch um Kreisimporte zu vermeiden)
  if (page === 'home')    import('../app/dashboard.js').then(m => m.loadDashboard());
  if (page === 'budget')  import('../app/budget.js').then(m => m.renderBudget());
  if (page === 'journal') import('../app/journal.js').then(m => m.loadJournalTrips());
  if (page === 'google')  import('../app/googleflights.js').then(m => m.loadGFTrackers());
  if (page === 'homair')  import('../app/homair.js').then(m => m.loadHomairTrackers());
  if (page === 'booking') import('../app/booking.js').then(m => m.loadBookingTrackers());
}

export function toggleSidebar() {
  const sb = document.getElementById('sidebar');
  const hb = document.getElementById('hamburger');
  const isOpen = sb.classList.toggle('open');
  hb.classList.toggle('open', isOpen);
}

export function closeSidebar() {
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('hamburger').classList.remove('open');
}

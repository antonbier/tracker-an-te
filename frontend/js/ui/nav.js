/**
 * ui/nav.js — Page navigation, sidebar and mobile bottom bar
 *
 * navigate(page) is the single entry point for all page switches. It:
 *   1. Toggles .page divs and .nav-item active states in the sidebar
 *   2. Syncs the mobile bottom bar active state via bnMap
 *   3. Lazy-loads page-specific data (avoids loading all modules on startup)
 *   4. Uses the View Transition API for smooth animations (Chrome 111+, graceful fallback)
 *
 * Page IDs (passed to navigate):
 *   home | priceradar | discover | mytrips | ryanair | google | homair | booking | budget | journal
 */

import { setCurrentPage } from '../core/state.js';

export function navigate(page) {
  // 1. Switch visible page and active nav highlight
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('page-' + page)?.classList.add('active');
  document.getElementById('nav-' + page)?.classList.add('active');
  setCurrentPage(page);
  if (window.innerWidth < 900) closeSidebar();

  // 2. Sync bottom bar — sub-pages share a parent bar item (e.g. ryanair → bn-radar)
  const bnMap = { home:'bn-home', priceradar:'bn-radar', ryanair:'bn-radar', google:'bn-radar', homair:'bn-radar', booking:'bn-radar', discover:'bn-discover', mytrips:'bn-trips', budget:'bn-trips', journal:'bn-trips' };
  document.querySelectorAll('.bottom-nav-item').forEach(b => b.classList.remove('active'));
  const bnId = bnMap[page];
  if (bnId) document.getElementById(bnId)?.classList.add('active');

  // 3. Lazy-load page data via dynamic import (only loads the module when first needed)
  const doNav = () => {
    if (page === 'home')       import('../app/dashboard.js').then(m => m.loadDashboard());
    if (page === 'budget')     import('../app/budget.js').then(m => m.renderBudget());
    if (page === 'journal')    import('../app/journal.js').then(m => m.loadJournalTrips());
    if (page === 'google')     import('../app/googleflights.js').then(m => m.loadGFTrackers());
    if (page === 'homair')     import('../app/homair.js').then(m => m.loadHomairTrackers());
    if (page === 'booking')    import('../app/booking.js').then(m => m.loadBookingTrackers());
    if (page === 'priceradar') import('../ui/priceradar.js').then(m => m.switchRadarCategory('overview'));
    if (page === 'mytrips')    import('../ui/tabs.js').then(m => { m.switchMyTripsTab('overview'); import('../app/bucketlist.js').then(b => b.updateMyTripsStats()); });
  };

  // 4. View Transition API — smooth crossfade between pages
  // NOTE: startViewTransition creates a ::view-transition overlay that can
  // intercept clicks on header buttons during/after animation. We use a
  // short timeout to ensure the transition completes before UI is interactive.
  if (document.startViewTransition) {
    const transition = document.startViewTransition(doNav);
    // Ensure header stays interactive during transition
    transition.finished.then(() => {
      document.documentElement.style.pointerEvents = '';
    });
  } else {
    doNav();
  }
}

/** Toggle the sidebar open/closed (hamburger button, desktop only). */
export function toggleSidebar() {
  const sb     = document.getElementById('sidebar');
  const hb     = document.getElementById('hamburger');
  const isOpen = sb.classList.toggle('open');
  hb.classList.toggle('open', isOpen);
}

/** Close the sidebar. Called after a mobile nav tap or an outside click. */
export function closeSidebar() {
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('hamburger').classList.remove('open');
}

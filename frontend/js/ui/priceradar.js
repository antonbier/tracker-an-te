/**
 * ui/priceradar.js — Preis-Radar two-level navigation
 *
 * The Preis-Radar page has two levels of navigation:
 *
 *   Level 1 (pill tabs): overview | flights | accommodations | carrental
 *     → switchRadarCategory(cat)
 *
 *   Level 2 (sub-tabs inside flights/accommodations):
 *     flights:         ryanair | google
 *     accommodations:  homair  | booking
 *     → switchRadarSubTab(trackerId)
 *
 * The legacy page-ryanair etc. divs still exist as hidden DOM nodes so that
 * JS functions like loadTrackers() can find their container IDs unchanged.
 */

const CATEGORIES = ['overview', 'flights', 'accommodations', 'carrental'];
const SUB_TABS   = { flights: ['ryanair', 'google'], accommodations: ['homair', 'booking'] };

/**
 * Switch the main Preis-Radar category.
 * Hides all panels, shows the selected one, and lazy-loads the default sub-tab.
 * @param {'overview'|'flights'|'accommodations'|'carrental'} cat
 */
export function switchRadarCategory(cat) {
  CATEGORIES.forEach(c => {
    const panel = document.getElementById('radar-panel-' + c);
    const tab   = document.getElementById('radar-tab-' + c);
    if (panel) panel.style.display = c === cat ? 'block' : 'none';
    if (tab)   tab.classList.toggle('active', c === cat);
  });

  // Auto-open the previously active sub-tab, or default to the first one
  if (cat === 'flights') {
    const active = document.querySelector('#radar-panel-flights .radar-sub-panel[data-active="true"]');
    const id = active ? active.id.replace('radar-sub-', '') : 'ryanair';
    switchRadarSubTab(id);
  }
  if (cat === 'accommodations') {
    const active = document.querySelector('#radar-panel-accommodations .radar-sub-panel[data-active="true"]');
    const id = active ? active.id.replace('radar-sub-', '') : 'homair';
    switchRadarSubTab(id);
  }
}

/**
 * Switch the tracker sub-tab within flights or accommodations.
 * Determines the parent category automatically from the trackerId.
 * Also triggers lazy-loading of the tracker list.
 * @param {'ryanair'|'google'|'homair'|'booking'} trackerId
 */
export function switchRadarSubTab(trackerId) {
  const cat      = ['ryanair','google'].includes(trackerId) ? 'flights' : 'accommodations';
  const siblings = SUB_TABS[cat];

  siblings.forEach(id => {
    const panel = document.getElementById('radar-sub-' + id);
    const tab   = document.getElementById('radar-subtab-' + id);
    if (panel) {
      panel.style.display = id === trackerId ? 'block' : 'none';
      panel.dataset.active = id === trackerId ? 'true' : 'false';
    }
    if (tab) tab.classList.toggle('active', id === trackerId);
  });

  // Lazy-load tracker data for the newly visible panel
  if (trackerId === 'ryanair') import('../app/ryanair.js').then(m => m.loadTrackers());
  if (trackerId === 'google')  import('../app/googleflights.js').then(m => m.loadGFTrackers());
  if (trackerId === 'homair')  import('../app/homair.js').then(m => m.loadHomairTrackers());
  if (trackerId === 'booking') import('../app/booking.js').then(m => m.loadBookingTrackers());
}

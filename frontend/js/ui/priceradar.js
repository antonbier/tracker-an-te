// frontend/js/ui/priceradar.js
// Preis-Radar: Two-level navigation (category → sub-tracker)

const CATEGORIES = ['overview', 'flights', 'accommodations', 'carrental'];
const SUB_TABS   = { flights: ['ryanair', 'google'], accommodations: ['homair', 'booking'] };

// Switch main Radar category (overview / flights / accommodations / carrental)
export function switchRadarCategory(cat) {
  CATEGORIES.forEach(c => {
    const panel = document.getElementById('radar-panel-' + c);
    const tab   = document.getElementById('radar-tab-' + c);
    if (panel) panel.style.display = c === cat ? 'block' : 'none';
    if (tab)   tab.classList.toggle('active', c === cat);
  });

  // Lazy-load sub-content when entering flights/accommodations
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

// Switch sub-tracker tab (ryanair / google / homair / booking)
export function switchRadarSubTab(trackerId) {
  // Determine parent category
  const cat = ['ryanair','google'].includes(trackerId) ? 'flights' : 'accommodations';
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

  // Trigger lazy-load for the selected tracker
  if (trackerId === 'ryanair') import('../app/ryanair.js').then(m => m.loadTrackers());
  if (trackerId === 'google')  import('../app/googleflights.js').then(m => m.loadGFTrackers());
  if (trackerId === 'homair')  import('../app/homair.js').then(m => m.loadHomairTrackers());
  if (trackerId === 'booking') import('../app/booking.js').then(m => m.loadBookingTrackers());
}

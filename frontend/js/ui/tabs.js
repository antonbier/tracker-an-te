// frontend/js/ui/tabs.js
// Shared tab-switching logic for multi-panel pages

const MYTRIPS_TABS = ['overview', 'bucketlist', 'journal', 'budget'];

export function switchMyTripsTab(tabId) {
  MYTRIPS_TABS.forEach(id => {
    const panel = document.getElementById('mytrips-panel-' + id);
    const tab   = document.getElementById('mytrips-tab-' + id);
    if (panel) panel.style.display = id === tabId ? 'block' : 'none';
    if (tab)   tab.classList.toggle('active', id === tabId);
  });

  // Lazy-load on first open
  if (tabId === 'journal')    import('../app/journal.js').then(m => m.loadJournalTrips());
  if (tabId === 'budget')     import('../app/budget.js').then(m => m.renderBudget());
  if (tabId === 'bucketlist') import('../app/bucketlist.js').then(m => m.renderBucketList());
  if (tabId === 'overview')   import('../app/bucketlist.js').then(m => m.updateMyTripsStats());
}

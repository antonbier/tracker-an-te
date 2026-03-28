/**
 * ui/tabs.js — Meine Reisen sub-tab switching
 *
 * Handles the four sub-tabs inside the "Meine Reisen" page:
 *   overview | bucketlist | journal | budget
 *
 * Each tab lazy-loads its data on first activation to avoid
 * unnecessary API calls when the page loads.
 */

const MYTRIPS_TABS = ['overview', 'bucketlist', 'journal', 'budget'];

/**
 * Switch to a sub-tab in the Meine Reisen page.
 * Shows the corresponding panel, marks the tab button as active,
 * and lazy-loads the tab content if needed.
 * @param {'overview'|'bucketlist'|'journal'|'budget'} tabId
 */
export function switchMyTripsTab(tabId) {
  MYTRIPS_TABS.forEach(id => {
    const panel = document.getElementById('mytrips-panel-' + id);
    const tab   = document.getElementById('mytrips-tab-' + id);
    if (panel) panel.style.display = id === tabId ? 'block' : 'none';
    if (tab)   tab.classList.toggle('active', id === tabId);
  });

  // Lazy-load on tab open — each import is cached by the browser after first load
  if (tabId === 'journal')    import('../app/journal.js').then(m => m.loadJournalTrips());
  if (tabId === 'budget')     import('../app/budget.js').then(m => m.renderBudget());
  if (tabId === 'bucketlist') import('../app/bucketlist.js').then(m => m.renderBucketList());
  if (tabId === 'overview')   import('../app/bucketlist.js').then(m => m.updateMyTripsStats());
}

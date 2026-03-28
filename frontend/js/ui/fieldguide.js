/**
 * ui/fieldguide.js — Feldführer (Help/Manual) slide panel
 *
 * The Field Guide is a full-height slide panel from the right (same pattern as Settings).
 * It has 4 tabs covering all major features of WanderSuite.
 *
 * Tabs: start | radar | mytrips | discover
 *
 * openFieldGuide()         — slides in the panel, defaults to 'start' tab
 * closeFieldGuide(e)       — slides out (also used as backdrop click handler)
 * switchFieldGuideTab(tab) — switches between the 4 content tabs
 */

const FG_TABS = ['start', 'radar', 'mytrips', 'discover'];

/**
 * Open the Field Guide panel and show the first tab.
 * Applies translations to any data-i18n elements inside the panel.
 */
export function openFieldGuide() {
  // Apply translations to dynamically rendered content
  const { t } = window;
  if (t) {
    document.querySelectorAll('#fieldGuideBackdrop [data-i18n]').forEach(el => {
      el.textContent = t(el.getAttribute('data-i18n'));
    });
  }
  switchFieldGuideTab('start');
  document.getElementById('fieldGuideBackdrop').classList.add('open');
  document.body.style.overflow = 'hidden';
  // Close sidebar on mobile
  if (window.innerWidth < 900 && window.closeSidebar) window.closeSidebar();
}

/**
 * Close the Field Guide panel.
 * When used as a backdrop onclick handler, only closes if the backdrop itself was clicked.
 * @param {Event|undefined} e
 */
export function closeFieldGuide(e) {
  if (e && e.target !== document.getElementById('fieldGuideBackdrop')) return;
  document.getElementById('fieldGuideBackdrop').classList.remove('open');
  document.body.style.overflow = '';
}

/**
 * Switch to a Field Guide tab.
 * @param {'start'|'radar'|'mytrips'|'discover'} tab
 */
export function switchFieldGuideTab(tab) {
  FG_TABS.forEach(id => {
    const panel = document.getElementById('fg-panel-' + id);
    const tabEl = document.getElementById('fg-tab-' + id);
    if (panel) panel.style.display = id === tab ? 'block' : 'none';
    if (tabEl) tabEl.classList.toggle('active', id === tab);
  });
}

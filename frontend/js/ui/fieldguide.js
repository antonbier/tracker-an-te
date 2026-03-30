/**
 * ui/fieldguide.js — Feldführer (Help/Manual) slide panel
 */

const FG_TABS = ['start', 'radar', 'mytrips', 'discover'];

export function openFieldGuide() {
  const bd = document.getElementById('fieldGuideBackdrop');
  if (!bd) { console.warn('[FG] fieldGuideBackdrop not found'); return; }
  switchFieldGuideTab('start');
  bd.classList.add('open');
  document.body.style.overflow = 'hidden';
  if (window.innerWidth < 900 && window.closeSidebar) window.closeSidebar();
}

export function closeFieldGuide(e) {
  // Close when clicking the backdrop itself (not its children)
  if (e && e.target !== document.getElementById('fieldGuideBackdrop')) return;
  _closeFieldGuide();
}

export function closeFieldGuideForced() {
  _closeFieldGuide();
}

function _closeFieldGuide() {
  const bd = document.getElementById('fieldGuideBackdrop');
  if (!bd) return;
  bd.classList.remove('open');
  document.body.style.overflow = '';
}

export function switchFieldGuideTab(tab) {
  FG_TABS.forEach(id => {
    const panel = document.getElementById('fg-panel-' + id);
    const tabEl = document.getElementById('fg-tab-' + id);
    if (panel) panel.style.display = id === tab ? 'block' : 'none';
    if (tabEl) tabEl.classList.toggle('active', id === tab);
  });
}

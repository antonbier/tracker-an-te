/**
 * ui/fieldguide.js — Feldführer (Help/Manual) slide panel
 */

const FG_TABS = ['start', 'radar', 'mytrips', 'discover'];

export function openFieldGuide() {
  const bd = document.getElementById('fieldGuideBackdrop');
  if (!bd) return;
  // Apply translations
  const { t } = window;
  if (t) {
    document.querySelectorAll('#fieldGuideBackdrop [data-i18n]').forEach(el => {
      el.textContent = t(el.getAttribute('data-i18n'));
    });
  }
  switchFieldGuideTab('start');
  bd.classList.add('open');
  document.body.style.overflow = 'hidden';
  if (window.innerWidth < 900 && window.closeSidebar) window.closeSidebar();
}

export function closeFieldGuide(e) {
  if (e && e.target !== document.getElementById('fieldGuideBackdrop')) return;
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

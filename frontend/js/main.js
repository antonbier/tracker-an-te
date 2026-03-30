/**
 * main.js — Application entry point
 *
 * This file is the ONLY file referenced in index.html:
 *   <script type="module" src="js/main.js">
 *
 * It does three things and nothing else:
 *   1. Imports all ES modules
 *   2. Binds all functions that are called from onclick="..." in HTML to window.*
 *      (ES modules don't share scope with inline handlers automatically)
 *   3. Runs the DOMContentLoaded initialization (locale load, theme, API check, etc.)
 *
 * To add a new function callable from HTML:
 *   1. Export it from its module
 *   2. Import it here
 *   3. Add window.myFunction = myFunction
 */

// ── Core ──────────────────────────────────────────────────────────────────────
import { API_URL, currentLang, setApiUrl }               from './core/state.js';
import { api, checkApiStatus }                            from './core/api.js';
import { syncAllToBackend, restoreFromBackend }           from './core/persist.js';
import { initAuth, logout, showAuthScreen, hideAuthScreen,
         submitLogin, submitSetup, switchAuthTab,
         loadAdminUsers, createAdminUser, deleteAdminUser,
         changePassword }                                 from './app/auth.js';

// ── UI ────────────────────────────────────────────────────────────────────────
import { loadLocale, t, applyTranslations, setLang }     from './ui/i18n.js';
import { navigate, toggleSidebar, closeSidebar }          from './ui/nav.js';
import { toast }                                          from './ui/toast.js';
import { openSettings, closeSettings, saveSettings,
         loadSerpApiQuota, backdropClick, switchTab,
         switchNotifTab, testTelegram, testGotify,
         toggleTheme }                                    from './ui/settings.js';
import { switchRadarCategory, switchRadarSubTab }         from './ui/priceradar.js';
import { switchMyTripsTab }                               from './ui/tabs.js';
import { openFieldGuide, closeFieldGuide,
         switchFieldGuideTab }                            from './ui/fieldguide.js';

// ── App Modules ───────────────────────────────────────────────────────────────
import { toggleBag, addTracker, loadTrackers, renderTrackers,
         selectTracker, renderStats, renderChart, renderTable,
         scrapeNow, deleteTracker, togglePause,
         checkDawarich, generateIdeas, renderRecommendations,
         setThreshold, clearThreshold, exportCsvSelected }    from './app/ryanair.js';

import { toggleActualSync, addTrip, syncActualBudget,
         updateBudget, renderBudget, removeTrip,
         loadExpenses, filterExpenses, renderExpenseTable }    from './app/budget.js';

import { loadDashboard, loadDashTrackers,
         loadDashBudget, loadDashTrips,
         loadMyTripsDashboard }                               from './app/dashboard.js';
import { initScratchMap, loadScratchMap }                    from './app/scratchmap.js';
import { addGFTracker, loadGFTrackers, renderGFTrackers,
         scrapeGFTracker, deleteGFTracker }                    from './app/googleflights.js';

import { addHomairTracker, loadHomairTrackers, renderHomairTrackers,
         scrapeHomairTracker, deleteHomairTracker }             from './app/homair.js';

import { addBookingTracker, loadBookingTrackers, renderBookingTrackers,
         scrapeBookingTracker, deleteBookingTracker }           from './app/booking.js';

import { loadJournalTrips, renderJournalTrips,
         syncJournal, deleteJournalTrip }                      from './app/journal.js';

import { checkOnboarding, closeOnboarding, obNext, obBack,
         updateObStep, checkConnection }                        from './app/onboarding.js';

import { addBucketListItem, deleteBucketListItem,
         renderBucketList, updateMyTripsStats }                from './app/bucketlist.js';

// ── Hilfsfunktionen ───────────────────────────────────────────────────────────
function fmt(d) { return d.toISOString().slice(0,10); }

// ── Window-Bindungen (für onclick="..." im HTML) ──────────────────────────────
window.navigate              = navigate;
window.toggleSidebar         = toggleSidebar;
window.closeSidebar          = closeSidebar;
window.api                   = api;
window.checkApiStatus        = checkApiStatus;
window.syncAllToBackend      = syncAllToBackend;
window.restoreFromBackend    = restoreFromBackend;
window.logout                = logout;
window.showAuthScreen        = showAuthScreen;
window.hideAuthScreen        = hideAuthScreen;
window.submitLogin           = submitLogin;
window.submitSetup           = submitSetup;
window.switchAuthTab         = switchAuthTab;
window.loadAdminUsers        = loadAdminUsers;
window.createAdminUser       = createAdminUser;
window.deleteAdminUser       = deleteAdminUser;
window.changePassword        = changePassword;
window.restoreFromBackend    = restoreFromBackend;
window.t                     = t;
window.setLang               = setLang;
window.applyTranslations     = applyTranslations;
window.loadLocale            = loadLocale;
window.fmt                   = fmt;
window.toast                 = toast;
window.openSettings          = openSettings;
window.closeSettings         = closeSettings;
window.saveSettings          = saveSettings;
window.loadSerpApiQuota      = loadSerpApiQuota;
window.backdropClick         = backdropClick;
window.switchTab             = switchTab;
window.switchNotifTab        = switchNotifTab;
window.testTelegram          = testTelegram;
window.testGotify            = testGotify;
window.toggleTheme           = toggleTheme;
window.openFieldGuide        = openFieldGuide;
window.closeFieldGuide       = closeFieldGuide;
window.switchFieldGuideTab   = switchFieldGuideTab;
window.switchRadarCategory   = switchRadarCategory;
window.switchRadarSubTab     = switchRadarSubTab;
window.switchMyTripsTab      = switchMyTripsTab;
window.toggleBag             = toggleBag;
window.addTracker            = addTracker;
window.loadTrackers          = loadTrackers;
window.renderTrackers        = renderTrackers;
window.selectTracker         = selectTracker;
window.scrapeNow             = scrapeNow;
window.deleteTracker         = deleteTracker;
window.togglePause           = togglePause;
window.checkDawarich         = checkDawarich;
window.generateIdeas         = generateIdeas;
window.renderRecommendations = renderRecommendations;
window.setThreshold          = setThreshold;
window.clearThreshold        = clearThreshold;
window.exportCsvSelected     = exportCsvSelected;
window.toggleActualSync      = toggleActualSync;
window.addTrip               = addTrip;
window.syncActualBudget      = syncActualBudget;
window.updateBudget          = updateBudget;
window.renderBudget          = renderBudget;
window.removeTrip            = removeTrip;
window.loadExpenses          = loadExpenses;
window.filterExpenses        = filterExpenses;
window.renderExpenseTable    = renderExpenseTable;
window.loadDashboard         = loadDashboard;
window.loadDashTrackers      = loadDashTrackers;
window.loadDashBudget        = loadDashBudget;
window.loadDashTrips         = loadDashTrips;
window.loadMyTripsDashboard  = loadMyTripsDashboard;
window.initScratchMap        = initScratchMap;
window.loadScratchMap        = loadScratchMap;
window.addGFTracker          = addGFTracker;
window.loadGFTrackers        = loadGFTrackers;
window.renderGFTrackers      = renderGFTrackers;
window.scrapeGFTracker       = scrapeGFTracker;
window.deleteGFTracker       = deleteGFTracker;
window.addHomairTracker      = addHomairTracker;
window.loadHomairTrackers    = loadHomairTrackers;
window.renderHomairTrackers  = renderHomairTrackers;
window.scrapeHomairTracker   = scrapeHomairTracker;
window.deleteHomairTracker   = deleteHomairTracker;
window.addBookingTracker     = addBookingTracker;
window.loadBookingTrackers   = loadBookingTrackers;
window.renderBookingTrackers = renderBookingTrackers;
window.scrapeBookingTracker  = scrapeBookingTracker;
window.deleteBookingTracker  = deleteBookingTracker;
window.loadJournalTrips      = loadJournalTrips;
window.renderJournalTrips    = renderJournalTrips;
window.syncJournal           = syncJournal;
window.deleteJournalTrip     = deleteJournalTrip;
window.checkOnboarding       = checkOnboarding;
window.closeOnboarding       = closeOnboarding;
window.obNext                = obNext;
window.obBack                = obBack;
window.updateObStep          = updateObStep;
window.checkConnection       = checkConnection;
window.addBucketListItem     = addBucketListItem;
window.deleteBucketListItem  = deleteBucketListItem;
window.renderBucketList      = renderBucketList;
window.updateMyTripsStats    = updateMyTripsStats;

// ── Init ──────────────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', async () => {
  const toLoad = currentLang === 'de' ? ['de'] : ['de', currentLang];
  await Promise.all(toLoad.map(loadLocale));
  applyTranslations();

  if (localStorage.getItem('theme') === 'dark') document.body.classList.add('dark-mode');

  const savedUrl = localStorage.getItem('apiUrl') || '';
  setApiUrl(savedUrl);

  const today = new Date();
  const out = new Date(today); out.setDate(out.getDate() + 30);
  const ret = new Date(today); ret.setDate(ret.getDate() + 37);
  document.getElementById('outboundDate').value = fmt(out);
  document.getElementById('returnDate').value   = fmt(ret);

  // Auth gate — runs before app starts
  const authOk = await initAuth();
  if (!authOk) return;

  checkApiStatus();
  restoreFromBackend(); // cold-start: pull ws-trips/budget/bucketlist from backend if localStorage is empty
  loadTrackers();
  loadDashboard();
  checkOnboarding();

  if (savedUrl) {
    const notice = document.querySelector('.api-notice');
    if (notice) notice.classList.add('hidden');
  }

  const savedBudget = localStorage.getItem('ws-budget');
  if (savedBudget) document.getElementById('budgetTotal').value = savedBudget;

  document.addEventListener('click', e => {
    const sb = document.getElementById('sidebar');
    const hb = document.getElementById('hamburger');
    if (window.innerWidth < 900 && sb.classList.contains('open') &&
        !sb.contains(e.target) && !hb.contains(e.target)) closeSidebar();
  });

  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeSettings(); });

  // Bind fieldguide button via addEventListener (more reliable than onclick for ES modules)
  const fgBtn = document.getElementById('btn-fieldguide');
  if (fgBtn) {
    fgBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      console.log('[FieldGuide] button clicked via addEventListener');
      openFieldGuide();
    });
  } else {
    console.warn('[FieldGuide] btn-fieldguide not found in DOM');
  }

  // ── PWA: Register Service Worker ──────────────────────────────────────────
  if ('serviceWorker' in navigator) {
    // Verify sw.js is reachable with correct MIME type before registering
    fetch('/sw.js', { method: 'HEAD' })
      .then(r => {
        const ct = r.headers.get('content-type') || '';
        console.log('[PWA] sw.js status:', r.status, 'content-type:', ct);
        if (!r.ok) throw new Error('sw.js not found: ' + r.status);
        if (!ct.includes('javascript') && !ct.includes('application/')) {
          console.warn('[PWA] sw.js wrong MIME type:', ct, '— SW may be blocked by browser');
        }
      })
      .catch(e => console.warn('[PWA] sw.js HEAD check failed:', e));

    navigator.serviceWorker.register('/sw.js', { scope: '/' })
      .then(reg => {
        console.log('[SW] Registered successfully, scope:', reg.scope);
        reg.update();
      })
      .catch(err => {
        console.error('[SW] Registration FAILED:', err.message);
        console.error('[SW] This usually means: wrong MIME type, wrong path, or not HTTPS');
      });
  } else {
    console.warn('[PWA] Service Workers not supported in this browser');
  }

  // ── PWA: Install prompt ────────────────────────────────────────────────────
  // Chrome fires beforeinstallprompt when the app is installable.
  // We catch it, show our custom button, and trigger it on click.
  let _deferredInstallPrompt = null;

  window.addEventListener('beforeinstallprompt', e => {
    e.preventDefault();                            // stop Chrome's auto-banner
    _deferredInstallPrompt = e;
    const btn = document.getElementById('pwa-install-btn');
    if (btn) btn.classList.add('visible');         // show our button
    console.log('[PWA] Install prompt ready');
  });

  window.addEventListener('appinstalled', () => {
    _deferredInstallPrompt = null;
    const btn = document.getElementById('pwa-install-btn');
    if (btn) btn.classList.remove('visible');
    console.log('[PWA] App installed successfully');
  });

  // Called by onclick="pwaInstall()" on the install button
  window.pwaInstall = async () => {
    if (!_deferredInstallPrompt) return;
    _deferredInstallPrompt.prompt();
    const { outcome } = await _deferredInstallPrompt.userChoice;
    console.log('[PWA] User choice:', outcome);
    _deferredInstallPrompt = null;
    const btn = document.getElementById('pwa-install-btn');
    if (btn) btn.classList.remove('visible');
  };

  // ── Dark mode: sync theme-color meta tag with body class ──────────────────
  const syncThemeColor = () => {
    const isDark = document.body.classList.contains('dark-mode');
    const meta   = document.getElementById('meta-theme-color');
    if (meta) meta.content = isDark ? '#12141c' : '#f9f8f6';
  };
  // Observe body class changes
  new MutationObserver(syncThemeColor).observe(document.body, { attributes: true, attributeFilter: ['class'] });
  syncThemeColor(); // run once on load
});

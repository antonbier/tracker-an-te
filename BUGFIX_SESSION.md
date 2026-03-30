# Bug Fix Session — UI Not Clickable / Field Guide Not Opening

## Environment
- Frontend deployed on here.now (static host, only deploys `frontend/` root files)
- Service Worker pre-caches all JS modules
- Chrome + Firefox tested

## Symptoms
1. Field Guide (📖 button) not opening
2. Onboarding wizard not appearing on first visit (incognito)
3. Security tab visible in Settings when AUTH_ENABLED=false
4. "Nothing clickable" after fresh SW install

---

## Root Causes & Fixes (chronological)

### 1. `pointer-events` transition delay on `#onboardingBackdrop` (FIXED)
```css
/* BUG — delay in .open state blocked clicks on everything below for 350ms */
#onboardingBackdrop.open {
  pointer-events: all;
  transition: opacity .35s ease, pointer-events 0s .35s; /* ← WRONG */
}
/* FIX */
#onboardingBackdrop.open {
  pointer-events: all;
  transition: opacity .35s ease;
}
```
Also added `visibility: hidden` to closed state.

### 2. `saveSettings()` triggering `checkOnboarding()` (FIXED)
`frontend/js/ui/settings.js` called `checkOnboarding()` after saving — which
re-showed the wizard if `ws-onboarding-done` wasn't set.
Fix: removed call, replaced with `localStorage.setItem('ws-onboarding-done', '1')`.

### 3. `auth-overlay` (z-index: 2000) left in DOM (FIXED)
When `initAuth()` returns true (no backend / auth disabled), the `#auth-overlay`
div was not always removed.
Fix: added `_removeOverlayIfPresent()` on every `return true` path in `auth.js`.

### 4. View Transition API blocking header clicks (FIXED)
`nav.js` used `document.startViewTransition()` which creates a `::view-transition`
pseudo-element covering the entire viewport including the header.
Fix: `startViewTransition` completely disabled, using plain `doNav()` instead.

### 5. z-index conflict — `modal-backdrop` below `#onboardingBackdrop` (FIXED)
`.modal-backdrop` z-index was 500, `#onboardingBackdrop` was 1000.
Fix: `.modal-backdrop` z-index raised to 1100.
Also removed `view-transition-name: header` from `.header` CSS (was creating
a stacking context).

### 6. Service Worker serving stale JS — fixes never reached browser (CONFIRMED)
here.now only deploys files in `frontend/` root (4 files: index.html, sw.js,
manifest.json, _headers). The `js/` subdirectory was served from SW cache v2.
All fixes to `fieldguide.js`, `nav.js` etc. never reached the browser.
Fix: SW cache bumped v2 → v3 (forces fresh fetch of all JS modules).

### 7. Security tab visible when AUTH_ENABLED=false (FIXED)
`#tab-security` button was always visible in Settings HTML.
Fix: added `style="display:none"` by default — settings.js shows it only when
the user is authenticated as admin.

### 8. `_renderOverviewLinks` undefined in dashboard.js (FIXED)
`dashboard.js` called `_renderOverviewLinks()` which was never defined.
Caused `ReferenceError` on startup when `loadDashboard()` ran with no backend.
Fix: removed the call — content already handled by `_notConfigured()`.

### 9. `.main-content` animation creating CSS stacking context (FIXED — NOT YET CONFIRMED WORKING)
`animation: page-in .22s ease both` on `.main-content` creates a CSS stacking
context. The `both` fill-mode keeps all children at `opacity:0` until the
animation fires. Fixed-position modals (Field Guide, Settings) inside this
stacking context remain at `opacity:0` even with `!important` overrides.

This explains why:
- `classList.add('open')` ran successfully
- `opacity:1 !important` was set
- But `getComputedStyle(bd).opacity` still returned `0`

Fix: removed animation from `.main-content`, moved to `.page.active`:
```css
/* BEFORE */
.main-content { animation: page-in .22s ease both; }

/* AFTER */
.main-content { /* no animation */ }
.page.active { animation: page-in .22s ease; }
```

---

## Current Status (session end)
- Field Guide still not confirmed working — not tested after fix #9
- Onboarding still not appearing in incognito — not tested after fix #9
- All fixes committed, SW at v3

## Files Modified
- `frontend/index.html` — CSS fixes (z-index, animation, security tab, modal-backdrop)
- `frontend/sw.js` — cache version v2 → v3
- `frontend/js/app/auth.js` — `_removeOverlayIfPresent()` cleanup
- `frontend/js/app/onboarding.js` — simplified `checkOnboarding()`, next button never disabled
- `frontend/js/app/dashboard.js` — removed undefined `_renderOverviewLinks()` call
- `frontend/js/ui/settings.js` — removed `checkOnboarding()` call after save
- `frontend/js/ui/fieldguide.js` — cleaned up debug logs
- `frontend/js/ui/nav.js` — disabled `startViewTransition`, plain `doNav()` instead
- `frontend/js/main.js` — `addEventListener` binding for fieldguide button

## Commit History
- `0cede33` — onboarding wizard blocks app when no backend
- `ecf87b8` — onboarding skips if any localStorage exists; auth-overlay cleanup
- `19cf277` — pointer-events transition delay fix; visibility:hidden
- `f94d0d5` — debug logging in fieldguide; onboarding key check
- `d0594e2` — fieldguide button via addEventListener+stopPropagation
- `8ab7d0b` — BUGFIX_SESSION.md created
- `f2e6582` — View Transition API disabled; shorter animation duration
- `4709b0f` — modal-backdrop z-index 500→1100; remove view-transition-name
- `cb6e97d` — force fieldguide styles + log computed styles (debug)
- `df7ea2a` — SW cache v2→v3; inline fixes in index.html (later removed)
- `94d75e2` — removed blocking inline script; clean fieldguide.js
- `270a910` — opacity:1 !important on .modal-backdrop.open
- `02eb2ff` — main-content animation removed (stacking context fix)

## Next Steps for New Claude Instance
1. Test after fix #9 — open here.now in Chrome incognito
2. Check console: does Field Guide open now?
3. If still `opacity:0` on backdrop:
   - Run in console: `document.querySelector('.main-content').getAnimations()`
     → should return empty array
   - Run: `document.querySelector('.modal-backdrop').offsetParent`
     → should NOT be `.main-content`
   - Check if any OTHER ancestor has `animation`, `transform`, `filter`, `will-change`,
     `isolation: isolate` — all create stacking contexts
4. Nuclear option if still broken: move ALL modals to `document.body` directly
   via JavaScript: `document.body.appendChild(document.getElementById('fieldGuideBackdrop'))`
   — this removes them from any stacking context entirely

## Key Insight
CSS stacking contexts (created by animation, transform, filter, opacity<1,
will-change, isolation) affect `position:fixed` children — they become
fixed relative to the stacking context ancestor, not the viewport.
This is why z-index and !important overrides didn't work.

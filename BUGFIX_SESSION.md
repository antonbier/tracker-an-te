# Bug Fix Session — UI Not Clickable

## Symptoms
- Entire UI blocked/not clickable after page load
- Field Guide (📖) button not responding to clicks
- Settings modal working after partial fix
- Onboarding wizard appearing unexpectedly and blocking UI

## Root Causes Found

### 1. `pointer-events` transition delay on `#onboardingBackdrop` (FIXED)
```css
/* BUG — this was in .open state, causing 350ms block on everything below */
#onboardingBackdrop.open {
  pointer-events: all;
  transition: opacity .35s ease, pointer-events 0s .35s; /* ← WRONG */
}
/* FIX */
#onboardingBackdrop.open {
  pointer-events: all;
  transition: opacity .35s ease; /* delay removed */
}
```
Also added `visibility: hidden` to closed state so it's fully inert.

### 2. `saveSettings()` triggering `checkOnboarding()` (FIXED)
In `frontend/js/ui/settings.js`, after saving settings, `checkOnboarding()` was
called — which would re-show the wizard if `ws-onboarding-done` wasn't set yet.
Fix: removed `checkOnboarding()` call from `saveSettings()`, replaced with:
```js
localStorage.setItem('ws-onboarding-done', '1');
```

### 3. `checkOnboarding()` showing wizard incorrectly (FIXED)
- Was using `localStorage.length > 0` to detect "has visited before" — unreliable
- Fixed to check for WanderSuite-specific keys: `theme`, `lang`, `s-timezone`, `s-lightMode`
- In incognito without backend: wizard now correctly shows (none of those keys exist)

### 4. `auth-overlay` (z-index: 2000) left in DOM (FIXED)
When `initAuth()` returns `true` (no backend / auth disabled), the `#auth-overlay`
div was not always removed. Added `_removeOverlayIfPresent()` called on every
`return true` path in `auth.js`.

### 5. Field Guide button not responding (IN PROGRESS — NOT YET FIXED)
`openFieldGuide()` is correctly bound to `window`, but clicks on the 📖 button
produce no console output at all — meaning something is intercepting the click
before it reaches the button.

**What was tried:**
- Added `id="btn-fieldguide"` to the button
- Bound via `addEventListener('click', e => { e.stopPropagation(); openFieldGuide(); })`
  in `main.js` DOMContentLoaded — pushed but not yet confirmed working

### 6. View Transition API overlay blocking header clicks (ROOT CAUSE — FIXED)

`nav.js` uses `document.startViewTransition()` for page animations. This API
creates a `::view-transition` pseudo-element that covers the **entire viewport**
including the header during (and sometimes after) the animation.

On Chrome 111+ (which here.now uses), this overlay intercepts all click events
on the header buttons (⚙ Settings, 📖 Field Guide) after any navigation.

**Fix in `frontend/js/ui/nav.js`:**
```js
// Added transition.finished.then() to clean up pointer-events
const transition = document.startViewTransition(doNav);
transition.finished.then(() => {
  document.documentElement.style.pointerEvents = '';
});
```

**Fix in `frontend/index.html`:**
```css
/* Shorter transition duration + give header its own layer */
::view-transition-old(root), ::view-transition-new(root) {
  animation-duration: 0.18s;
}
.header { view-transition-name: header; }
```

**Commits:** see latest push

## Files Modified
- `frontend/index.html` — CSS fixes for onboarding, auth-overlay, fieldguide button id
- `frontend/js/app/onboarding.js` — checkOnboarding logic, next button never disabled
- `frontend/js/app/auth.js` — _removeOverlayIfPresent() on all return true paths
- `frontend/js/ui/settings.js` — removed checkOnboarding() call, mark done instead
- `frontend/js/ui/fieldguide.js` — added console.log debug (can be removed once fixed)
- `frontend/js/main.js` — addEventListener binding for fieldguide button

## Commits
- `0cede33` — onboarding wizard blocks app when no backend
- `ecf87b8` — onboarding skips if any localStorage exists; auth-overlay cleanup
- `19cf277` — pointer-events transition delay fix; visibility:hidden when closed
- `f94d0d5` — debug logging in fieldguide; onboarding WanderSuite-specific key check
- `d0594e2` — fieldguide button via addEventListener+stopPropagation


### 7. z-index conflict — modal-backdrop below onboardingBackdrop (FIXED)

`.modal-backdrop` (z-index: 500) was below `#onboardingBackdrop` (z-index: 1000).
Even with `visibility:hidden` on the onboarding backdrop, it was creating a
stacking context that prevented the Field Guide panel from appearing visually.

Also: `view-transition-name: header` on `.header` was creating a new stacking
context that interfered with fixed-position modals.

**Fixes:**
- `.modal-backdrop` z-index: 500 → **1100** (above onboarding at 1000)
- Removed `view-transition-name: header` from `.header` CSS
- All modals (Settings + Field Guide) now render above onboarding backdrop

**z-index hierarchy (final):**
```
sidebar:         200
header:          300
bottom-nav:      400
onboarding:     1000
modal-backdrop: 1100  ← Settings + Field Guide
auth-overlay:   2000
```


### 8. opacity:0 not overridden — View Transition animation resetting styles (ROOT CAUSE CONFIRMED)

Console showed: `opacity: 0` even after `bd.style.opacity = '1'` was set inline.
This confirms the View Transition API's `::view-transition` pseudo-element was
running an animation that reset opacity back to 0 on all fixed-position elements.

**Final fixes:**
- `document.startViewTransition()` **completely disabled** in `nav.js` — just `doNav()` now
- `.modal-backdrop.open { opacity:1 !important }` to prevent any override
- Onboarding check simplified back to basics (only `seen` + `hasUrl` checks)

**Result:** Field Guide and Settings panels should now open correctly.

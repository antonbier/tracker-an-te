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

**Next steps to try if still broken:**
1. Open DevTools → Elements → inspect the 📖 button
2. Run in console: `document.getElementById('btn-fieldguide').getBoundingClientRect()`
   — check if width/height is 0 (invisible/collapsed)
3. Run: `document.elementFromPoint(X, Y)` where X,Y are the pixel coords of the button
   — this reveals what element is actually receiving the click
4. Check if `.header-right` has correct `overflow: visible` and no child is expanding
5. Suspect: `.status-dot` or another element in `.header-right` may be expanding
   beyond its visual bounds and overlapping the 📖 button

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

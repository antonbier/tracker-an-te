# Session-Ende 2026-03-30

## GitHub Token
Neuen Token in den Repo-Settings generieren unter:
https://github.com/settings/tokens
→ Scopes: repo (full)

## SW Cache: v13 (in frontend/sw.js)

## Aktuelle here.now URL
Immer aktuell: https://github.com/antonbier/tracker-an-te/actions
→ Letzter bekannter Stand: boreal-soul-2yey.here.now

---

## Offener Bug: Bottom Nav fehlt auf Mobile (iPhone)

Status: Mehrere Fixes, noch nicht bestaetigt.
Letzter Stand: display:flex !important in Media Query + z-index:1002

Debug in Konsole:
```
const n = document.getElementById('bottomNav');
console.log(getComputedStyle(n).display, n.getBoundingClientRect());
console.log('body overflow:', document.body.style.overflow);
```

Schnelltest (wenn Nav erscheint = CSS Specificity Problem):
```
document.getElementById('bottomNav').style.cssText =
  'display:flex!important;position:fixed!important;bottom:0;left:0;right:0;z-index:9999';
```

---

## Behobene Bugs dieser Session

- App nicht klickbar: onboardingBackdrop class=open hardcoded im HTML -> entfernt
- Onboarding blockiert Klicks: Teil der modal-backdrop Regel -> eigene display:none/flex Regel
- Field Guide oeffnet nicht: Doppelter Handler (onclick + addEventListener) -> onclick entfernt
- Modals blieben opacity:0: animation auf .main-content = Stacking Context -> auf .page.active
- Header-Buttons nicht klickbar: View Transition API -> startViewTransition deaktiviert
- Auth-Overlay blieb im DOM: _removeOverlayIfPresent() auf allen initAuth() Pfaden
- Settings oeffnete Onboarding: checkOnboarding()-Call aus saveSettings() entfernt

---

## Svelte-Migration

Stack: Svelte + Vite (reine SPA, kein SvelteKit noetig)
Deploy: Netlify oder Cloudflare Pages (stabile URLs!)
Backend: FastAPI + SQLite unveraendert

here.now Problem: neue URL bei JEDEM Deploy -> bei Svelte-Migration sofort zu Netlify wechseln.

Svelte Store fuer state.js:
```javascript
import { writable } from 'svelte/store';
export const apiUrl      = writable(localStorage.getItem('apiUrl') || '');
export const jwtToken    = writable(localStorage.getItem('ws-jwt') || '');
export const currentUser = writable(
  JSON.parse(localStorage.getItem('ws-current-user') || 'null')
);
```

Migrations-Reihenfolge:
1. Vite + Svelte Setup, npm run build -> dist/
2. api.js mit JWT-Injection portieren
3. Auth Store + Login-Komponente
4. Komponenten: Card -> Panel -> Page -> App-Shell
5. Netlify/Cloudflare Deploy

CLAUDE.md und README.md enthalten die vollstaendige Architektur-Dokumentation.
BUGFIX_SESSION.md enthaelt den detaillierten Bug-Verlauf dieser Session.

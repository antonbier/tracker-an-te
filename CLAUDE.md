# CLAUDE.md — WanderSuite AI Assistant Context (BETA branch)

**⚠️ You are on the `beta` branch.**

---

## Branch Strategy

| Branch | Purpose | Ports | Version |
|--------|---------|-------|---------|
| `main` | Stable, production | 8765 / 8766 | `1.0.0` |
| `beta` | New features, testing | 8767 / 8768 | `beta-YYYY-MM-DD HH:MM` |

## Multi-User Architecture (beta)

### Data Isolation
| Table | Per-User | Notes |
|-------|----------|-------|
| `trackers` | ✅ `user_id` | each user sees own trackers |
| `gf_trackers` | ✅ `user_id` | |
| `homair_trackers` | ✅ `user_id` | |
| `booking_trackers` | ✅ `user_id` | |
| `detected_trips` | ✅ `user_id` | Dawarich per user |
| `user_data` | ✅ `user_id` | trips list, budget, bucketlist |
| `user_settings` | ✅ `user_id` | dawarich, actualbudget, home coords |
| `settings` | ❌ Global | API keys (serpapi, gemini, openai), notifications |
| `webauthn_credentials` | ✅ `user_id` | passkeys per user |

### Settings Split
- **Global (Admin):** `POST /api/settings` — SerpAPI, Gemini, OpenAI, Telegram, Gotify
- **Per-User:** `GET/POST /api/settings/user` — Dawarich, ActualBudget, Home coords

### AUTH_ENABLED=false (guest mode)
- `get_current_user()` returns `GUEST_USER = {id: 0, role: "admin"}`
- DB functions with `user_id=0` → `_uid()` returns `None` → no filter → sees all data
- Fully backward compatible — single-user setups work without auth

### User ID flow
```
Request → get_current_user() → {id: N}
         ↓
Route → _uid(user) → N or None
         ↓
DB function(user_id=N) → WHERE user_id=N
                        → no filter if N=None (guest/admin)
```

## Passkey + Password Auth
- `POST /api/auth/login` — email + password → JWT
- `POST /api/auth/passkeys/login/begin|complete` — WebAuthn → JWT
- `POST /api/auth/passkeys/register/begin|complete` — register passkey (logged in)
- Requires HTTPS for WebAuthn (localhost works for testing)
- `.env`: `WEBAUTHN_RP_ID`, `WEBAUTHN_ORIGIN`

## Build + Start (beta)

```bash
cd /mnt/user/appdata/wandersuite-beta
git pull
BUILD_DATE="$(date '+%Y-%m-%d %H:%M')" docker compose up -d --build
```

## Active Development (beta)
- [ ] Frontend: per-user Settings tab ("Mein Bereich")
- [ ] Frontend: PasskeyManager in Settings
- [ ] Scratch Map (jsvectormap)
- [ ] Price history chart (Chart.js)
- [ ] Mietwagen tab
- [ ] Discord webhook
- [ ] Currency toggle (EUR/USD/GBP)

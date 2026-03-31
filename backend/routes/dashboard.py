"""
WanderSuite — REST Routes: /api/dashboard
Aggregated stats for the "Meine Reisen" overview dashboard.

Returns live data from:
  - Dawarich (visited places / unique countries)
  - ActualBudget (remaining travel budget)
  - Local DB (detected trips count)

All integrations are optional — missing config returns null values
with a descriptive status so the frontend can show "Setup fehlt".
"""

from fastapi import APIRouter
import logging

from database import list_detected_trips
from settings_manager import get_setting_value, get_user_setting_value

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/stats")
def get_dashboard_stats():
    """
    Aggregated stats for the Meine Reisen overview tab.

    Returns:
        visited_places:   int | None   — detected trips count from local DB
        unique_countries: int | None   — unique countries from detected trips
        dawarich_status:  str          — 'ok' | 'not_configured'
        budget_remaining: float | None — remaining travel budget from ActualBudget
        budget_total:     float | None — total budgeted for travel
        budget_month:     str | None   — month of budget data (YYYY-MM)
        budget_status:    str          — 'ok' | 'not_configured' | 'error'
        wishlist_count:   None         — always null (stored client-side only)
    """
    result = {
        "visited_places":   None,
        "unique_countries": None,
        "dawarich_status":  "not_configured",
        "budget_remaining": None,
        "budget_total":     None,
        "budget_month":     None,
        "budget_status":    "not_configured",
        "wishlist_count":   None,  # localStorage-only, backend can't know
    }

    # ── Dawarich: read from local detected_trips table ─────────────────────
    # We don't re-fetch from Dawarich API here (expensive) — use already-synced data
    dawarich_url   = get_setting_value("dawarich_url")   or ""
    dawarich_token = get_setting_value("dawarich_token") or ""

    if dawarich_url and dawarich_token:
        try:
            trips = list_detected_trips(limit=500, user_id=None)
            result["visited_places"]   = len(trips)
            result["unique_countries"] = len({t.get("country") for t in trips if t.get("country")})
            result["dawarich_status"]  = "ok"
        except Exception as e:
            logger.warning(f"Dashboard stats: Dawarich DB read failed: {e}")
            result["dawarich_status"] = "error"
    # else: not_configured — frontend shows "Nicht verknüpft"

    # ── ActualBudget: fetch current month summary ───────────────────────────
    actual_url      = get_setting_value("actual_url")   or ""
    actual_token    = get_setting_value("actual_token") or ""
    actual_file     = get_setting_value("actual_file")  or ""
    travel_cats_raw = get_setting_value("travel_categories") or ""

    if actual_url and actual_token and actual_file:
        try:
            from actual_budget import get_budget_summary
            travel_cats = [c.strip() for c in travel_cats_raw.split(",") if c.strip()]

            summary = get_budget_summary(actual_url, actual_token, actual_file, month=None)

            if "error" in summary:
                result["budget_status"] = "error"
            else:
                total_budgeted = summary.get("total_budgeted", 0) or 0
                total_spent    = summary.get("total_spent", 0)    or 0

                # Filter to travel categories if configured
                cats = summary.get("travel_categories") or []
                if travel_cats and cats:
                    travel_cat_names = {c.lower() for c in travel_cats}
                    filtered = [c for c in cats if c.get("name","").lower() in travel_cat_names]
                    if filtered:
                        total_budgeted = sum(c.get("budgeted", 0) or 0 for c in filtered)
                        total_spent    = sum(c.get("spent",    0) or 0 for c in filtered)

                remaining = max(0, total_budgeted - total_spent)
                result["budget_remaining"] = round(remaining, 2)
                result["budget_total"]     = round(total_budgeted, 2)
                result["budget_month"]     = summary.get("month")
                result["budget_status"]    = "ok"
        except Exception as e:
            logger.warning(f"Dashboard stats: ActualBudget failed: {e}")
            result["budget_status"] = "error"

    return result

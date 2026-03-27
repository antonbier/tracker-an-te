"""
WanderSuite v0.6 — ActualBudget Integration
Synchronisiert Reiseausgaben mit ActualBudget (self-hosted Budget-App).
API Docs: https://actualbudget.org/docs/api/
"""

import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def get_accounts(base_url: str, token: str) -> dict:
    """Alle Konten aus ActualBudget abrufen."""
    url = f"{base_url.rstrip('/')}/v1/accounts"
    try:
        resp = requests.get(url, headers=_headers(token), timeout=10)
        resp.raise_for_status()
        return {"accounts": resp.json()}
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            return {"error": "ActualBudget: Ungültiger Token"}
        return {"error": f"ActualBudget Fehler: {e.response.status_code}"}
    except requests.RequestException as e:
        return {"error": f"Verbindungsfehler: {str(e)}"}


def get_budget_summary(base_url: str, token: str, month: str | None = None) -> dict:
    """
    Budget-Zusammenfassung abrufen.
    month: Format YYYY-MM (default: aktueller Monat)
    """
    if not month:
        month = datetime.now().strftime("%Y-%m")

    url = f"{base_url.rstrip('/')}/v1/budget-months/{month}"
    try:
        resp = requests.get(url, headers=_headers(token), timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # Reise-relevante Kategorien herausfiltern
        travel_keywords = ["reise", "travel", "viaggio", "urlaub", "vacation", "flug", "hotel", "flight"]
        categories = data.get("categoryGroups", [])
        travel_categories = []

        for group in categories:
            for cat in group.get("categories", []):
                name_lower = cat.get("name", "").lower()
                if any(kw in name_lower for kw in travel_keywords):
                    travel_categories.append({
                        "name":      cat.get("name"),
                        "budgeted":  cat.get("budgeted", 0) / 100,  # ActualBudget uses cents
                        "spent":     abs(cat.get("spent", 0)) / 100,
                        "balance":   cat.get("balance", 0) / 100,
                    })

        return {
            "month": month,
            "travel_categories": travel_categories,
            "total_budgeted": sum(c["budgeted"] for c in travel_categories),
            "total_spent":    sum(c["spent"]    for c in travel_categories),
        }

    except requests.HTTPError as e:
        if e.response.status_code == 401:
            return {"error": "ActualBudget: Ungültiger Token"}
        return {"error": f"ActualBudget Fehler: {e.response.status_code}"}
    except requests.RequestException as e:
        return {"error": f"Verbindungsfehler: {str(e)}"}


def add_transaction(
    base_url: str, token: str,
    account_id: str, amount: float,
    payee: str, notes: str = "",
    date: str | None = None,
) -> dict:
    """
    Neue Transaktion in ActualBudget anlegen (z.B. Flugbuchung).
    amount: negativer Wert für Ausgaben (z.B. -450.00)
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    url = f"{base_url.rstrip('/')}/v1/accounts/{account_id}/transactions"
    payload = [{
        "date":    date,
        "amount":  int(amount * 100),  # ActualBudget uses cents
        "payee":   payee,
        "notes":   notes,
        "cleared": False,
    }]

    try:
        resp = requests.post(url, json=payload, headers=_headers(token), timeout=10)
        resp.raise_for_status()
        return {"success": True, "message": f"Transaktion '{payee}' angelegt: {amount} €"}
    except requests.HTTPError as e:
        return {"error": f"ActualBudget Fehler: {e.response.status_code}: {e.response.text[:200]}"}
    except requests.RequestException as e:
        return {"error": f"Verbindungsfehler: {str(e)}"}


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

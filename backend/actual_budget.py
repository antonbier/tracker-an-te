"""
WanderSuite — ActualBudget Integration
Syncs travel expenses with ActualBudget (self-hosted budgeting app).
API Docs: https://actualbudget.org/docs/api/

Authentication: ActualBudget uses its server password as Bearer token.
Amounts are stored in millicents (×1000) in ActualBudget — we divide by 1000 to get euros.
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
                        "budgeted":  cat.get("budgeted", 0) / 1000,  # ActualBudget uses millicents
                        "spent":     abs(cat.get("spent", 0)) / 1000,  # ActualBudget uses millicents
                        "balance":   cat.get("balance", 0) / 1000,  # ActualBudget uses millicents
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
        "amount":  int(amount * 1000),  # ActualBudget uses millicents
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


def get_travel_expenses(
    base_url: str,
    token: str,
    category_names: list[str],
    year: int | None = None,
) -> dict:
    """
    Reise-Transaktionen nach Kategorienamen abrufen.
    Gibt {transactions: [...], total: float} zurück.
    """
    import datetime as dt
    if not year:
        year = dt.date.today().year

    start = f"{year}-01-01"
    end   = f"{year}-12-31"

    # Alle Accounts laden
    accounts_result = get_accounts(base_url, token)
    if "error" in accounts_result:
        return accounts_result

    accounts = accounts_result.get("accounts", [])
    if not accounts:
        return {"error": "Keine Konten in ActualBudget gefunden"}

    # Transaktionen aus allen Konten sammeln
    all_transactions = []
    category_names_lower = [c.strip().lower() for c in category_names if c.strip()]

    for account in accounts:
        account_id = account.get("id")
        if not account_id:
            continue

        url = f"{base_url.rstrip('/')}/v1/accounts/{account_id}/transactions"
        params = {"start_date": start, "end_date": end}

        try:
            resp = requests.get(url, headers=_headers(token), params=params, timeout=15)
            if not resp.ok:
                continue
            transactions = resp.json()
            if isinstance(transactions, dict):
                transactions = transactions.get("data", transactions.get("transactions", []))

            for tx in transactions:
                # Kategorie prüfen
                cat_name = str(tx.get("category_name", tx.get("category", ""))).lower()
                if not category_names_lower or any(c in cat_name for c in category_names_lower):
                    amount_raw = tx.get("amount", 0)
                    # ActualBudget speichert Beträge in Millicent (×1000)
                    amount = float(amount_raw) / 1000

                    all_transactions.append({
                        "date":       tx.get("date", ""),
                        "payee":      tx.get("payee_name", tx.get("payee", "")),
                        "category":   tx.get("category_name", tx.get("category", "")),
                        "amount":     round(amount, 2),
                        "account":    account.get("name", ""),
                        "notes":      tx.get("notes", ""),
                    })

        except requests.RequestException:
            continue

    # Nach Datum sortieren (neueste zuerst)
    all_transactions.sort(key=lambda x: x["date"], reverse=True)

    total = sum(abs(tx["amount"]) for tx in all_transactions if tx["amount"] < 0)

    return {
        "transactions": all_transactions,
        "total_spent":  round(total, 2),
        "year":         year,
        "categories":   category_names,
    }


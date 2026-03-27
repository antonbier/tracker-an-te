"""
WanderSuite v0.6 — REST Routes: /api/budget
ActualBudget Sync.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import logging

from actual_budget import get_accounts, get_budget_summary, add_transaction, get_categories

router = APIRouter()
logger = logging.getLogger(__name__)


class ActualConfig(BaseModel):
    base_url: str
    token:    str
    month:    Optional[str] = None


class ActualTransaction(BaseModel):
    base_url:   str
    token:      str
    account_id: str
    amount:     float
    payee:      str
    notes:      str = ""
    date:       Optional[str] = None


@router.post("/actual/accounts")
def sync_accounts(config: ActualConfig):
    """Alle ActualBudget Konten abrufen."""
    return get_accounts(config.base_url, config.token)


@router.post("/actual/summary")
def sync_summary(config: ActualConfig):
    """Budget-Zusammenfassung inkl. Reise-Kategorien abrufen."""
    return get_budget_summary(config.base_url, config.token, config.month)


@router.post("/actual/transaction")
def create_transaction(data: ActualTransaction):
    """Neue Transaktion in ActualBudget anlegen."""
    return add_transaction(
        base_url=data.base_url, token=data.token,
        account_id=data.account_id, amount=data.amount,
        payee=data.payee, notes=data.notes, date=data.date,
    )


class ExpensesRequest(BaseModel):
    base_url:           str
    token:              str
    category_names:     Optional[list[str]] = None
    year:               Optional[int] = None


@router.post("/actual/expenses")
def get_expenses(data: ExpensesRequest):
    """Reise-Transaktionen nach Kategorie abrufen."""
    from actual_budget import get_travel_expenses
    cats = data.category_names or []
    return get_travel_expenses(data.base_url, data.token, cats, data.year)


@router.post("/actual/debug")
def debug_actual(config: ActualConfig):
    """
    Debug-Endpoint: Zeigt Konten, Kategorien und erste 5 Transaktionen
    damit Feldnamen und Kategorie-IDs geprüft werden können.
    """
    from actual_budget import get_accounts, get_categories, _headers
    import requests as req

    base = config.base_url.rstrip('/')
    hdrs = _headers(config.token)
    result = {}

    # 1. Accounts
    accounts_resp = get_accounts(config.base_url, config.token)
    accounts = accounts_resp.get("accounts", [])
    result["accounts"] = [{"id": a.get("id"), "name": a.get("name")} for a in accounts[:5]]

    # 2. Categories — zeige was /v1/categories zurückgibt
    try:
        r = req.get(f"{base}/v1/categories", headers=hdrs, timeout=10)
        result["categories_status"] = r.status_code
        raw_cats = r.json() if r.ok else r.text[:300]
        cats_list = raw_cats if isinstance(raw_cats, list) else raw_cats.get("categories", raw_cats.get("data", raw_cats)) if isinstance(raw_cats, dict) else raw_cats
        result["categories_raw_sample"] = cats_list[:5] if isinstance(cats_list, list) else cats_list
        result["category_map"] = get_categories(config.base_url, config.token)
    except Exception as e:
        result["categories_error"] = str(e)

    # 3. Erste 5 Transaktionen aus erstem Account — zeige alle Felder
    if accounts:
        first_account = accounts[0]
        try:
            r = req.get(
                f"{base}/v1/accounts/{first_account['id']}/transactions",
                headers=hdrs,
                params={"start_date": "2024-01-01", "end_date": "2025-12-31"},
                timeout=15
            )
            result["transactions_status"] = r.status_code
            txs = r.json() if r.ok else []
            if isinstance(txs, dict):
                txs = txs.get("data", txs.get("transactions", []))
            result["transactions_sample"] = txs[:3]
            result["transactions_total"] = len(txs)
        except Exception as e:
            result["transactions_error"] = str(e)

    return result


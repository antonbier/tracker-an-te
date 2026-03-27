"""
WanderSuite — REST Routes: /api/budget
ActualBudget Sync via actualpy.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class ActualConfig(BaseModel):
    base_url:    str
    password:    str
    budget_file: str
    month:       Optional[str] = None


class ExpensesRequest(BaseModel):
    base_url:       str
    password:       str
    budget_file:    str
    category_names: Optional[list[str]] = None
    year:           Optional[int] = None


@router.post("/actual/files")
def list_files(config: ActualConfig):
    """Verfügbare Budget-Dateien auflisten."""
    from actual_budget import list_budget_files
    return list_budget_files(config.base_url, config.password)


@router.post("/actual/summary")
def sync_summary(config: ActualConfig):
    """Budget-Zusammenfassung inkl. Reise-Kategorien abrufen."""
    from actual_budget import get_budget_summary
    return get_budget_summary(config.base_url, config.password, config.budget_file, config.month)


@router.post("/actual/expenses")
def get_expenses(data: ExpensesRequest):
    """Reise-Transaktionen nach Kategorie abrufen."""
    from actual_budget import get_travel_expenses
    cats = data.category_names or []
    return get_travel_expenses(data.base_url, data.password, data.budget_file, cats, data.year)


@router.post("/actual/debug")
def debug_actual(config: ActualConfig):
    """
    Debug: Liste Budget-Dateien und zeige erste Transaktionen + Kategorien.
    """
    from actual_budget import list_budget_files, get_travel_expenses

    result = {}

    # Budget-Dateien
    files = list_budget_files(config.base_url, config.password)
    result["budget_files"] = files

    if "error" in files:
        return result

    # Erste Transaktionen aus der angegebenen Budget-Datei
    try:
        from actual import Actual
        from actual.queries import get_transactions, get_accounts
        import datetime as dt

        with Actual(base_url=config.base_url, password=config.password, file=config.budget_file) as actual:
            accounts = get_accounts(actual.session)
            result["accounts"] = [{"id": str(a.id), "name": a.name} for a in accounts[:10]]

            txs = get_transactions(
                actual.session,
                start_date=dt.date(dt.date.today().year, 1, 1),
                end_date=dt.date.today(),
            )
            sample = []
            for tx in list(txs)[:5]:
                if tx.tombstone:
                    continue
                sample.append({
                    "date":     str(tx.date),
                    "payee":    tx.payee.name if tx.payee else None,
                    "category": tx.category.name if tx.category else None,
                    "amount":   (tx.amount or 0) / 100,
                    "account":  tx.account.name if tx.account else None,
                    "notes":    tx.notes,
                })
            result["transactions_sample"] = sample

    except Exception as e:
        result["debug_error"] = str(e)

    return result

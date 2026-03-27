"""
WanderSuite v0.6 — REST Routes: /api/budget
ActualBudget Sync.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import logging

from actual_budget import get_accounts, get_budget_summary, add_transaction

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

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
    from actual_budget import list_budget_files, get_travel_expenses, _normalize_date

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
                    "date":     _normalize_date(tx.date),
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



class TransactionsRequest(BaseModel):
    actual_url:   str
    actual_token: str
    actual_file:  Optional[str] = None
    categories:   Optional[str] = None  # komma-getrennt oder None


@router.post("/actual/transactions")
def get_transactions_alias(data: TransactionsRequest):
    """
    Frontend-kompatibler Endpoint.
    Mappt actual_url/actual_token/actual_file → base_url/password/budget_file.
    Gibt { transactions: [...] } zurück.
    """
    from actual_budget import get_travel_expenses, list_budget_files
    import datetime as dt

    base_url    = data.actual_url.rstrip("/")
    password    = data.actual_token
    budget_file = data.actual_file or ""
    cats        = [c.strip() for c in (data.categories or "").split(",") if c.strip()]

    # Falls kein budget_file angegeben: erste verfügbare Datei nehmen
    if not budget_file:
        files_resp = list_budget_files(base_url, password)
        files = files_resp.get("files", [])
        if not files:
            return {"error": "Keine Budget-Dateien gefunden. Bitte Budget-Dateiname in Einstellungen eintragen.", "transactions": []}
        budget_file = files[0].get("name", "")
        logger.info(f"[ActualBudget] Kein Dateiname angegeben, nutze erste Datei: {budget_file}")

    result = get_travel_expenses(base_url, password, budget_file, cats, dt.date.today().year)
    if "error" in result:
        return {"error": result["error"], "transactions": [], "budget_file_used": budget_file}

    return {
        "transactions": result.get("transactions", []),
        "total": result.get("total", 0),
        "budget_file_used": budget_file,
        "categories_used": cats or ["alle"],
    }


@router.post("/actual/list-files")
def list_budget_files_endpoint(data: TransactionsRequest):
    """
    Listet alle Budget-Dateien auf — hilft beim Herausfinden des richtigen Dateinamens.
    Nur actual_url + actual_token nötig.
    """
    from actual_budget import list_budget_files
    result = list_budget_files(data.actual_url.rstrip("/"), data.actual_token)
    return result

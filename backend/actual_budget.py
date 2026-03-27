"""
WanderSuite — ActualBudget Integration
Syncs travel expenses using the official actualpy Python library.

ActualBudget has NO REST API. It uses a local-first sync protocol.
We use actualpy (pip install actualpy) which reimplements the Node.js
@actual-app/api package in Python.

Required settings:
  - actual_url:    URL of the ActualBudget server
  - actual_token:  Server password (stored as actual_token in settings)
  - actual_file:   Budget UUID or name
"""

import logging

logger = logging.getLogger(__name__)


def _get_actual(base_url: str, password: str, budget_file: str):
    try:
        from actual import Actual
    except ImportError:
        raise RuntimeError("actualpy nicht installiert")
    return Actual(base_url=base_url, password=password, file=budget_file, encryption_password=None)


def _normalize_date(d) -> str:
    """
    Normalisiert ActualBudget-Datumswerte auf YYYY-MM-DD.
    actualpy kann je nach Version datetime.date, int (20260314) oder str zurückgeben.
    """
    if not d:
        return ""
    s = str(d)
    if len(s) == 8 and s.isdigit():
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return s[:10]


def get_budget_summary(base_url: str, password: str, budget_file: str, month: str | None = None) -> dict:
    from datetime import datetime, date
    if not month:
        month = datetime.now().strftime("%Y-%m")

    try:
        with _get_actual(base_url, password, budget_file) as actual:
            from actual.queries import get_budgets
            year, mon = map(int, month.split("-"))
            budgets = get_budgets(actual.session, month=date(year, mon, 1))

            travel_keywords = ["reise", "travel", "viaggio", "urlaub", "vacation", "flug", "hotel", "flight"]
            travel_categories = []

            for b in budgets:
                name = b.category.name if b.category else ""
                if any(kw in name.lower() for kw in travel_keywords):
                    travel_categories.append({
                        "name":     name,
                        "budgeted": (b.budgeted or 0) / 100,
                        "spent":    abs(b.activity or 0) / 100,
                        "balance":  (b.balance or 0) / 100,
                    })

            return {
                "month": month,
                "travel_categories": travel_categories,
                "total_budgeted": sum(c["budgeted"] for c in travel_categories),
                "total_spent":    sum(c["spent"]    for c in travel_categories),
            }
    except Exception as e:
        logger.error(f"[ActualBudget] get_budget_summary: {e}")
        return {"error": str(e)}


def get_travel_expenses(
    base_url: str,
    password: str,
    budget_file: str,
    category_names: list[str],
    year: int | None = None,
) -> dict:
    import datetime as dt
    if not year:
        year = dt.date.today().year

    year_prefix = str(year)
    category_names_lower = [c.strip().lower() for c in category_names if c.strip()]

    try:
        with _get_actual(base_url, password, budget_file) as actual:
            from actual.queries import get_transactions

            # Kein start/end_date — actualpy-Datumsvergleich ist mit Integer-Dates unzuverlässig.
            # Wir laden alle Transaktionen und filtern selbst nach normalize_date.
            txs = get_transactions(actual.session)

            all_transactions = []
            for tx in txs:
                if tx.transfer_id or tx.tombstone:
                    continue

                date_str = _normalize_date(tx.date)

                # Jahresfilter
                if not date_str.startswith(year_prefix):
                    continue

                cat_name = tx.category.name if tx.category else ""

                # Kategorie-Filter
                if category_names_lower and not any(c in cat_name.lower() for c in category_names_lower):
                    continue

                amount = (tx.amount or 0) / 100

                all_transactions.append({
                    "date":     date_str,
                    "payee":    tx.payee.name if tx.payee else "",
                    "category": cat_name,
                    "amount":   round(amount, 2),
                    "account":  tx.account.name if tx.account else "",
                    "notes":    tx.notes or "",
                })

            all_transactions.sort(key=lambda x: x["date"], reverse=True)
            total = sum(abs(tx["amount"]) for tx in all_transactions if tx["amount"] < 0)

            logger.info(f"[ActualBudget] {len(all_transactions)} Transaktionen gefunden (Jahr {year}, Filter: {category_names_lower or 'alle'})")

            return {
                "transactions": all_transactions,
                "total_spent":  round(total, 2),
                "year":         year,
                "categories":   category_names,
            }
    except Exception as e:
        logger.error(f"[ActualBudget] get_travel_expenses: {e}")
        return {"error": str(e)}


def list_budget_files(base_url: str, password: str) -> dict:
    try:
        from actual import Actual
        with Actual(base_url=base_url, password=password) as actual:
            files = actual.list_user_files()
            return {"files": [{"id": f.file_id, "name": f.name} for f in files.data]}
    except Exception as e:
        return {"error": str(e)}

"""
WanderSuite — crud/documents.py
Dokumenten-Vault: reine DB-Zugriffsschicht für die documents-Tabelle (Metadaten).
Der verschlüsselte Dateiinhalt selbst wird über document_vault.py verwaltet.
"""

from core.database import db


def create_document(user_id: int, trip_id: int | None, doc_type: str, title: str,
                     stored_filename: str, orig_filename: str | None, mime_type: str | None,
                     size_bytes: int, expiry_date: str | None, notes: str | None) -> int:
    with db() as conn:
        cur = conn.execute(
            """INSERT INTO documents
               (user_id, trip_id, doc_type, title, filename, orig_filename, mime_type,
                size_bytes, expiry_date, notes, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,datetime('now'))""",
            (user_id, trip_id, doc_type, title, stored_filename, orig_filename, mime_type,
             size_bytes, expiry_date, notes)
        )
        return cur.lastrowid


def list_documents(user_id: int, trip_id: int | None = None) -> list[dict]:
    with db() as conn:
        if trip_id is not None:
            rows = conn.execute(
                "SELECT * FROM documents WHERE user_id=? AND trip_id=? ORDER BY created_at DESC",
                (user_id, trip_id)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM documents WHERE user_id=? ORDER BY created_at DESC",
                (user_id,)
            ).fetchall()
    return [dict(r) for r in rows]


def get_document(doc_id: int, user_id: int) -> dict | None:
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE id=? AND user_id=?", (doc_id, user_id)
        ).fetchone()
    return dict(row) if row else None


def update_document(doc_id: int, user_id: int, fields: dict) -> bool:
    """Partial update of metadata. Changing expiry_date resets expiry_notified_at
    so a renewed document can trigger a fresh reminder later."""
    allowed = {"title", "doc_type", "expiry_date", "notes", "trip_id"}
    sets, params = [], []
    for k, v in fields.items():
        if k in allowed:
            sets.append(f"{k}=?")
            params.append(v)
    if not sets:
        return False
    if "expiry_date" in fields:
        sets.append("expiry_notified_at=NULL")
    params += [doc_id, user_id]
    with db() as conn:
        cur = conn.execute(
            f"UPDATE documents SET {', '.join(sets)} WHERE id=? AND user_id=?", params
        )
    return cur.rowcount > 0


def delete_document(doc_id: int, user_id: int) -> dict | None:
    """Deletes the DB row and returns the deleted row (caller removes the file on disk)."""
    doc = get_document(doc_id, user_id)
    if not doc:
        return None
    with db() as conn:
        conn.execute("DELETE FROM documents WHERE id=? AND user_id=?", (doc_id, user_id))
    return doc


def list_expiring_documents(days_ahead: int = 90) -> list[dict]:
    """All documents expiring within `days_ahead` days (or already expired) that
    haven't been notified about yet. Used by the daily scheduler job."""
    with db() as conn:
        rows = conn.execute(
            """SELECT * FROM documents
               WHERE expiry_date IS NOT NULL
                 AND expiry_date <= date('now', ?)
                 AND expiry_notified_at IS NULL""",
            (f"+{days_ahead} days",)
        ).fetchall()
    return [dict(r) for r in rows]


def mark_document_notified(doc_id: int) -> None:
    with db() as conn:
        conn.execute("UPDATE documents SET expiry_notified_at=datetime('now') WHERE id=?", (doc_id,))

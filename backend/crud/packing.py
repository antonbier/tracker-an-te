"""
WanderSuite — crud/packing.py
Packlisten-Vorlagen: wiederverwendbare, trip-unabhängige Packlisten.
Item-Mutationen (toggle/delete) prüfen die Ownership immer per JOIN gegen
packing_templates.user_id — IDOR-Schutz analog Tracker-Ownership (siehe CLAUDE.md).
"""

from core.database import db


def create_template(user_id: int, name: str) -> int:
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO packing_templates (user_id, name, created_at) VALUES (?,?,datetime('now'))",
            (user_id, name)
        )
        return cur.lastrowid


def list_templates(user_id: int) -> list[dict]:
    with db() as conn:
        templates = conn.execute(
            "SELECT * FROM packing_templates WHERE user_id=? ORDER BY created_at ASC",
            (user_id,)
        ).fetchall()
        result = []
        for tpl in templates:
            items = conn.execute(
                "SELECT * FROM packing_template_items WHERE template_id=? ORDER BY sort_order ASC, id ASC",
                (tpl["id"],)
            ).fetchall()
            result.append({**dict(tpl), "items": [dict(i) for i in items]})
    return result


def rename_template(template_id: int, user_id: int, name: str) -> bool:
    with db() as conn:
        cur = conn.execute(
            "UPDATE packing_templates SET name=? WHERE id=? AND user_id=?",
            (name, template_id, user_id)
        )
    return cur.rowcount > 0


def delete_template(template_id: int, user_id: int) -> bool:
    with db() as conn:
        cur = conn.execute(
            "DELETE FROM packing_templates WHERE id=? AND user_id=?", (template_id, user_id)
        )
    return cur.rowcount > 0


def add_item(template_id: int, user_id: int, text: str, category: str = "general") -> int | None:
    """Returns the new item id, or None if the template isn't owned by user_id."""
    with db() as conn:
        owns = conn.execute(
            "SELECT 1 FROM packing_templates WHERE id=? AND user_id=?", (template_id, user_id)
        ).fetchone()
        if not owns:
            return None
        max_order = conn.execute(
            "SELECT COALESCE(MAX(sort_order), -1) FROM packing_template_items WHERE template_id=?",
            (template_id,)
        ).fetchone()[0]
        cur = conn.execute(
            """INSERT INTO packing_template_items (template_id, text, category, sort_order, created_at)
               VALUES (?,?,?,?,datetime('now'))""",
            (template_id, text, category, max_order + 1)
        )
        return cur.lastrowid


def toggle_item(item_id: int, user_id: int) -> bool:
    with db() as conn:
        row = conn.execute(
            """SELECT i.id, i.is_done FROM packing_template_items i
               JOIN packing_templates t ON t.id = i.template_id
               WHERE i.id=? AND t.user_id=?""",
            (item_id, user_id)
        ).fetchone()
        if not row:
            return False
        conn.execute(
            "UPDATE packing_template_items SET is_done=? WHERE id=?",
            (0 if row["is_done"] else 1, item_id)
        )
    return True


def delete_item(item_id: int, user_id: int) -> bool:
    with db() as conn:
        cur = conn.execute(
            """DELETE FROM packing_template_items WHERE id=? AND template_id IN
               (SELECT id FROM packing_templates WHERE user_id=?)""",
            (item_id, user_id)
        )
    return cur.rowcount > 0


def reset_template(template_id: int, user_id: int) -> bool:
    """Setzt is_done aller Items auf 0 zurück — vor der nächsten Reise wiederverwenden."""
    with db() as conn:
        owns = conn.execute(
            "SELECT 1 FROM packing_templates WHERE id=? AND user_id=?", (template_id, user_id)
        ).fetchone()
        if not owns:
            return False
        conn.execute("UPDATE packing_template_items SET is_done=0 WHERE template_id=?", (template_id,))
    return True

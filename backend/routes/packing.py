"""
WanderSuite — /api/packing-templates
Wiederverwendbare Packlisten-Vorlagen, unabhängig von einzelnen Trips.
"""

import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth_jwt import get_current_user
from crud.packing import (
    add_item,
    create_template,
    create_template_with_items,
    delete_item,
    delete_template,
    list_templates,
    rename_template,
    reset_template,
    toggle_item,
)

router = APIRouter()

_TAG_RE = re.compile(r"<[^>]+>")

# ── Statische Katalog-Vorlagen ─────────────────────────────────────────────────
# Fest eingebaute Listen zum Ein-Klick-Übernehmen — kein KI-Aufwand nötig.
# KI-generierte Listen (basierend auf Ziel/Dauer/Saison) wären eine spätere
# Erweiterung, die auf demselben create_template_with_items() aufbauen würde.
CATALOGS = {
    "beach": {
        "label": "🏖️ Strandurlaub", "icon": "🏖️",
        "items": [
            ("Badehose / Bikini", "clothing"), ("Sonnencreme", "toiletries"),
            ("Sonnenbrille", "other"), ("Strandtuch", "other"),
            ("Flip-Flops", "clothing"), ("After-Sun", "toiletries"),
            ("Wasserflasche", "other"), ("Buch / E-Reader", "other"),
        ],
    },
    "city": {
        "label": "🏙️ Städtetrip", "icon": "🏙️",
        "items": [
            ("Bequeme Schuhe", "clothing"), ("Offline-Stadtplan / Maps", "documents"),
            ("Kamera", "electronics"), ("Powerbank", "electronics"),
            ("Kleiner Rucksack", "other"), ("Regenschirm", "other"),
        ],
    },
    "winter": {
        "label": "❄️ Winterurlaub", "icon": "❄️",
        "items": [
            ("Skijacke", "clothing"), ("Handschuhe", "clothing"),
            ("Mütze", "clothing"), ("Thermounterwäsche", "clothing"),
            ("Skibrille", "other"), ("Sonnencreme (Schnee!)", "toiletries"),
            ("Warme Socken", "clothing"),
        ],
    },
    "business": {
        "label": "💼 Business-Trip", "icon": "💼",
        "items": [
            ("Anzug / Blazer", "clothing"), ("Laptop + Ladekabel", "electronics"),
            ("Visitenkarten", "documents"), ("Steckdosen-Adapter", "electronics"),
            ("Formelle Schuhe", "clothing"),
        ],
    },
    "hiking": {
        "label": "🥾 Wanderurlaub", "icon": "🥾",
        "items": [
            ("Wanderschuhe", "clothing"), ("Regenjacke", "clothing"),
            ("Rucksack", "other"), ("Erste-Hilfe-Set", "other"),
            ("Trekkingstöcke", "other"), ("Kopflampe", "electronics"),
            ("Wanderkarte", "documents"),
        ],
    },
}


def _sanitize(value: str, max_len: int = 200) -> str:
    return _TAG_RE.sub("", str(value)).strip()[:max_len]


def _uid(user: dict) -> int:
    return user.get("id", 1) or 1


class TemplateCreate(BaseModel):
    name: str


class TemplateRename(BaseModel):
    name: str


class ItemCreate(BaseModel):
    text: str
    category: str = "general"


class FromCatalogRequest(BaseModel):
    catalog_key: str
    name: Optional[str] = None


@router.get("/catalog")
def get_catalogs():
    """Katalog-Vorschau für die Übernehmen-Auswahl — kein Auth nötig, da statisch."""
    return [
        {"key": key, "label": c["label"], "icon": c["icon"], "items": [t for t, _ in c["items"]]}
        for key, c in CATALOGS.items()
    ]


@router.post("/from-catalog")
def create_from_catalog(data: FromCatalogRequest, user: dict = Depends(get_current_user)):
    catalog = CATALOGS.get(data.catalog_key)
    if not catalog:
        raise HTTPException(404, f"Katalog '{data.catalog_key}' nicht gefunden")
    name = _sanitize(data.name) if data.name else catalog["label"]
    tpl_id = create_template_with_items(_uid(user), name, catalog["items"])
    return {"id": tpl_id, "message": "Vorlage übernommen ✓"}


@router.post("")
def create(data: TemplateCreate, user: dict = Depends(get_current_user)):
    name = _sanitize(data.name) or "Packliste"
    tpl_id = create_template(_uid(user), name)
    return {"id": tpl_id, "message": "Angelegt ✓"}


@router.get("")
def get_all(user: dict = Depends(get_current_user)):
    return list_templates(_uid(user))


@router.patch("/{template_id}")
def rename(template_id: int, data: TemplateRename, user: dict = Depends(get_current_user)):
    if not rename_template(template_id, _uid(user), _sanitize(data.name)):
        raise HTTPException(404, "Vorlage nicht gefunden")
    return {"message": "Umbenannt ✓"}


@router.delete("/{template_id}")
def remove(template_id: int, user: dict = Depends(get_current_user)):
    if not delete_template(template_id, _uid(user)):
        raise HTTPException(404, "Vorlage nicht gefunden")
    return {"message": "Gelöscht ✓"}


@router.post("/{template_id}/items")
def add(template_id: int, data: ItemCreate, user: dict = Depends(get_current_user)):
    text = _sanitize(data.text)
    if not text:
        raise HTTPException(400, "Text darf nicht leer sein")
    item_id = add_item(template_id, _uid(user), text, data.category)
    if item_id is None:
        raise HTTPException(404, "Vorlage nicht gefunden")
    return {"id": item_id, "message": "Hinzugefügt ✓"}


@router.patch("/items/{item_id}/toggle")
def toggle(item_id: int, user: dict = Depends(get_current_user)):
    if not toggle_item(item_id, _uid(user)):
        raise HTTPException(404, "Item nicht gefunden")
    return {"message": "OK"}


@router.delete("/items/{item_id}")
def remove_item(item_id: int, user: dict = Depends(get_current_user)):
    if not delete_item(item_id, _uid(user)):
        raise HTTPException(404, "Item nicht gefunden")
    return {"message": "Gelöscht ✓"}


@router.post("/{template_id}/reset")
def reset(template_id: int, user: dict = Depends(get_current_user)):
    if not reset_template(template_id, _uid(user)):
        raise HTTPException(404, "Vorlage nicht gefunden")
    return {"message": "Zurückgesetzt ✓"}

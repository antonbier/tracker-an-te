"""
WanderSuite — /api/packing-templates
Wiederverwendbare Packlisten-Vorlagen, unabhängig von einzelnen Trips.
"""

import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth_jwt import get_current_user
from crud.packing import (
    add_item,
    create_template,
    delete_item,
    delete_template,
    list_templates,
    rename_template,
    reset_template,
    toggle_item,
)

router = APIRouter()

_TAG_RE = re.compile(r"<[^>]+>")


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

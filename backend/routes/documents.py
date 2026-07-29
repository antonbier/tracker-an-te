"""
WanderSuite — /api/documents
Dokumenten-Vault: Pass, Visum, Impfnachweis, Buchungsbestätigungen etc.
Dateiinhalt liegt Fernet-verschlüsselt auf Disk (document_vault.py), Metadaten in der
documents-Tabelle (crud/documents.py).
"""

import logging
import re
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

import document_vault
from auth_jwt import get_current_user
from crud.documents import (
    create_document,
    delete_document,
    get_document,
    list_documents,
    update_document,
)

router = APIRouter()
logger = logging.getLogger(__name__)

DOC_TYPES = {"passport", "visa", "vaccination", "insurance", "booking", "other"}

# Minimales Sanitizing für Titel/Notizen (analog routes/ws_trips.py) — keine HTML-Tags in Freitextfeldern.
_TAG_RE = re.compile(r"<[^>]+>")


def _sanitize(value: str | None, max_len: int = 300) -> str | None:
    if value is None:
        return None
    v = _TAG_RE.sub("", str(value)).strip()[:max_len]
    return v or None


def _uid(user: dict) -> int:
    return user.get("id", 1) or 1


@router.post("")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    doc_type: str = Form("other"),
    trip_id: Optional[int] = Form(None),
    expiry_date: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    user: dict = Depends(get_current_user),
):
    if doc_type not in DOC_TYPES:
        raise HTTPException(400, f"doc_type muss eines von {DOC_TYPES} sein")
    content = await file.read()
    if len(content) > document_vault.MAX_FILE_SIZE:
        raise HTTPException(413, "Datei zu groß (max. 20 MB)")
    if not content:
        raise HTTPException(400, "Leere Datei")

    uid = _uid(user)
    stored_filename = document_vault.save_encrypted_file(uid, content)
    doc_id = create_document(
        user_id=uid,
        trip_id=trip_id,
        doc_type=doc_type,
        title=_sanitize(title) or file.filename or "Dokument",
        stored_filename=stored_filename,
        orig_filename=file.filename,
        mime_type=file.content_type,
        size_bytes=len(content),
        expiry_date=expiry_date or None,
        notes=_sanitize(notes, max_len=1000),
    )
    return {"id": doc_id, "message": "Dokument gespeichert ✓"}


@router.get("")
def get_documents(trip_id: Optional[int] = None, user: dict = Depends(get_current_user)):
    return list_documents(_uid(user), trip_id=trip_id)


@router.get("/{doc_id}/download")
def download_document(doc_id: int, user: dict = Depends(get_current_user)):
    uid = _uid(user)
    doc = get_document(doc_id, uid)
    if not doc:
        raise HTTPException(404, "Dokument nicht gefunden")
    content = document_vault.read_encrypted_file(uid, doc["filename"])
    if content is None:
        raise HTTPException(404, "Datei nicht mehr vorhanden")
    filename = doc.get("orig_filename") or f"document-{doc_id}"
    return Response(
        content=content,
        media_type=doc.get("mime_type") or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    doc_type: Optional[str] = None
    trip_id: Optional[int] = None
    expiry_date: Optional[str] = None
    notes: Optional[str] = None


@router.patch("/{doc_id}")
def patch_document(doc_id: int, data: DocumentUpdate, user: dict = Depends(get_current_user)):
    uid = _uid(user)
    if not get_document(doc_id, uid):
        raise HTTPException(404, "Dokument nicht gefunden")
    if data.doc_type is not None and data.doc_type not in DOC_TYPES:
        raise HTTPException(400, f"doc_type muss eines von {DOC_TYPES} sein")
    fields = data.model_dump(exclude_unset=True)
    if "title" in fields:
        fields["title"] = _sanitize(fields["title"])
    if "notes" in fields:
        fields["notes"] = _sanitize(fields["notes"], max_len=1000)
    update_document(doc_id, uid, fields)
    return {"message": "Aktualisiert ✓"}


@router.delete("/{doc_id}")
def remove_document(doc_id: int, user: dict = Depends(get_current_user)):
    uid = _uid(user)
    doc = delete_document(doc_id, uid)
    if not doc:
        raise HTTPException(404, "Dokument nicht gefunden")
    document_vault.delete_file(uid, doc["filename"])
    return {"message": "Gelöscht ✓"}

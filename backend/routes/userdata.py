"""
WanderSuite — REST Routes: /api/userdata
Client-side data persistence for browser-agnostic storage.

Persists data that was previously localStorage-only:
  ws-trips      — manual travel trips [{name, cost, date, source?}]
  ws-budget     — total budget amount (string, EUR)
  ws-bucketlist — bucket list items [{id, dest, when, emoji, added}]

All values are stored as JSON strings and returned as-is.
The frontend is responsible for JSON serialisation/deserialisation.

No encryption needed — this is user preference data, not secrets.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from database import save_user_data, get_user_data

router = APIRouter()
logger = logging.getLogger(__name__)

# Allowed keys — prevent arbitrary data storage
ALLOWED_KEYS = {"ws-trips", "ws-budget", "ws-bucketlist"}


class UserDataPayload(BaseModel):
    value: str  # JSON string


@router.get("/{key}")
def get_data(key: str):
    """
    Retrieve stored user data by key.
    Returns {key, value} or 404 if not found.
    """
    if key not in ALLOWED_KEYS:
        raise HTTPException(400, f"Unknown key: {key}. Allowed: {sorted(ALLOWED_KEYS)}")
    value = get_user_data(key)
    if value is None:
        raise HTTPException(404, f"No data stored for key: {key}")
    return {"key": key, "value": value}


@router.put("/{key}")
def set_data(key: str, data: UserDataPayload):
    """
    Store user data for key (upsert).
    value must be a valid JSON string.
    """
    if key not in ALLOWED_KEYS:
        raise HTTPException(400, f"Unknown key: {key}. Allowed: {sorted(ALLOWED_KEYS)}")
    import json
    try:
        json.loads(data.value)  # validate JSON
    except json.JSONDecodeError as e:
        raise HTTPException(422, f"value must be valid JSON: {e}")
    save_user_data(key, data.value)
    logger.info(f"[UserData] Saved {key} ({len(data.value)} bytes)")
    return {"key": key, "saved": True}


@router.get("")
def get_all():
    """Return all stored user data keys and values."""
    result = {}
    for key in ALLOWED_KEYS:
        value = get_user_data(key)
        if value is not None:
            result[key] = value
    return result

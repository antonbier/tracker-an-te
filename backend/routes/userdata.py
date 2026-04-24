"""
WanderSuite — /api/userdata (Multi-User)
Each user has their own trips, budget, bucketlist.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging, json

from crud.trips import save_user_data, get_user_data
from auth_jwt import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_KEYS = {"ws-trips", "ws-budget", "ws-bucketlist", "ws-budget-years"}


class UserDataPayload(BaseModel):
    value: str


def _uid(user: dict) -> int:
    """Return user_id. Guest (id=0) → use 1 as default bucket."""
    return user.get("id", 1) or 1


@router.get("/{key}")
def get_data(key: str, user: dict = Depends(get_current_user)):
    if key not in ALLOWED_KEYS:
        raise HTTPException(400, f"Unknown key: {key}")
    value = get_user_data(key, user_id=_uid(user))
    if value is None:
        raise HTTPException(404, f"No data for key: {key}")
    return {"key": key, "value": value}


@router.put("/{key}")
def set_data(key: str, data: UserDataPayload, user: dict = Depends(get_current_user)):
    if key not in ALLOWED_KEYS:
        raise HTTPException(400, f"Unknown key: {key}")
    try:
        json.loads(data.value)
    except json.JSONDecodeError as e:
        raise HTTPException(422, f"value must be valid JSON: {e}")
    save_user_data(key, data.value, user_id=_uid(user))
    return {"key": key, "saved": True}


@router.get("")
def get_all(user: dict = Depends(get_current_user)):
    result = {}
    for key in ALLOWED_KEYS:
        value = get_user_data(key, user_id=_uid(user))
        if value is not None:
            result[key] = value
    return result

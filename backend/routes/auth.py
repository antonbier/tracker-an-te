"""
WanderSuite — Auth Routes
/api/status    — public: app state (auth enabled? needs setup?)
/api/auth/*    — public: setup + login
/api/admin/*   — admin only: user management
"""

import os
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr

from auth_db import (
    count_users, get_user_by_email, create_user, update_password,
    list_users, delete_user, verify_password,
)
from auth_jwt import create_token, get_current_user, require_admin, AUTH_ENABLED

router_status = APIRouter()
router_auth   = APIRouter()
router_admin  = APIRouter()

logger = logging.getLogger(__name__)


# ══ /api/status ══════════════════════════════════════════════════════════════

@router_status.get("/status")
def get_status():
    """
    Public endpoint — frontend polls this on startup.
    Returns:
        auth_enabled: bool  — is AUTH_ENABLED=true in env?
        needs_setup:  bool  — true when no users exist yet (first run)
    """
    return {
        "auth_enabled": AUTH_ENABLED,
        "needs_setup":  AUTH_ENABLED and count_users() == 0,
    }


# ══ /api/auth/* ══════════════════════════════════════════════════════════════

class SetupPayload(BaseModel):
    email:    str
    password: str

class LoginPayload(BaseModel):
    email:    str
    password: str

class PasswordChangePayload(BaseModel):
    current_password: str
    new_password:     str


@router_auth.post("/auth/setup")
def setup(data: SetupPayload):
    """
    Create the first admin user. Only allowed when users table is empty.
    Returns JWT so the UI can log the admin in immediately after setup.
    """
    if not AUTH_ENABLED:
        raise HTTPException(400, "AUTH_ENABLED=false — Setup nicht nötig.")
    if count_users() > 0:
        raise HTTPException(409, "Setup bereits abgeschlossen. Bitte einloggen.")
    if len(data.password) < 8:
        raise HTTPException(422, "Passwort muss mindestens 8 Zeichen haben.")

    user = create_user(data.email, data.password, role="admin")
    token = create_token(user["id"], user["email"], user["role"])
    logger.info(f"[Auth] Erster Admin erstellt: {user['email']}")
    return {"token": token, "user": {"email": user["email"], "role": user["role"]}}


@router_auth.post("/auth/login")
def login(data: LoginPayload):
    """
    Authenticate with email + password. Returns a 30-day JWT on success.
    """
    if not AUTH_ENABLED:
        raise HTTPException(400, "AUTH_ENABLED=false — kein Login erforderlich.")

    user = get_user_by_email(data.email)
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(401, "E-Mail oder Passwort falsch.")

    token = create_token(user["id"], user["email"], user["role"])
    logger.info(f"[Auth] Login: {user['email']}")
    return {"token": token, "user": {"email": user["email"], "role": user["role"]}}


@router_auth.post("/auth/change-password")
def change_password(
    data: PasswordChangePayload,
    current_user: dict = Depends(get_current_user),
):
    """Allow authenticated user to change their own password."""
    user = get_user_by_email(current_user["email"])
    if not user:
        raise HTTPException(404, "User nicht gefunden.")
    if not verify_password(data.current_password, user["password_hash"]):
        raise HTTPException(401, "Aktuelles Passwort falsch.")
    if len(data.new_password) < 8:
        raise HTTPException(422, "Neues Passwort muss mindestens 8 Zeichen haben.")
    update_password(current_user["id"], data.new_password)
    return {"message": "Passwort geändert ✓"}


@router_auth.get("/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """Return the current user's public profile."""
    return {"id": current_user["id"], "email": current_user["email"], "role": current_user["role"]}


# ══ /api/admin/* — admin only ════════════════════════════════════════════════

class CreateUserPayload(BaseModel):
    email:    str
    password: str
    role:     str = "user"


@router_admin.get("/admin/users")
def admin_list_users(admin: dict = Depends(require_admin)):
    """List all users (admin only)."""
    return list_users()


@router_admin.post("/admin/users", status_code=201)
def admin_create_user(data: CreateUserPayload, admin: dict = Depends(require_admin)):
    """Create a new user (admin only)."""
    if data.role not in ("admin", "user"):
        raise HTTPException(422, "role muss 'admin' oder 'user' sein.")
    if len(data.password) < 8:
        raise HTTPException(422, "Passwort muss mindestens 8 Zeichen haben.")
    try:
        user = create_user(data.email, data.password, data.role)
    except ValueError as e:
        raise HTTPException(409, str(e))
    return user


@router_admin.delete("/admin/users/{user_id}")
def admin_delete_user(user_id: int, admin: dict = Depends(require_admin)):
    """Delete a user (admin only). Admins cannot delete themselves."""
    if user_id == admin["id"]:
        raise HTTPException(400, "Du kannst dich nicht selbst löschen.")
    if not delete_user(user_id):
        raise HTTPException(404, "User nicht gefunden.")
    return {"message": f"User {user_id} gelöscht ✓"}

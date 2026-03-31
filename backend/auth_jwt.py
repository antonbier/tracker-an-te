"""
WanderSuite — JWT Middleware & Auth Dependencies

AUTH_ENABLED=false → GUEST_USER (id=0, admin role) passes through.
AUTH_ENABLED=true  → Bearer JWT required.

Routes use get_current_user() to get {id, email, role}.
Pass user["id"] to DB functions for per-user data isolation.
id=0 (guest) → DB functions return all data (no filter).
"""

import os
import jwt
import logging
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

AUTH_ENABLED    = os.getenv("AUTH_ENABLED", "false").lower() == "true"
JWT_SECRET      = os.getenv("JWT_SECRET", "wandersuite-dev-secret-not-for-production")
JWT_ALGO        = "HS256"
JWT_EXPIRY_DAYS = 30

if AUTH_ENABLED and JWT_SECRET == "wandersuite-dev-secret-not-for-production":
    logger.warning("⚠️  JWT_SECRET is the default dev value. Set a real secret in .env!")

_bearer = HTTPBearer(auto_error=False)

# Guest user: id=0 so DB functions skip user_id filter → sees all data
GUEST_USER = {"id": 0, "email": "guest@wandersuite.local", "role": "admin"}


def create_token(user_id: int, email: str, role: str) -> str:
    payload = {
        "sub":   str(user_id),
        "email": email,
        "role":  role,
        "exp":   datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRY_DAYS),
        "iat":   datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    if not AUTH_ENABLED:
        return GUEST_USER

    if not creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kein Token — bitte einloggen.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[JWT_ALGO])
        return {
            "id":    int(payload["sub"]),
            "email": payload["email"],
            "role":  payload["role"],
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token abgelaufen.")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Ungültiger Token: {e}")


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin-Rechte erforderlich.")
    return user

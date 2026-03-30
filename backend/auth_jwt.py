"""
WanderSuite — JWT Middleware & Auth Dependencies
Handles token creation, validation, and FastAPI dependency injection.

When AUTH_ENABLED=false (default): all protected routes pass through with
a synthetic "guest" identity — existing behaviour preserved completely.

When AUTH_ENABLED=true: Bearer JWT required on all /api/* routes except:
  GET  /api/status
  POST /api/auth/setup
  POST /api/auth/login
  GET  /health
  GET  /
"""

import os
import jwt
import logging
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"
JWT_SECRET   = os.getenv("JWT_SECRET", "wandersuite-dev-secret-not-for-production")
JWT_ALGO     = "HS256"
JWT_EXPIRY_DAYS = 30

if AUTH_ENABLED and JWT_SECRET == "wandersuite-dev-secret-not-for-production":
    logger.warning("⚠️  JWT_SECRET is the default dev value. Set a real secret in .env!")

# HTTPBearer is optional so it doesn't break routes when auth is disabled
_bearer = HTTPBearer(auto_error=False)

# Synthetic guest user used when AUTH_ENABLED=false
GUEST_USER = {"id": 0, "email": "guest@wandersuite.local", "role": "admin"}


# ── Token creation ────────────────────────────────────────────────────────────

def create_token(user_id: int, email: str, role: str) -> str:
    """Create a signed JWT valid for JWT_EXPIRY_DAYS days."""
    payload = {
        "sub":   str(user_id),
        "email": email,
        "role":  role,
        "exp":   datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRY_DAYS),
        "iat":   datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


# ── FastAPI dependency ────────────────────────────────────────────────────────

def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    """
    FastAPI dependency that returns the current authenticated user.

    - AUTH_ENABLED=false → always returns GUEST_USER (no token needed)
    - AUTH_ENABLED=true  → validates Bearer JWT, raises 401 on failure

    Usage in route:
        @router.get("/")
        def my_route(user: dict = Depends(get_current_user)):
            return {"user_id": user["id"]}
    """
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
        raise HTTPException(status_code=401, detail="Token abgelaufen — bitte neu einloggen.")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Ungültiger Token: {e}")


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Dependency that additionally requires role='admin'."""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin-Rechte erforderlich.")
    return user

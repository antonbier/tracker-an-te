"""
WanderSuite — WebAuthn / Passkey Routes
"""

import os
import json
import base64
import logging
from urllib.parse import urlparse
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

import webauthn
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    ResidentKeyRequirement,
)
from webauthn.helpers.cose import COSEAlgorithmIdentifier

from auth_db import (
    get_user_by_email, get_user_by_id, create_user,
    save_credential, get_credential, list_credentials,
    update_sign_count, delete_credential,
    save_challenge, consume_challenge,
)
from auth_jwt import create_token, get_current_user, AUTH_ENABLED

router = APIRouter()
logger = logging.getLogger(__name__)

_RP_ID_ENV   = os.getenv("WEBAUTHN_RP_ID",   "localhost")
_RP_NAME_ENV = os.getenv("WEBAUTHN_RP_NAME",  "WanderSuite")
_ORIGIN_ENV  = os.getenv("WEBAUTHN_ORIGIN",   "http://localhost:8767")


def _get_rp(request: Request):
    """
    Derive RP_ID and ORIGIN from the HTTP request.
    Priority:
      1. Explicit env vars (WEBAUTHN_RP_ID != "localhost")
      2. HTTP Origin header (set by browser on every cross-origin/same-origin POST)
      3. Env var fallback
    """
    # 1. Explicit env config always wins
    if _RP_ID_ENV != "localhost":
        logger.info(f"[Passkey] Using env config: rp_id={_RP_ID_ENV} origin={_ORIGIN_ENV}")
        return _RP_ID_ENV, _RP_NAME_ENV, _ORIGIN_ENV

    # 2. Browser always sends Origin header on POST requests
    origin_header = request.headers.get("origin", "").strip()
    if origin_header:
        parsed = urlparse(origin_header)
        hostname = parsed.hostname or ""
        if hostname:
            rp_id = hostname  # must be registrable domain suffix of origin
            origin = f"{parsed.scheme}://{parsed.netloc}"
            logger.info(f"[Passkey] Derived from Origin header: rp_id={rp_id} origin={origin}")
            return rp_id, _RP_NAME_ENV, origin

    # 3. Fallback to env vars
    logger.warning(f"[Passkey] No Origin header found, using env fallback: rp_id={_RP_ID_ENV}")
    return _RP_ID_ENV, _RP_NAME_ENV, _ORIGIN_ENV


# ── Register ──────────────────────────────────────────────────────────────────

class RegisterBeginPayload(BaseModel):
    device_name: str = "Passkey"


@router.post("/register/begin")
def register_begin(data: RegisterBeginPayload, request: Request, current_user: dict = Depends(get_current_user)):
    """Start passkey registration for the currently logged-in user."""
    rp_id, rp_name, origin = _get_rp(request)

    user = get_user_by_id(current_user["id"])
    if not user:
        raise HTTPException(404, "User nicht gefunden.")

    user_id_bytes = str(current_user["id"]).encode()

    try:
        options = webauthn.generate_registration_options(
            rp_id=rp_id,
            rp_name=rp_name,
            user_id=user_id_bytes,
            user_name=user["email"],
            user_display_name=user["email"],
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=ResidentKeyRequirement.PREFERRED,
                user_verification=UserVerificationRequirement.PREFERRED,
            ),
            supported_pub_key_algs=[
                COSEAlgorithmIdentifier.ECDSA_SHA_256,
                COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256,
            ],
        )
    except Exception as e:
        logger.error(f"[Passkey] generate_registration_options failed: {e}")
        raise HTTPException(500, f"Passkey-Optionen konnten nicht generiert werden: {e}")

    challenge_b64 = base64.b64encode(options.challenge).decode()
    save_challenge(challenge_b64, "register", current_user["id"])

    logger.info(f"[Passkey] register/begin — user={user['email']} rp_id={rp_id} origin={origin}")
    return json.loads(webauthn.options_to_json(options))


class RegisterCompletePayload(BaseModel):
    credential: dict
    device_name: str = "Passkey"


@router.post("/register/complete")
def register_complete(data: RegisterCompletePayload, request: Request, current_user: dict = Depends(get_current_user)):
    """Verify registration response and save the passkey."""
    rp_id, _, origin = _get_rp(request)

    raw_challenge = data.credential.get("response", {}).get("clientDataJSON", "")
    try:
        client_data = json.loads(base64.b64decode(raw_challenge + "=="))
        challenge_b64 = base64.b64encode(
            base64.urlsafe_b64decode(client_data["challenge"] + "==")
        ).decode()
    except Exception:
        raise HTTPException(400, "Ungültige clientDataJSON.")

    stored = consume_challenge(challenge_b64, "register")
    if not stored or stored["user_id"] != current_user["id"]:
        raise HTTPException(400, "Challenge ungültig oder abgelaufen.")

    try:
        verification = webauthn.verify_registration_response(
            credential=data.credential,
            expected_challenge=base64.b64decode(challenge_b64),
            expected_rp_id=rp_id,
            expected_origin=origin,
        )
    except Exception as e:
        logger.warning(f"[Passkey] Registration verification failed (rp_id={rp_id} origin={origin}): {e}")
        raise HTTPException(400, f"Passkey-Verifizierung fehlgeschlagen: {e}")

    cred_id = base64.b64encode(verification.credential_id).decode()
    pub_key = base64.b64encode(verification.credential_public_key).decode()
    aaguid  = str(verification.aaguid) if verification.aaguid else None

    pk_id = save_credential(
        user_id=current_user["id"],
        credential_id=cred_id,
        public_key=pub_key,
        sign_count=verification.sign_count,
        device_name=data.device_name,
        aaguid=aaguid,
    )

    logger.info(f"[Passkey] Registered for user {current_user['email']}: {data.device_name}")
    return {"id": pk_id, "device_name": data.device_name, "message": "Passkey registriert ✓"}


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login/begin")
def login_begin(request: Request):
    """Start passkey authentication — discoverable credentials."""
    if not AUTH_ENABLED:
        raise HTTPException(400, "AUTH_ENABLED=false.")

    rp_id, _, origin = _get_rp(request)

    options = webauthn.generate_authentication_options(
        rp_id=rp_id,
        user_verification=UserVerificationRequirement.PREFERRED,
        allow_credentials=[],
    )

    challenge_b64 = base64.b64encode(options.challenge).decode()
    save_challenge(challenge_b64, "login")

    return json.loads(webauthn.options_to_json(options))


class LoginCompletePayload(BaseModel):
    credential: dict


@router.post("/login/complete")
def login_complete(data: LoginCompletePayload, request: Request):
    """Verify authentication response and return JWT."""
    if not AUTH_ENABLED:
        raise HTTPException(400, "AUTH_ENABLED=false.")

    rp_id, _, origin = _get_rp(request)

    try:
        raw = data.credential.get("response", {}).get("clientDataJSON", "")
        client_data = json.loads(base64.b64decode(raw + "=="))
        challenge_b64 = base64.b64encode(
            base64.urlsafe_b64decode(client_data["challenge"] + "==")
        ).decode()
    except Exception:
        raise HTTPException(400, "Ungültige clientDataJSON.")

    stored = consume_challenge(challenge_b64, "login")
    if not stored:
        raise HTTPException(400, "Challenge ungültig oder abgelaufen.")

    cred_id = data.credential.get("id", "")
    try:
        cred_id_bytes = base64.urlsafe_b64decode(cred_id + "==")
        cred_id_b64   = base64.b64encode(cred_id_bytes).decode()
    except Exception:
        cred_id_b64 = cred_id

    stored_cred = get_credential(cred_id_b64)
    if not stored_cred:
        raise HTTPException(401, "Passkey nicht gefunden.")

    try:
        pub_key_bytes = base64.b64decode(stored_cred["public_key"])
        verification  = webauthn.verify_authentication_response(
            credential=data.credential,
            expected_challenge=base64.b64decode(challenge_b64),
            expected_rp_id=rp_id,
            expected_origin=origin,
            credential_public_key=pub_key_bytes,
            credential_current_sign_count=stored_cred["sign_count"],
        )
    except Exception as e:
        logger.warning(f"[Passkey] Auth verification failed: {e}")
        raise HTTPException(401, f"Passkey-Authentifizierung fehlgeschlagen: {e}")

    update_sign_count(cred_id_b64, verification.new_sign_count)

    token = create_token(stored_cred["user_id"], stored_cred["email"], stored_cred["role"])
    logger.info(f"[Passkey] Login: {stored_cred['email']}")
    return {
        "token": token,
        "user": {"email": stored_cred["email"], "role": stored_cred["role"]},
    }


# ── Manage Passkeys ───────────────────────────────────────────────────────────

@router.get("")
def get_my_passkeys(current_user: dict = Depends(get_current_user)):
    """List all passkeys for the current user."""
    return list_credentials(current_user["id"])


@router.delete("/{pk_id}")
def delete_my_passkey(pk_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a passkey by its DB id."""
    if not delete_credential(pk_id, current_user["id"]):
        raise HTTPException(404, "Passkey nicht gefunden.")
    return {"message": "Passkey gelöscht ✓"}

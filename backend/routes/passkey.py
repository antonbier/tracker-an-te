"""
WanderSuite — WebAuthn / Passkey Routes

Endpoints:
  POST /api/auth/passkey/register/begin     → generate registration options
  POST /api/auth/passkey/register/complete  → verify + save credential
  POST /api/auth/passkey/login/begin        → generate authentication options
  POST /api/auth/passkey/login/complete     → verify + return JWT
  GET  /api/auth/passkeys                   → list my passkeys
  DELETE /api/auth/passkeys/{id}            → delete a passkey

Requires HTTPS in production (WebAuthn spec).
For local testing: works on localhost only.
"""

import os
import json
import base64
import logging
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

# RP = Relying Party (your app)
RP_ID   = os.getenv("WEBAUTHN_RP_ID", "localhost")
RP_NAME = os.getenv("WEBAUTHN_RP_NAME", "WanderSuite")
# Origin must match exactly what the browser sees
# e.g. https://wandersuite.example.com or http://localhost:8765
ORIGIN  = os.getenv("WEBAUTHN_ORIGIN", f"http://localhost:8765")


# ── Register ──────────────────────────────────────────────────────────────────

class RegisterBeginPayload(BaseModel):
    device_name: str = "Passkey"


@router.post("/register/begin")
def register_begin(data: RegisterBeginPayload, current_user: dict = Depends(get_current_user)):
    """
    Start passkey registration for the currently logged-in user.
    Returns PublicKeyCredentialCreationOptions for the browser.
    """
    user = get_user_by_id(current_user["id"])
    if not user:
        raise HTTPException(404, "User nicht gefunden.")

    user_id_bytes = str(current_user["id"]).encode()

    options = webauthn.generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=user_id_bytes,
        user_name=user["email"],
        user_display_name=user["email"],
        attestation="none",
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
        supported_pub_key_algs=[
            COSEAlgorithmIdentifier.ECDSA_SHA_256,
            COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256,
        ],
    )

    # Store challenge for verification
    challenge_b64 = base64.b64encode(options.challenge).decode()
    save_challenge(challenge_b64, "register", current_user["id"])

    return json.loads(webauthn.options_to_json(options))


class RegisterCompletePayload(BaseModel):
    credential: dict
    device_name: str = "Passkey"


@router.post("/register/complete")
def register_complete(data: RegisterCompletePayload, current_user: dict = Depends(get_current_user)):
    """Verify registration response and save the passkey."""

    # Recover challenge
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
            expected_rp_id=RP_ID,
            expected_origin=ORIGIN,
        )
    except Exception as e:
        logger.warning(f"[Passkey] Registration verification failed: {e}")
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
def login_begin():
    """
    Start passkey authentication (no email needed — discoverable credentials).
    Returns PublicKeyCredentialRequestOptions for the browser.
    """
    if not AUTH_ENABLED:
        raise HTTPException(400, "AUTH_ENABLED=false.")

    options = webauthn.generate_authentication_options(
        rp_id=RP_ID,
        user_verification=UserVerificationRequirement.PREFERRED,
        allow_credentials=[],  # empty = discoverable / resident key
    )

    challenge_b64 = base64.b64encode(options.challenge).decode()
    save_challenge(challenge_b64, "login")

    return json.loads(webauthn.options_to_json(options))


class LoginCompletePayload(BaseModel):
    credential: dict


@router.post("/login/complete")
def login_complete(data: LoginCompletePayload):
    """Verify authentication response and return JWT."""
    if not AUTH_ENABLED:
        raise HTTPException(400, "AUTH_ENABLED=false.")

    # Extract challenge from clientDataJSON
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

    # Look up credential
    cred_id = data.credential.get("id", "")
    # WebAuthn IDs are base64url — normalize to base64
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
            expected_rp_id=RP_ID,
            expected_origin=ORIGIN,
            credential_public_key=pub_key_bytes,
            credential_current_sign_count=stored_cred["sign_count"],
        )
    except Exception as e:
        logger.warning(f"[Passkey] Auth verification failed: {e}")
        raise HTTPException(401, f"Passkey-Authentifizierung fehlgeschlagen: {e}")

    # Update sign count (replay attack protection)
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

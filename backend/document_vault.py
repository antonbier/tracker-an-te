"""
WanderSuite — document_vault.py
Verschlüsselte Dateiablage für den Dokumenten-Vault (Pass, Visum, Impfnachweis, ...).

Dateien liegen Fernet-verschlüsselt unter /app/data/vault/{user_id}/{stored_filename}
(stored_filename ist ein zufälliger Token, nie der Original-Dateiname — verhindert
Path-Traversal und Namenskollisionen). Nutzt dieselbe Fernet-Instanz wie
settings_manager.py (APP_SECRET), damit kein zweites Secret verwaltet werden muss.
"""

import os
import secrets

from settings_manager import _get_fernet

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB — reicht für gescannte Dokumente/Fotos

_DB_PATH = os.environ.get("DB_PATH", "/app/data/tracker.db")
VAULT_DIR = os.path.join(os.path.dirname(_DB_PATH) or ".", "vault")


def _user_dir(user_id: int) -> str:
    d = os.path.join(VAULT_DIR, str(user_id))
    os.makedirs(d, exist_ok=True)
    return d


def save_encrypted_file(user_id: int, content: bytes) -> str:
    """Encrypts and writes file content, returns the stored filename (opaque token)."""
    fernet = _get_fernet()
    stored_filename = secrets.token_hex(16)
    encrypted = fernet.encrypt(content)
    path = os.path.join(_user_dir(user_id), stored_filename)
    with open(path, "wb") as f:
        f.write(encrypted)
    return stored_filename


def read_encrypted_file(user_id: int, stored_filename: str) -> bytes | None:
    """Reads and decrypts a file. Returns None if missing or undecryptable."""
    path = os.path.join(_user_dir(user_id), stored_filename)
    if not os.path.isfile(path):
        return None
    fernet = _get_fernet()
    with open(path, "rb") as f:
        encrypted = f.read()
    try:
        return fernet.decrypt(encrypted)
    except Exception:
        return None


def delete_file(user_id: int, stored_filename: str) -> None:
    path = os.path.join(_user_dir(user_id), stored_filename)
    try:
        os.remove(path)
    except FileNotFoundError:
        pass

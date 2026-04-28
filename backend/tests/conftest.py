"""
WanderSuite — pytest conftest.py

Shared fixtures für alle Tests.
Nutzt FastAPI TestClient mit AUTH_ENABLED=false (Guest-Modus)
und einer In-Memory SQLite Datenbank — kein Zustand zwischen Tests.
"""

import os
import pytest

# Test-Umgebung vor jedem Import setzen
os.environ.setdefault("AUTH_ENABLED", "false")
os.environ.setdefault("JWT_SECRET", "wandersuite-test-secret-not-for-production")
os.environ.setdefault("DB_PATH", ":memory:")  # In-Memory DB — kein Disk-Zustand

from fastapi.testclient import TestClient
from main import app
from core.db_init import init_db


@pytest.fixture(scope="session", autouse=True)
def init_database():
    """Initialisiert die In-Memory DB einmal pro Test-Session."""
    init_db()


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient — AUTH_ENABLED=false, kein echter Server nötig."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

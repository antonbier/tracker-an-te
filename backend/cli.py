#!/usr/bin/env python3
"""
WanderSuite — CLI Notfall-Tool
Verwendung (im Backend-Verzeichnis oder Docker-Container):

    python3 cli.py reset-password <email> <new_password>
    python3 cli.py list-users
    python3 cli.py create-admin <email> <password>

Nützlich wenn man aus dem Admin-Account ausgesperrt ist.
Benötigt direkten Zugriff auf die SQLite-Datenbank (DB_PATH Env-Variable).
"""

import sys
import os

# Ensure backend modules are importable
sys.path.insert(0, os.path.dirname(__file__))

from core.db_init import init_db
from auth_db import init_auth_tables, update_password, get_user_by_email, \
                    create_user, list_users, count_users


def cmd_reset_password(email: str, new_password: str):
    if len(new_password) < 8:
        print("❌ Passwort muss mindestens 8 Zeichen haben.")
        sys.exit(1)
    user = get_user_by_email(email)
    if not user:
        print(f"❌ Kein User mit E-Mail '{email}' gefunden.")
        sys.exit(1)
    update_password(user["id"], new_password)
    print(f"✅ Passwort für {email} (ID={user['id']}, role={user['role']}) geändert.")


def cmd_list_users():
    users = list_users()
    if not users:
        print("Keine User in der Datenbank.")
        return
    print(f"{'ID':<5} {'E-Mail':<35} {'Rolle':<8} {'Erstellt'}")
    print("─" * 70)
    for u in users:
        print(f"{u['id']:<5} {u['email']:<35} {u['role']:<8} {u.get('created_at','?')}")


def cmd_create_admin(email: str, password: str):
    if len(password) < 8:
        print("❌ Passwort muss mindestens 8 Zeichen haben.")
        sys.exit(1)
    try:
        user = create_user(email, password, role="admin")
        print(f"✅ Admin erstellt: {user['email']} (ID={user['id']})")
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)


def main():
    # Initialize DB tables before any operation
    init_db()
    init_auth_tables()

    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    cmd = args[0]

    if cmd == "reset-password":
        if len(args) != 3:
            print("Verwendung: python3 cli.py reset-password <email> <new_password>")
            sys.exit(1)
        cmd_reset_password(args[1], args[2])

    elif cmd == "list-users":
        cmd_list_users()

    elif cmd == "create-admin":
        if len(args) != 3:
            print("Verwendung: python3 cli.py create-admin <email> <password>")
            sys.exit(1)
        cmd_create_admin(args[1], args[2])

    else:
        print(f"❌ Unbekannter Befehl: {cmd}")
        print("Verfügbare Befehle: reset-password, list-users, create-admin")
        sys.exit(1)


if __name__ == "__main__":
    main()

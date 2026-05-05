#!/bin/sh
# WanderSuite Backend Entrypoint
#
# Problem: Das /app/data Volume wird vom Host gemountet und gehört oft root.
# Der non-root User 'wandersuite' (UID 1000) kann dann nicht in die DB schreiben.
#
# Lösung: Root setzt die Permissions, dann wird zu 'wandersuite' gewechselt.
# Dieses Script läuft initial als root (via Docker USER-Wechsel mit gosu).

set -e

DATA_DIR="${DB_PATH%/*}"
DATA_DIR="${DATA_DIR:-/app/data}"

# Permissions nur setzen wenn nötig (Performance)
if [ -d "$DATA_DIR" ]; then
    chown -R wandersuite:wandersuite "$DATA_DIR" 2>/dev/null || true
    chmod -R 755 "$DATA_DIR" 2>/dev/null || true
fi

# Als wandersuite User weiterlaufen
exec gosu wandersuite uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info

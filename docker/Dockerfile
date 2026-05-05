FROM python:3.12-slim

# System dependencies:
#   curl  — healthcheck
#   gosu  — sauberer User-Wechsel im Entrypoint (root → wandersuite)
#           ohne gosu müsste der Container komplett als root laufen
RUN apt-get update && apt-get install -y --no-install-recommends curl gosu     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer cache)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Persistent data directory — wird vom Host via Volume gemountet
RUN mkdir -p /app/data

# Entrypoint-Script: läuft als root, setzt Permissions auf /app/data,
# wechselt dann via gosu zu 'wandersuite' → kein readonly-DB-Problem
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ── Security: non-root user ───────────────────────────────────────────────────
# wandersuite (UID 1000) ist der Laufzeit-User nach dem Entrypoint-Wechsel.
# Der Container startet als root (für chown), wechselt dann zu wandersuite.
RUN groupadd -r wandersuite && useradd -r -g wandersuite -u 1000 wandersuite     && chown -R wandersuite:wandersuite /app

EXPOSE 8000

# Entrypoint: setzt Permissions, wechselt zu wandersuite, startet uvicorn
ENTRYPOINT ["/entrypoint.sh"]
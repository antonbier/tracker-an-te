FROM python:3.12-slim

# System dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer cache)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Persistent data directory — mounted from host via docker-compose volume
# DB_PATH defaults to /app/data/tracker.db (set via environment variable)
RUN mkdir -p /app/data

# ── Security: non-root user ───────────────────────────────────────────────────
# Run as unprivileged user — reduces attack surface if container is compromised.
# UID/GID 1000 is conventional for app users; data volume must be writable.
RUN groupadd -r wandersuite && useradd -r -g wandersuite -u 1000 wandersuite \
    && chown -R wandersuite:wandersuite /app

USER wandersuite

EXPOSE 8000

# uvicorn runs on all interfaces, port 8000 (mapped to BACKEND_PORT on host)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]

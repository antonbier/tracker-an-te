"""
WanderSuite — Shared Immich Client

Konsolidiert Search+Thumbnail-Zugriffe, die zuvor dupliziert in discovery.py
und routes/ws_trips.py existierten. `POST /api/search/metadata` bleibt der
korrekte Immich-Endpoint (auch unter v3 unverändert — siehe Code-Review).
"""

import httpx

DEFAULT_TIMEOUT = 15.0


async def search_metadata(base_url: str, api_key: str, *, query: str | None = None,
                           size: int = 1, taken_after: str | None = None,
                           taken_before: str | None = None, with_exif: bool = False,
                           timeout: float = DEFAULT_TIMEOUT,
                           client: httpx.AsyncClient | None = None) -> list[dict]:
    """POST /api/search/metadata — gibt die assets.items-Liste zurück.
    Wirft RuntimeError bei Nicht-200-Antwort."""
    body: dict = {"size": size, "type": "IMAGE", "withExif": with_exif}
    if query:
        body["query"] = query
    if taken_after:
        body["takenAfter"] = taken_after
    if taken_before:
        body["takenBefore"] = taken_before

    async def _do(c: httpx.AsyncClient) -> list[dict]:
        resp = await c.post(
            f"{base_url}/api/search/metadata",
            headers={"x-api-key": api_key, "Content-Type": "application/json"},
            json=body,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Immich antwortet mit {resp.status_code}")
        return resp.json().get("assets", {}).get("items", [])

    if client is not None:
        return await _do(client)
    async with httpx.AsyncClient(timeout=timeout, trust_env=False, follow_redirects=True) as c:
        return await _do(c)


async def fetch_thumbnail(base_url: str, api_key: str, asset_id: str, *,
                           size: str = "preview", timeout: float = DEFAULT_TIMEOUT,
                           client: httpx.AsyncClient | None = None) -> httpx.Response:
    """GET .../assets/{id}/thumbnail — gibt die rohe Response zurück
    (Aufrufer prüft status_code selbst, je nach gewünschtem Fehlerverhalten)."""
    async def _do(c: httpx.AsyncClient) -> httpx.Response:
        return await c.get(
            f"{base_url}/api/assets/{asset_id}/thumbnail?size={size}",
            headers={"x-api-key": api_key},
        )

    if client is not None:
        return await _do(client)
    async with httpx.AsyncClient(timeout=timeout, trust_env=False, follow_redirects=True) as c:
        return await _do(c)

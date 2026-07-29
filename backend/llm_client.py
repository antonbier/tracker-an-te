"""
WanderSuite — Shared LLM Client (OpenAI + Gemini)

Konsolidiert die Call+Parse-Logik, die zuvor dupliziert in discovery.py
und routes/ws_trips.py existierte (inkl. der dort separat gepflegten,
inzwischen veralteten gemini-2.0-flash Modell-ID).
"""

import json
import logging

import httpx

logger = logging.getLogger(__name__)

OPENAI_MODEL = "gpt-4o-mini"
GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_TIMEOUT = 25.0


def parse_json_array(text: str) -> list:
    """Robustes Parsen von LLM-Antworten: plain JSON-Array, in Markdown-Codefences
    verpackt, oder in ein Objekt eingebettet (dann wird die erste Liste-von-Dicts
    darin zurückgegeben)."""
    try:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            if "```" in cleaned:
                cleaned = cleaned.rsplit("```", 1)[0]
        if cleaned.startswith("json\n"):
            cleaned = cleaned[5:]
        result = json.loads(cleaned)
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            for v in result.values():
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    return v
            return [result]
    except Exception as e:
        logger.warning(f"[LLM] JSON parse failed: {e} | text={text[:200]}")
    return []


async def call_openai(user_prompt: str, api_key: str, *, system_prompt: str | None = None,
                       max_tokens: int = 800, temperature: float = 0.7,
                       timeout: float = DEFAULT_TIMEOUT) -> list:
    if not api_key:
        logger.warning("[LLM] OpenAI key not configured")
        return []
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})
    try:
        async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": OPENAI_MODEL,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            if resp.status_code == 429:
                logger.warning("[LLM] OpenAI rate limit (429)")
                raise RuntimeError("api_rate_limit:openai")
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"]
            return parse_json_array(text)
    except RuntimeError:
        raise
    except httpx.HTTPStatusError as e:
        logger.warning(f"[LLM] OpenAI HTTP {e.response.status_code}: {e.response.text}")
        return []
    except Exception as e:
        logger.warning(f"[LLM] OpenAI call failed: {e}")
        return []


async def call_gemini(user_prompt: str, api_key: str, *, system_prompt: str | None = None,
                       max_tokens: int = 800, temperature: float = 0.7,
                       timeout: float = DEFAULT_TIMEOUT) -> list:
    if not api_key:
        logger.warning("[LLM] Gemini key not configured")
        return []
    text_prompt = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
    try:
        async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}",
                json={
                    "contents": [{"parts": [{"text": text_prompt}]}],
                    "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature},
                },
            )
            resp.raise_for_status()
            text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            return parse_json_array(text)
    except Exception as e:
        logger.warning(f"[LLM] Gemini call failed: {e}")
        return []


async def suggest(user_prompt: str, *, system_prompt: str | None, openai_key: str,
                   gemini_key: str, prefer: str = "openai", **kwargs) -> list:
    """Ruft den bevorzugten Provider auf, fällt bei leerem Ergebnis auf den anderen zurück."""
    if prefer == "gemini":
        result = await call_gemini(user_prompt, gemini_key, system_prompt=system_prompt, **kwargs)
        if not result:
            result = await call_openai(user_prompt, openai_key, system_prompt=system_prompt, **kwargs)
    else:
        result = await call_openai(user_prompt, openai_key, system_prompt=system_prompt, **kwargs)
        if not result:
            result = await call_gemini(user_prompt, gemini_key, system_prompt=system_prompt, **kwargs)
    return result

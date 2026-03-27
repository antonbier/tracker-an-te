"""
WanderSuite v0.5 — REST Routes: /api/discover
AI-Reiseempfehlungen via Google Gemini.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import logging

from gemini import generate_travel_recommendations

router = APIRouter()
logger = logging.getLogger(__name__)


class DiscoverRequest(BaseModel):
    query:          str
    api_key:        str
    lang:           str = "de"
    exclude_places: Optional[list[str]] = None


@router.post("")
def get_recommendations(data: DiscoverRequest):
    if not data.query.strip():
        return {"error": "Bitte beschreibe was du suchst"}
    if not data.api_key:
        return {"error": "Gemini API Key fehlt"}

    result = generate_travel_recommendations(
        query=data.query,
        api_key=data.api_key,
        exclude_places=data.exclude_places or [],
        lang=data.lang,
    )
    return result

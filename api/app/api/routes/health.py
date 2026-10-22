"""Santé de l'API et de l'API Mock. Utilisées par le staging et le workflow de release."""
from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, HTTPException

from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])

MOCK_API_URL = (settings.MOCK_API_URL or "http://10.43.43.80:8000").rstrip("/")
MOCK_API_CREDENTIALS = (settings.MOCK_API_USERNAME, settings.MOCK_API_PASSWORD)
# Authentification basique requise sur l'URL publique, absente sur le réseau de l'école
MOCK_API_AUTH = MOCK_API_CREDENTIALS if all(MOCK_API_CREDENTIALS) else None


@router.get("")
async def health():
    return {
        "status": "healthy",
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(UTC).isoformat(),
        "version": {"commit": settings.GIT_TITLE, "sha": settings.GIT_SHA},
    }


@router.get("/mock")
async def health_mock():
    try:
        async with httpx.AsyncClient(timeout=5.0, auth=MOCK_API_AUTH) as client:
            response = await client.get(f"{MOCK_API_URL}/health")
            response.raise_for_status()
            return response.json()

    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="API Mock inaccessible")

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502, detail=f"Erreur API Mock : {exc.response.status_code}"
        )

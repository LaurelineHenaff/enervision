
import os

import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI()

MOCK_API_URL = (os.getenv("API_MOCK_URL") or "http://10.43.43.80:8000").rstrip("/")
MOCK_API_CREDENTIALS = (os.getenv("API_MOCK_USER"), os.getenv("API_MOCK_PASSWORD"))
# Authentification basique requise sur l'URL publique, absente sur le réseau de l'école
MOCK_API_AUTH = MOCK_API_CREDENTIALS if all(MOCK_API_CREDENTIALS) else None


@app.get("/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=5.0, auth=MOCK_API_AUTH) as client:
            response = await client.get(f"{MOCK_API_URL}/health")
            response.raise_for_status()
            return response.json()

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="API Mock inaccessible"
        )

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Erreur API Mock : {exc.response.status_code}"
        )

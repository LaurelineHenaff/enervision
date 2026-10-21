
import os
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException

# Environnement (dev, staging, production) : défini au lancement du conteneur, pas dans l'image,
# car la même image est promue du staging vers la production
ENVIRONMENT = os.getenv("APP_ENV", "dev")

# Version déployée : renseignée à la construction de l'image par la CI (publish-images.yml)
GIT_TITLE = os.getenv("GIT_TITLE", "dev")
GIT_SHA = os.getenv("GIT_SHA", "dev")

app = FastAPI(title="enervision-api", description=f"Environnement : {ENVIRONMENT}")

MOCK_API_URL = (os.getenv("MOCK_API_URL") or "http://10.43.43.80:8000").rstrip("/")
MOCK_API_CREDENTIALS = (os.getenv("MOCK_API_USERNAME"), os.getenv("MOCK_API_PASSWORD"))
# Authentification basique requise sur l'URL publique, absente sur le réseau de l'école
MOCK_API_AUTH = MOCK_API_CREDENTIALS if all(MOCK_API_CREDENTIALS) else None


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": {"commit": GIT_TITLE, "sha": GIT_SHA},
    }


@app.get("/health/mock")
async def health_mock():
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

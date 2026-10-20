
import os

import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI()

MOCK_API_URL = os.getenv("API_MOCK_URL") or "http://10.43.43.80:8000"


@app.get("/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
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

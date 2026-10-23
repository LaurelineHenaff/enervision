from datetime import UTC, datetime

from fastapi import FastAPI

# L'ETL n'expose pas d'API métier : pas de documentation, seulement la sonde de santé
app = FastAPI(title="enervision-etl", docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(UTC).isoformat()}

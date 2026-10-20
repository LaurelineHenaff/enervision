"""Point d'entrée de l'API EnerVision.

Assemble les routes, verrouille le CORS sur le front Angular, et crée les
tables au démarrage (pratique en dev ; en prod on passera par Alembic).
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.api.routes import auth, history, predictions, recommendations

# Important : importer les modèles pour qu'ils soient enregistrés sur Base
from app.models import user  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev uniquement : crée les tables si absentes. En prod → migrations Alembic.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="EnerVision API", version="0.1.0", lifespan=lifespan)

# CORS verrouillé sur l'origine du front — pas de "*" en présence de cookies/JWT
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(predictions.router)
app.include_router(history.router)
app.include_router(recommendations.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}

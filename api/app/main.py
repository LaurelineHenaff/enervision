"""Point d'entrée de l'API EnerVision.

Assemble les routes et verrouille le CORS sur le front Angular. Le schéma de la base n'est
pas créé ici : il vient des migrations de db/migrations (dbmate), appliquées avant le
démarrage de l'API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, health, history, predictions, recommendations
from app.core.config import settings

app = FastAPI(
    title="enervision-api",
    description=f"Environnement : {settings.APP_ENV}",
)

# CORS verrouillé sur l'origine du front — pas de "*" en présence de cookies/JWT
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(predictions.router)
app.include_router(history.router)
app.include_router(recommendations.router)

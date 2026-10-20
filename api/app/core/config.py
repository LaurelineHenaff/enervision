"""Configuration centralisée, lue depuis les variables d'environnement (.env).

Toutes les valeurs sensibles (DB, clé JWT) viennent d'ici — jamais en dur
dans le code. pydantic-settings valide et type automatiquement.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # Base de données
    DATABASE_URL: str

    # Sécurité JWT
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # CORS
    FRONTEND_ORIGIN: str = "http://localhost:4200"


@lru_cache
def get_settings() -> Settings:
    """Mise en cache : les settings ne sont lus qu'une fois au démarrage."""
    return Settings()


settings = get_settings()

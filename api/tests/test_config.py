"""Lecture et validation des variables d'environnement."""
import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_url_postgresql_convertie_en_asyncpg():
    s = Settings(_env_file=None, DATABASE_URL="postgresql://u:p@db:5432/x", SECRET_KEY="k")
    assert s.DATABASE_URL == "postgresql+asyncpg://u:p@db:5432/x"


def test_url_deja_asyncpg_inchangee():
    url = "postgresql+asyncpg://u:p@db:5432/x"
    s = Settings(_env_file=None, DATABASE_URL=url, SECRET_KEY="k")
    assert s.DATABASE_URL == url


def test_valeurs_par_defaut():
    s = Settings(_env_file=None, DATABASE_URL="postgresql://u:p@db/x", SECRET_KEY="k")
    assert s.APP_ENV == "dev"
    assert s.ALGORITHM == "HS256"
    assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 60


@pytest.mark.parametrize("variable", ["DATABASE_URL", "SECRET_KEY"])
def test_variable_obligatoire_manquante(monkeypatch, variable):
    monkeypatch.delenv(variable, raising=False)
    valeurs = {"DATABASE_URL": "postgresql://u:p@db/x", "SECRET_KEY": "k"}
    del valeurs[variable]
    with pytest.raises(ValidationError, match=variable):
        Settings(_env_file=None, **valeurs)

"""Fixtures communes aux tests unitaires de l'ETL.

Les tests ne demandent ni base de données ni réseau :
- les identifiants de l'API Mock reçoivent des valeurs de test avant tout import de api_mock ;
- l'API Mock est remplacée par un httpx2.MockTransport qui répond avec une fonction de test.
"""
import os

# À faire avant d'importer api_mock.* : la config est lue à l'import de api_mock.config
os.environ.setdefault("MOCK_API_URL", "http://mock.test")
os.environ.setdefault("MOCK_API_USERNAME", "utilisateur-test")
os.environ.setdefault("MOCK_API_PASSWORD", "motdepasse-test")

import httpx2
import pytest
from fastapi.testclient import TestClient

from api_mock.services import site_service
from main import app

SITE_EXEMPLE = {
    "site_id": "SITE001",
    "site_type": "office",
    "site_name": "Bureau Paris",
    "location": "Paris",
    "capacity_kw": 250.0,
    "status": "active",
}


@pytest.fixture
def anyio_backend():
    # Les fonctions async sont testées avec le plugin pytest d'anyio (déjà installé avec FastAPI)
    return "asyncio"


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_api(monkeypatch):
    """Fait répondre l'API Mock par une fonction de test au lieu du réseau.

    Renvoie la liste des requêtes reçues, pour vérifier l'URL et l'authentification.
    """
    requetes: list[httpx2.Request] = []

    def _mock_api(handler):
        vrai_client = httpx2.AsyncClient

        def enregistrer(request):
            requetes.append(request)
            return handler(request)

        def faux_client(**kwargs):
            return vrai_client(transport=httpx2.MockTransport(enregistrer), **kwargs)

        monkeypatch.setattr(site_service.httpx2, "AsyncClient", faux_client)
        return requetes

    return _mock_api

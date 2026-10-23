"""Fixtures communes aux tests unitaires de l'ETL.

Les tests ne demandent ni base de données ni réseau :
- les identifiants de l'API Mock reçoivent des valeurs de test avant tout import de mock_client ;
- l'API Mock est remplacée par un httpx2.MockTransport qui répond avec une fonction de test.
"""
import os

# À faire avant d'importer mock_client.* : la config est lue à l'import de mock_client.config
os.environ.setdefault("MOCK_API_URL", "http://mock.test")
os.environ.setdefault("MOCK_API_USERNAME", "utilisateur-test")
os.environ.setdefault("MOCK_API_PASSWORD", "motdepasse-test")

import httpx2
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from main import app

SITE_EXAMPLE = {
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
    received_requests: list[httpx2.Request] = []

    def _mock_api(handler):
        real_client = httpx2.AsyncClient

        def record(request):
            received_requests.append(request)
            return handler(request)

        def fake_client(**kwargs):
            return real_client(transport=httpx2.MockTransport(record), **kwargs)

        monkeypatch.setattr(httpx2, "AsyncClient", fake_client)
        return received_requests

    return _mock_api


NAN = np.nan


def make_readings(kwh, euros=None, site="SITE001", start="2023-01-01 00:00:00"):
    n = len(kwh)
    return pd.DataFrame(
        {
            "timestamp": pd.date_range(start, periods=n, freq="h").strftime("%Y-%m-%d %H:%M:%S"),
            "site_id": site,
            "consumption_kwh": kwh,
            "consumption_euros": euros if euros is not None else [NAN] * n,
            "temperature_celsius": [10.0] * n,
        }
    )


def make_metadata(anomalies=(), total=3, start="2023-01-01T00:00:00", end="2023-01-01T02:00:00"):
    return {
        "frequency": "1h",
        "sites": {
            "SITE001": {
                "total_records": total,
                "start_date": start,
                "end_date": end,
                "anomalies": list(anomalies),
            }
        },
    }


def make_anomaly(timestamp, type_, description, severity="critical"):
    return {"timestamp": timestamp, "type": type_, "severity": severity, "description": description}

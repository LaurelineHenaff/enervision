"""L'ETL n'expose que /health : ni Swagger, ni route métier."""
import pytest


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.parametrize("chemin", ["/docs", "/redoc", "/openapi.json", "/sites", "/readings"])
def test_aucune_autre_route(client, chemin):
    assert client.get(chemin).status_code == 404

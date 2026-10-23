"""L'ETL n'expose que /health : ni Swagger, ni route métier."""
import pytest


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json", "/sites", "/readings"])
def test_no_other_route(client, path):
    assert client.get(path).status_code == 404

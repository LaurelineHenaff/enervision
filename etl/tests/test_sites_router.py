"""Route GET /sites : réponse et traduction des erreurs de l'API Mock (simulée)."""
import httpx2

from tests.conftest import SITE_EXEMPLE


def test_liste_des_sites(client, mock_api):
    mock_api(lambda request: httpx2.Response(200, json=[SITE_EXEMPLE]))
    response = client.get("/sites")
    assert response.status_code == 200
    assert response.json() == [SITE_EXEMPLE]


def test_api_mock_en_erreur(client, mock_api):
    mock_api(lambda request: httpx2.Response(500))
    response = client.get("/sites")
    assert response.status_code == 502
    assert response.json()["detail"] == "API Mock a répondu 500"


def test_api_mock_injoignable(client, mock_api):
    def handler(request):
        raise httpx2.ConnectError("connexion refusée", request=request)

    mock_api(handler)
    response = client.get("/sites")
    assert response.status_code == 503
    assert response.json()["detail"] == "API Mock injoignable"


def test_api_mock_trop_lente(client, mock_api):
    def handler(request):
        raise httpx2.ReadTimeout("délai dépassé", request=request)

    mock_api(handler)
    response = client.get("/sites")
    assert response.status_code == 503

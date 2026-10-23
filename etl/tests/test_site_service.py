"""Service get_all_sites : appel de l'API Mock (simulée) et transformation en Site."""
import base64

import httpx2
import pytest
from pydantic import ValidationError

from api_mock.schemas.site import Site
from api_mock.services import site_service
from tests.conftest import SITE_EXEMPLE

pytestmark = pytest.mark.anyio


async def test_renvoie_les_sites(mock_api):
    autre = {**SITE_EXEMPLE, "site_id": "SITE002", "site_type": "factory"}
    mock_api(lambda request: httpx2.Response(200, json=[SITE_EXEMPLE, autre]))

    sites = await site_service.get_all_sites()

    assert sites == [Site(**SITE_EXEMPLE), Site(**autre)]


async def test_liste_vide(mock_api):
    mock_api(lambda request: httpx2.Response(200, json=[]))
    assert await site_service.get_all_sites() == []


async def test_appelle_la_bonne_url_avec_authentification(mock_api, monkeypatch):
    monkeypatch.setattr(site_service, "MOCK_API_URL", "http://mock.test")
    monkeypatch.setattr(site_service, "MOCK_API_USERNAME", "alice")
    monkeypatch.setattr(site_service, "MOCK_API_PASSWORD", "secret")
    requetes = mock_api(lambda request: httpx2.Response(200, json=[]))

    await site_service.get_all_sites()

    assert len(requetes) == 1
    requete = requetes[0]
    assert requete.method == "GET"
    assert str(requete.url) == "http://mock.test/api/v1/sites"
    attendu = "Basic " + base64.b64encode(b"alice:secret").decode()
    assert requete.headers["Authorization"] == attendu


@pytest.mark.parametrize("champ", ["MOCK_API_USERNAME", "MOCK_API_PASSWORD"])
async def test_identifiants_manquants(mock_api, monkeypatch, champ):
    monkeypatch.setattr(site_service, champ, None)
    requetes = mock_api(lambda request: httpx2.Response(200, json=[]))

    with pytest.raises(RuntimeError, match="Identifiants"):
        await site_service.get_all_sites()
    assert requetes == []  # aucun appel réseau tenté


async def test_erreur_http_remontee(mock_api):
    mock_api(lambda request: httpx2.Response(401))
    with pytest.raises(httpx2.HTTPStatusError):
        await site_service.get_all_sites()


async def test_api_injoignable(mock_api):
    def handler(request):
        raise httpx2.ConnectError("connexion refusée", request=request)

    mock_api(handler)
    with pytest.raises(httpx2.RequestError):
        await site_service.get_all_sites()


async def test_donnees_invalides_refusees(mock_api):
    incomplet = {k: v for k, v in SITE_EXEMPLE.items() if k != "site_name"}
    mock_api(lambda request: httpx2.Response(200, json=[incomplet]))
    with pytest.raises(ValidationError):
        await site_service.get_all_sites()

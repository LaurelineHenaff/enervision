"""Services du client de l'API Mock : URL, authentification, paramètres et validation (mock simulé)."""
import base64
from datetime import UTC, datetime, timedelta, timezone

import httpx2
import pytest
from pydantic import ValidationError

from api_mock import config
from api_mock.schemas.site import Site
from api_mock.services import (
    alert_service,
    reading_service,
    sensor_service,
    simulation_service,
    site_service,
    statistic_service,
)
from tests.conftest import SITE_EXEMPLE

pytestmark = pytest.mark.anyio

READING = {
    "timestamp": "2026-10-23T12:50:25.646645",
    "site_id": "SITE001",
    "site_type": "office",
    "consumption_kw": 183.61,
    "consumption_kwh": 183.61,
    "voltage_v": 395.4,
    "current_a": 282.23,
    "power_factor": 0.898,
    "temperature_celsius": 10.1,
    "humidity_percent": None,
    "null_reasons": ["humidity_sensor_failure"],
    "data_quality": "partial",
}


async def test_sites_url_et_authentification(mock_api):
    requetes = mock_api(lambda request: httpx2.Response(200, json=[SITE_EXEMPLE]))

    assert await site_service.get_all_sites() == [Site(**SITE_EXEMPLE)]

    assert str(requetes[0].url) == "http://mock.test/api/v1/sites"
    attendu = base64.b64encode(b"utilisateur-test:motdepasse-test").decode()
    assert requetes[0].headers["authorization"] == f"Basic {attendu}"


async def test_sans_identifiants_aucune_authentification(mock_api, monkeypatch):
    monkeypatch.setattr(config, "MOCK_API_USERNAME", None)
    monkeypatch.setattr(config, "MOCK_API_PASSWORD", None)
    requetes = mock_api(lambda request: httpx2.Response(200, json=[]))

    assert await site_service.get_all_sites() == []
    assert "authorization" not in requetes[0].headers


async def test_detail_d_un_site(mock_api):
    requetes = mock_api(lambda request: httpx2.Response(200, json=SITE_EXEMPLE))
    assert (await site_service.get_site("SITE001")).site_name == "Bureau Paris"
    assert requetes[0].url.path == "/api/v1/sites/SITE001"


async def test_site_inconnu_propage_le_404(mock_api):
    mock_api(lambda request: httpx2.Response(404))
    with pytest.raises(httpx2.HTTPStatusError) as erreur:
        await site_service.get_site("SITE999")
    assert erreur.value.response.status_code == 404


async def test_erreur_serveur_propagee(mock_api):
    mock_api(lambda request: httpx2.Response(500))
    with pytest.raises(httpx2.HTTPStatusError):
        await site_service.get_all_sites()


@pytest.mark.parametrize(
    "erreur", [httpx2.ConnectError("connexion refusée"), httpx2.ReadTimeout("délai dépassé")]
)
async def test_reseau_injoignable_ou_trop_lent_propage(mock_api, erreur):
    def handler(request):
        erreur.request = request
        raise erreur

    mock_api(handler)
    with pytest.raises(httpx2.RequestError):
        await site_service.get_all_sites()


async def test_donnees_invalides_refusees(mock_api):
    mock_api(lambda request: httpx2.Response(200, json=[{**SITE_EXEMPLE, "capacity_kw": "beaucoup"}]))
    with pytest.raises(ValidationError):
        await site_service.get_all_sites()


async def test_reponse_inattendue_refusee(mock_api):
    mock_api(lambda request: httpx2.Response(200, json={"detail": "autre format"}))
    with pytest.raises(ValidationError):
        await site_service.get_all_sites()


async def test_mesure_instantanee_garde_les_null(mock_api):
    requetes = mock_api(lambda request: httpx2.Response(200, json=READING))
    lecture = await reading_service.get_current_reading("SITE001")
    assert requetes[0].url.path == "/api/v1/sites/SITE001/current"
    assert lecture.humidity_percent is None
    assert lecture.null_reasons == ["humidity_sensor_failure"]


async def test_historique_parametres_en_utc(mock_api):
    requetes = mock_api(lambda request: httpx2.Response(200, json=[READING]))
    paris = timezone(timedelta(hours=2))

    lectures = await reading_service.get_readings(
        site_id="SITE001",
        start_time=datetime(2024, 3, 13, 10, 0, tzinfo=paris),
        end_time=datetime(2024, 3, 13, 12, 0, tzinfo=UTC),
        limit=500,
    )

    assert len(lectures) == 1
    params = requetes[0].url.params
    assert params["site_id"] == "SITE001"
    assert params["limit"] == "500"
    assert params["start_time"] == "2024-03-13T08:00:00+00:00"
    assert params["end_time"] == "2024-03-13T12:00:00+00:00"


async def test_historique_refuse_un_horodatage_sans_fuseau():
    with pytest.raises(ValueError, match="fuseau"):
        await reading_service.get_readings(start_time=datetime(2024, 3, 13, 10, 0))


@pytest.mark.parametrize("limite", [0, 1001])
async def test_historique_refuse_une_limite_hors_bornes(limite):
    with pytest.raises(ValueError, match="limit"):
        await reading_service.get_readings(limit=limite)


async def test_alertes_filtres_et_liste_vide(mock_api):
    requetes = mock_api(lambda request: httpx2.Response(200, json=[]))
    assert await alert_service.get_alerts(site_id="SITE003", severity="high") == []
    assert requetes[0].url.params["site_id"] == "SITE003"
    assert requetes[0].url.params["severity"] == "high"


async def test_alerte_sans_valeur(mock_api):
    alerte = {
        "alert_id": "A1", "timestamp": "2026-10-22T10:00:00", "site_id": "SITE003",
        "severity": "high", "type": "spike", "message": "pic", "value": None, "threshold": 630.0,
    }  # fmt: skip
    mock_api(lambda request: httpx2.Response(200, json=[alerte]))
    assert (await alert_service.get_alerts())[0].value is None


async def test_capteurs_indexes_par_site(mock_api):
    reponse = {
        "SITE001": {
            "site_name": "Bureau",
            "overall": "degraded",
            "sensors": {
                "consumption": {"status": "ok", "failing_until": None},
                "humidity": {"status": "failing", "failing_until": "2026-10-23T12:51:10"},
            },
        }
    }
    mock_api(lambda request: httpx2.Response(200, json=reponse))
    sites = await sensor_service.get_sensors_status()
    assert sites[0].site_id == "SITE001"
    assert sites[0].overall == "degraded"
    assert sites[0].sensors["humidity"].failing_until is not None


async def test_synthese_du_parc(mock_api):
    reponse = {
        "timestamp": "2026-10-23T12:50:25",
        "total_sites": 2,
        "total_consumption_kw": 173.62,
        "total_capacity_kw": 1200,
        "average_load_percent": 86.8,
        "sites": [
            {"site_id": "SITE001", "site_name": "Bureau", "current_consumption_kw": 173.62,
             "capacity_kw": 200, "load_percent": 86.8, "data_quality": "good"},
            {"site_id": "SITE002", "site_name": "Usine", "current_consumption_kw": None,
             "capacity_kw": 1000, "load_percent": None, "data_quality": "degraded"},
        ],
    }  # fmt: skip
    mock_api(lambda request: httpx2.Response(200, json=reponse))
    synthese = await statistic_service.get_stats_summary()
    assert synthese.total_sites == 2
    assert synthese.sites[1].current_consumption_kw is None


async def test_synthese_inattendue_refusee(mock_api):
    mock_api(lambda request: httpx2.Response(200, json=[{"site_id": "SITE001"}]))
    with pytest.raises(ValidationError):
        await statistic_service.get_stats_summary()


async def test_simulation_de_pic(mock_api):
    requetes = mock_api(lambda request: httpx2.Response(200, json={"status": "ok"}))
    assert await simulation_service.simulate_spike("SITE002", 45) == {"status": "ok"}
    assert requetes[0].method == "POST"
    assert requetes[0].url.path == "/api/v1/simulate/spike/SITE002"
    assert requetes[0].url.params["duration_minutes"] == "45"


@pytest.mark.parametrize("duree", [0, 241])
async def test_simulation_refuse_une_duree_hors_bornes(duree):
    with pytest.raises(ValueError, match="duration_minutes"):
        await simulation_service.simulate_spike("SITE002", duree)

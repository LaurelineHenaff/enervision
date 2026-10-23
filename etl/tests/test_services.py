"""Services du client de l'API Mock : URL, authentification, paramètres et validation (mock simulé)."""
import base64
from datetime import UTC, datetime, timedelta, timezone

import httpx2
import pytest
from pydantic import ValidationError

from mock_client import config
from mock_client.schemas.site import Site
from mock_client.services import (
    alert_service,
    reading_service,
    sensor_service,
    simulation_service,
    site_service,
    statistic_service,
)
from tests.conftest import SITE_EXAMPLE

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


async def test_sites_url_and_authentication(mock_api):
    received_requests = mock_api(lambda request: httpx2.Response(200, json=[SITE_EXAMPLE]))

    assert await site_service.get_all_sites() == [Site(**SITE_EXAMPLE)]

    assert str(received_requests[0].url) == "http://mock.test/api/v1/sites"
    expected = base64.b64encode(b"utilisateur-test:motdepasse-test").decode()
    assert received_requests[0].headers["authorization"] == f"Basic {expected}"


async def test_no_credentials_no_authentication(mock_api, monkeypatch):
    monkeypatch.setattr(config, "MOCK_API_USERNAME", None)
    monkeypatch.setattr(config, "MOCK_API_PASSWORD", None)
    received_requests = mock_api(lambda request: httpx2.Response(200, json=[]))

    assert await site_service.get_all_sites() == []
    assert "authorization" not in received_requests[0].headers


async def test_site_detail(mock_api):
    received_requests = mock_api(lambda request: httpx2.Response(200, json=SITE_EXAMPLE))
    assert (await site_service.get_site("SITE001")).site_name == "Bureau Paris"
    assert received_requests[0].url.path == "/api/v1/sites/SITE001"


async def test_unknown_site_propagates_404(mock_api):
    mock_api(lambda request: httpx2.Response(404))
    with pytest.raises(httpx2.HTTPStatusError) as error:
        await site_service.get_site("SITE999")
    assert error.value.response.status_code == 404


async def test_server_error_propagated(mock_api):
    mock_api(lambda request: httpx2.Response(500))
    with pytest.raises(httpx2.HTTPStatusError):
        await site_service.get_all_sites()


@pytest.mark.parametrize("error", [httpx2.ConnectError("connection refused"), httpx2.ReadTimeout("timeout")]
)
async def test_unreachable_or_slow_network_propagated(mock_api, error):
    def handler(request):
        error.request = request
        raise error

    mock_api(handler)
    with pytest.raises(httpx2.RequestError):
        await site_service.get_all_sites()


async def test_invalid_data_rejected(mock_api):
    mock_api(lambda request: httpx2.Response(200, json=[{**SITE_EXAMPLE, "capacity_kw": "beaucoup"}]))
    with pytest.raises(ValidationError):
        await site_service.get_all_sites()


async def test_unexpected_response_rejected(mock_api):
    mock_api(lambda request: httpx2.Response(200, json={"detail": "other format"}))
    with pytest.raises(ValidationError):
        await site_service.get_all_sites()


async def test_current_reading_keeps_nulls(mock_api):
    received_requests = mock_api(lambda request: httpx2.Response(200, json=READING))
    reading = await reading_service.get_current_reading("SITE001")
    assert received_requests[0].url.path == "/api/v1/sites/SITE001/current"
    assert reading.humidity_percent is None
    assert reading.null_reasons == ["humidity_sensor_failure"]


async def test_readings_parameters_in_utc(mock_api):
    received_requests = mock_api(lambda request: httpx2.Response(200, json=[READING]))
    paris = timezone(timedelta(hours=2))

    readings = await reading_service.get_readings(
        site_id="SITE001",
        start_time=datetime(2024, 3, 13, 10, 0, tzinfo=paris),
        end_time=datetime(2024, 3, 13, 12, 0, tzinfo=UTC),
        limit=500,
    )

    assert len(readings) == 1
    params = received_requests[0].url.params
    assert params["site_id"] == "SITE001"
    assert params["limit"] == "500"
    assert params["start_time"] == "2024-03-13T08:00:00+00:00"
    assert params["end_time"] == "2024-03-13T12:00:00+00:00"


async def test_readings_reject_naive_timestamp():
    with pytest.raises(ValueError, match="timezone"):
        await reading_service.get_readings(start_time=datetime(2024, 3, 13, 10, 0))


@pytest.mark.parametrize("limit", [0, 1001])
async def test_readings_reject_out_of_range_limit(limit):
    with pytest.raises(ValueError, match="limit"):
        await reading_service.get_readings(limit=limit)


async def test_alerts_filters_and_empty_list(mock_api):
    received_requests = mock_api(lambda request: httpx2.Response(200, json=[]))
    assert await alert_service.get_alerts(site_id="SITE003", severity="high") == []
    assert received_requests[0].url.params["site_id"] == "SITE003"
    assert received_requests[0].url.params["severity"] == "high"


async def test_alert_without_value(mock_api):
    alert_payload = {
        "alert_id": "A1", "timestamp": "2026-10-22T10:00:00", "site_id": "SITE003",
        "severity": "high", "type": "spike", "message": "pic", "value": None, "threshold": 630.0,
    }  # fmt: skip
    mock_api(lambda request: httpx2.Response(200, json=[alert_payload]))
    assert (await alert_service.get_alerts())[0].value is None


async def test_sensors_indexed_by_site(mock_api):
    body = {
        "SITE001": {
            "site_name": "Bureau",
            "overall": "degraded",
            "sensors": {
                "consumption": {"status": "ok", "failing_until": None},
                "humidity": {"status": "failing", "failing_until": "2026-10-23T12:51:10"},
            },
        }
    }
    mock_api(lambda request: httpx2.Response(200, json=body))
    sites = await sensor_service.get_sensors_status()
    assert sites[0].site_id == "SITE001"
    assert sites[0].overall == "degraded"
    assert sites[0].sensors["humidity"].failing_until is not None


async def test_fleet_summary(mock_api):
    body = {
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
    mock_api(lambda request: httpx2.Response(200, json=body))
    summary = await statistic_service.get_stats_summary()
    assert summary.total_sites == 2
    assert summary.sites[1].current_consumption_kw is None


async def test_unexpected_summary_rejected(mock_api):
    mock_api(lambda request: httpx2.Response(200, json=[{"site_id": "SITE001"}]))
    with pytest.raises(ValidationError):
        await statistic_service.get_stats_summary()


async def test_spike_simulation(mock_api):
    received_requests = mock_api(lambda request: httpx2.Response(200, json={"status": "ok"}))
    assert await simulation_service.simulate_spike("SITE002", 45) == {"status": "ok"}
    assert received_requests[0].method == "POST"
    assert received_requests[0].url.path == "/api/v1/simulate/spike/SITE002"
    assert received_requests[0].url.params["duration_minutes"] == "45"


@pytest.mark.parametrize("duration", [0, 241])
async def test_simulation_rejects_out_of_range_duration(duration):
    with pytest.raises(ValueError, match="duration_minutes"):
        await simulation_service.simulate_spike("SITE002", duration)


def test_client_base_url_and_timeout():
    from mock_client.client import TIMEOUT_SECONDS, mock_client

    client = mock_client()
    assert str(client.base_url).startswith("http://mock.test/api/v1")
    assert client.timeout.read == TIMEOUT_SECONDS


async def test_raw_response_keeps_status_and_reception_time(mock_api):
    from mock_client.client import fetch_raw

    received_requests = mock_api(lambda request: httpx2.Response(200, json=[{"site_id": "SITE001"}]))
    raw_response = await fetch_raw("/readings", {"site_id": "SITE001", "limit": 5})

    assert raw_response.endpoint == "/api/v1/readings"
    assert raw_response.params == {"site_id": "SITE001", "limit": "5"}
    assert raw_response.http_status == 200
    assert raw_response.payload == [{"site_id": "SITE001"}]
    assert raw_response.fetched_at.tzinfo is not None and raw_response.fetched_at.utcoffset() == timedelta(0)
    assert len(received_requests) == 1


async def test_raw_response_keeps_failures_without_raising(mock_api):
    from mock_client.client import fetch_raw

    def handler(request):
        if request.url.path.endswith("/sites/SITE999"):
            return httpx2.Response(404, json={"detail": "inconnu"})
        return httpx2.Response(502, text="<html>erreur</html>")

    mock_api(handler)
    unknown = await fetch_raw("/sites/SITE999")
    assert (unknown.http_status, unknown.payload) == (404, {"detail": "inconnu"})
    gateway = await fetch_raw("/sites")
    assert (gateway.http_status, gateway.payload) == (502, None)


async def test_raw_response_propagates_network_errors(mock_api):
    from mock_client.client import fetch_raw

    def handler(request):
        raise httpx2.ConnectError("connection refused", request=request)

    mock_api(handler)
    with pytest.raises(httpx2.RequestError):
        await fetch_raw("/sites")


def test_mock_timestamps_converted_to_utc():
    from mock_client.schemas.reading import Reading

    naive = Reading.model_validate({**READING, "timestamp": "2026-10-23T12:50:25.646645"})
    with_z = Reading.model_validate({**READING, "timestamp": "2026-10-23T12:50:25.646645Z"})
    paris = Reading.model_validate({**READING, "timestamp": "2026-10-23T14:50:25.646645+02:00"})
    assert naive.timestamp == with_z.timestamp == paris.timestamp
    assert naive.timestamp.utcoffset() == timedelta(0)


def test_null_reasons_default_empty_and_quality_required():
    from mock_client.schemas.reading import Reading

    assert Reading.model_validate({**READING, "null_reasons": None}).null_reasons == []
    assert Reading.model_validate({k: v for k, v in READING.items() if k != "null_reasons"}).null_reasons == []
    with pytest.raises(ValidationError):
        Reading.model_validate({**READING, "data_quality": None})
    with pytest.raises(ValidationError):
        Reading.model_validate({**READING, "data_quality": "inconnue"})

"""Routes /sites : liste, détail, mesures, consommation agrégée et qualité."""
import pytest


async def test_routes_require_a_token(client):
    assert (await client.get("/sites")).status_code == 401


async def test_list_and_get_site(auth_client, site_with_readings):
    sites = (await auth_client.get("/sites")).json()
    assert site_with_readings in [s["site_id"] for s in sites]

    site = (await auth_client.get(f"/sites/{site_with_readings}")).json()
    assert site["site_name"] == "Site de test"


async def test_unknown_site_is_404(auth_client):
    assert (await auth_client.get("/sites/INCONNU")).status_code == 404
    assert (await auth_client.get("/sites/INCONNU/readings")).status_code == 404


async def test_readings_period_and_pagination(auth_client, site_with_readings):
    url = f"/sites/{site_with_readings}/readings"

    page = (await auth_client.get(url, params={"limit": 10, "offset": 5})).json()
    assert len(page) == 10
    assert page[0]["time"].startswith("2023-01-01T05:00")

    period = {"start": "2023-01-02T00:00:00Z", "end": "2023-01-02T03:00:00Z"}
    rows = (await auth_client.get(url, params=period)).json()
    assert [r["consumption_kwh"] for r in rows] == [2.0, 2.0, 2.0]


async def test_readings_rejects_reversed_period(auth_client, site_with_readings):
    period = {"start": "2023-01-02T00:00:00Z", "end": "2023-01-01T00:00:00Z"}
    response = await auth_client.get(f"/sites/{site_with_readings}/readings", params=period)
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("bucket", "expected_kwh"),
    # Les semaines de time_bucket commencent le lundi : le dimanche 01/01/2023 est seul dans la sienne
    [("day", [24.0, 48.0]), ("week", [24.0, 48.0]), ("month", [72.0])],
)
async def test_consumption_by_bucket(auth_client, site_with_readings, bucket, expected_kwh):
    rows = (
        await auth_client.get(f"/sites/{site_with_readings}/consumption", params={"bucket": bucket})
    ).json()

    assert [r["consumption_kwh"] for r in rows] == pytest.approx(expected_kwh)
    assert sum(r["nb_readings"] for r in rows) == 48


async def test_consumption_by_day_details(auth_client, site_with_readings):
    first_day = (await auth_client.get(f"/sites/{site_with_readings}/consumption")).json()[0]

    assert first_day["start"].startswith("2023-01-01")
    assert first_day["consumption_euros"] == pytest.approx(3.6)
    assert first_day["max_consumption_kw"] == 1.0
    assert first_day["avg_temperature_celsius"] == 10.0


async def test_quality_shares(auth_client, site_with_readings):
    rows = (await auth_client.get(f"/sites/{site_with_readings}/quality")).json()

    assert rows == [
        {"data_quality": "observed", "nb_readings": 47, "share": pytest.approx(0.9792)},
        {"data_quality": "interpolated", "nb_readings": 1, "share": pytest.approx(0.0208)},
    ]

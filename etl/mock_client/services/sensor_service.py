from mock_client.client import get_json
from mock_client.schemas.sensor import SiteSensors


async def get_sensors_status() -> list[SiteSensors]:
    """État des capteurs de chaque site ; le mock renvoie un objet indexé par site_id."""
    data = await get_json("/sensors/status")
    return [SiteSensors(site_id=site_id, **info) for site_id, info in data.items()]

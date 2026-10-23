import httpx2

from api_mock.config import MOCK_API_PASSWORD, MOCK_API_URL, MOCK_API_USERNAME
from api_mock.schemas.sensor import SiteSensors


async def get_all_sensors() -> list[SiteSensors]:
    async with httpx2.AsyncClient(auth=(MOCK_API_USERNAME, MOCK_API_PASSWORD)) as client:
        response = await client.get(f"{MOCK_API_URL}/api/v1/sensors/status")
        response.raise_for_status()
        data = response.json()
        return [SiteSensors(site=site, **info) for site, info in data.items()]

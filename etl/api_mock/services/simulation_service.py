import httpx2

from api_mock.config import MOCK_API_PASSWORD, MOCK_API_URL, MOCK_API_USERNAME


async def simulate_spike(site_id: str, duration_minutes: int) -> dict:
    url = f"{MOCK_API_URL}/api/v1/simulate/spike/{site_id}"
    async with httpx2.AsyncClient(auth=(MOCK_API_USERNAME, MOCK_API_PASSWORD)) as client:
        response = await client.post(url, params={"duration_minutes": duration_minutes})
        response.raise_for_status()
        return response.json()

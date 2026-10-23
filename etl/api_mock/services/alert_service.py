import httpx2

from api_mock.config import MOCK_API_PASSWORD, MOCK_API_URL, MOCK_API_USERNAME
from api_mock.schemas.alert import Alert


async def get_all_alerts() -> list[Alert]:
    """
    Récupère tous les alertes relevées depuis l'API Mock.
    """
    async with httpx2.AsyncClient(auth=(MOCK_API_USERNAME, MOCK_API_PASSWORD)) as client:
        # Remplace l'URL par celle de ton API Mock réelle
        response = await client.get(f"{MOCK_API_URL}/api/v1/alerts")
        response.raise_for_status()
        return [Alert(**item) for item in response.json()]

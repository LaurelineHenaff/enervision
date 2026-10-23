import httpx2

from api_mock.config import MOCK_API_PASSWORD, MOCK_API_URL, MOCK_API_USERNAME
from api_mock.schemas.reading import Reading


async def get_all_readings(
    site_id: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    limit: int = 100,
) -> list[Reading]:
    """
    Récupère les relevés depuis l'API Mock en appliquant les filtres.
    """
    async with httpx2.AsyncClient(auth=(MOCK_API_USERNAME, MOCK_API_PASSWORD)) as client:
        # Construction du dictionnaire de paramètres en ignorant les valeurs vides
        params = {"limit": limit}
        if site_id:
            params["site_id"] = site_id
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        # Remplacez l'URL par celle issue de votre configuration (ex: MOCK_API_URL)
        response = await client.get(f"{MOCK_API_URL}/api/v1/readings", params=params)
        response.raise_for_status()

        return [Reading(**item) for item in response.json()]

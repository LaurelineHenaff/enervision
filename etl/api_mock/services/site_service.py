import httpx2

from api_mock.config import MOCK_API_PASSWORD, MOCK_API_URL, MOCK_API_USERNAME
from api_mock.schemas.site import Site


async def get_all_sites() -> list[Site]:
    if not MOCK_API_USERNAME or not MOCK_API_PASSWORD:
        raise RuntimeError("Identifiants API Mock non configurés")

    async with httpx2.AsyncClient(
        timeout=10.0,
        auth=httpx2.BasicAuth(
            MOCK_API_USERNAME,
            MOCK_API_PASSWORD
        )
    ) as client:
        response = await client.get(
            f"{MOCK_API_URL}/api/v1/sites"
        )
        response.raise_for_status()

        return [
            Site.model_validate(site)
            for site in response.json()
        ]
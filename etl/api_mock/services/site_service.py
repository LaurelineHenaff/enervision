import httpx2

from api_mock.config import MOCK_API_PASSWORD, MOCK_API_URL, MOCK_API_USERNAME
from api_mock.schemas.reading import Reading
from api_mock.schemas.site import Site
from api_mock.schemas.siteInfo import SiteInfo


async def get_all_sites() -> list[Site]:
    if not MOCK_API_USERNAME or not MOCK_API_PASSWORD:
        raise RuntimeError("Identifiants API Mock non configurés")

    async with httpx2.AsyncClient(
        timeout=10.0, auth=httpx2.BasicAuth(MOCK_API_USERNAME, MOCK_API_PASSWORD)
    ) as client:
        response = await client.get(f"{MOCK_API_URL}/api/v1/sites")
        response.raise_for_status()

        return [Site.model_validate(site) for site in response.json()]


async def get_current_site(site_id: str) -> Reading:
    """
    Récupère le site courant pour un ID donné.
    """
    try:
        async with httpx2.AsyncClient(
            auth=(MOCK_API_USERNAME, MOCK_API_PASSWORD)
        ) as client:
            response = await client.get(
                f"{MOCK_API_URL}/api/v1/sites/{site_id}/current"
            )
            response.raise_for_status()

            return Reading(**response.json())

    except httpx2.HTTPStatusError as e:
        print(f"Erreur HTTP : {e}")
        raise


async def get_site_detail(site_id: str) -> SiteInfo:
    """Récupère le détail d'un site depuis l'API Mock."""

    if not MOCK_API_USERNAME or not MOCK_API_PASSWORD:
        raise RuntimeError("Identifiants API Mock non configurés")

    async with httpx2.AsyncClient(
        timeout=10.0,
        auth=httpx2.BasicAuth(
            MOCK_API_USERNAME,
            MOCK_API_PASSWORD,
        ),
    ) as client:
        response = await client.get(f"{MOCK_API_URL}/api/v1/sites/{site_id}")
        response.raise_for_status()

        return SiteInfo.model_validate(response.json())

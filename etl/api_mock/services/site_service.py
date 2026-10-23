from api_mock.client import get_json
from api_mock.schemas.site import Site


async def get_all_sites() -> list[Site]:
    return [Site.model_validate(site) for site in await get_json("/sites")]


async def get_site(site_id: str) -> Site:
    """Détail d'un site ; lève httpx2.HTTPStatusError (404) si le site est inconnu."""
    return Site.model_validate(await get_json(f"/sites/{site_id}"))

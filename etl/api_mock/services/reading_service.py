from datetime import UTC, datetime

from api_mock.client import get_json
from api_mock.schemas.reading import Reading

LIMIT_MAX = 1000


def _en_utc(moment: datetime) -> str:
    # Le mock raisonne en UTC : un horodatage sans fuseau serait interprété à tort
    if moment.tzinfo is None:
        raise ValueError("L'horodatage doit porter un fuseau horaire")
    return moment.astimezone(UTC).isoformat()


async def get_current_reading(site_id: str) -> Reading:
    """Mesure instantanée d'un site. Elle peut contenir des null (panne de capteur)."""
    return Reading.model_validate(await get_json(f"/sites/{site_id}/current"))


async def get_readings(
    site_id: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = 100,
) -> list[Reading]:
    """Historique simulé, trié par horodatage croissant.

    Le mock renvoie une grille régulière de `limit` points sur la fenêtre (pas = fenêtre
    divisée par `limit`), répartis à parts égales entre les sites si `site_id` est omis :
    interroger un site à la fois, sur une fenêtre fixe.
    """
    if not 1 <= limit <= LIMIT_MAX:
        raise ValueError(f"limit doit être compris entre 1 et {LIMIT_MAX}")

    params: dict[str, str | int] = {"limit": limit}
    if site_id:
        params["site_id"] = site_id
    if start_time:
        params["start_time"] = _en_utc(start_time)
    if end_time:
        params["end_time"] = _en_utc(end_time)

    return [Reading.model_validate(item) for item in await get_json("/readings", params)]

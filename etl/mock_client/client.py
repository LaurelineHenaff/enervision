"""Client HTTP de l'API Mock : URL de base, authentification facultative et délai d'attente.

Les services passent par get_json et post_json, pour que l'URL, l'authentification et le délai
soient réglés à un seul endroit. Les erreurs HTTP (httpx2.HTTPStatusError) et réseau
(httpx2.RequestError) sont propagées telles quelles à l'appelant.
"""
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx2

from mock_client import config

TIMEOUT_SECONDS = 10.0


def mock_client() -> httpx2.AsyncClient:
    credentials = (config.MOCK_API_USERNAME, config.MOCK_API_PASSWORD)
    # Authentification basique requise sur l'URL publique, absente sur le réseau de l'école
    auth = httpx2.BasicAuth(*credentials) if all(credentials) else None
    return httpx2.AsyncClient(
        base_url=f"{config.MOCK_API_URL}/api/v1", timeout=TIMEOUT_SECONDS, auth=auth
    )


async def get_json(path: str, params: dict | None = None):
    async with mock_client() as client:
        response = await client.get(path, params=params)
        response.raise_for_status()
        return response.json()


async def post_json(path: str, params: dict | None = None):
    async with mock_client() as client:
        response = await client.post(path, params=params)
        response.raise_for_status()
        return response.json()


@dataclass(frozen=True)
class RawResponse:
    """Réponse du mock telle que reçue, pour raw.api_response."""

    endpoint: str  # chemin appelé, par exemple /api/v1/sites/SITE001/current
    params: dict[str, str]
    http_status: int
    fetched_at: datetime  # UTC, relevée par notre code à la réception (received_at)
    payload: Any | None  # JSON tel que reçu, None si la réponse n'est pas du JSON


async def fetch_raw(path: str, params: dict | None = None, method: str = "GET") -> RawResponse:
    """Appelle le mock sans lever d'erreur sur un statut 4xx ou 5xx : l'échec est lui aussi conservé.

    Seules les erreurs réseau (httpx2.RequestError) sont propagées.
    """
    async with mock_client() as client:
        response = await client.request(method, path, params=params)
    fetched_at = datetime.now(UTC)
    try:
        payload = response.json()
    except ValueError:
        payload = None
    return RawResponse(
        endpoint=response.request.url.path,
        params=dict(response.request.url.params),
        http_status=response.status_code,
        fetched_at=fetched_at,
        payload=payload,
    )

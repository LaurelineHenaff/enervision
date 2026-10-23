"""Client HTTP de l'API Mock : URL de base, authentification facultative et délai d'attente.

Les services passent par get_json et post_json, pour que l'URL, l'authentification et le délai
soient réglés à un seul endroit. Les erreurs HTTP (httpx2.HTTPStatusError) et réseau
(httpx2.RequestError) sont propagées telles quelles à l'appelant.
"""
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

from mock_client.client import post_json

DURATION_MAX_MINUTES = 240


async def simulate_spike(site_id: str, duration_minutes: int = 30) -> dict:
    """Déclenche un pic fictif sur un site du mock.

    Le mock est partagé entre les équipes : à n'utiliser qu'avec l'accord de l'équipe.
    """
    if not 1 <= duration_minutes <= DURATION_MAX_MINUTES:
        raise ValueError(f"duration_minutes doit être compris entre 1 et {DURATION_MAX_MINUTES}")
    return await post_json(f"/simulate/spike/{site_id}", {"duration_minutes": duration_minutes})

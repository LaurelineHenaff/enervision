import httpx2

from api_mock.config import MOCK_API_PASSWORD, MOCK_API_URL, MOCK_API_USERNAME
from api_mock.schemas.statistic import Statistic


async def get_all_statistics() -> list[Statistic]:
    """
    Récupère toutes les statistiques relevées depuis l'API Mock.
    """
    async with httpx2.AsyncClient(auth=(MOCK_API_USERNAME, MOCK_API_PASSWORD)) as client:
        response = await client.get(f"{MOCK_API_URL}/api/v1/stats/summary")
        response.raise_for_status()
        data = response.json()

        # 1. Si la réponse est déjà une liste
        if isinstance(data, list):
            return [Statistic(**item) for item in data if isinstance(item, dict)]

        # 2. Si la réponse est un dictionnaire
        if isinstance(data, dict):
            # Cas A : Un seul objet statistique complet
            if "site_id" in data:
                return [Statistic(**data)]

            # Cas B : Données encapsulées (ex: {"data": [...]})
            for key in ["data", "statistics", "summary"]:
                if key in data and isinstance(data[key], list):
                    return [
                        Statistic(**item)
                        for item in data[key]
                        if isinstance(item, dict)
                    ]

            # Cas C : Dictionnaire clé-valeur (ex: {"SITE001": 150.5, "SITE002": {"current_consumption_kw": 40}})
            results = []
            for key, value in data.items():
                if isinstance(value, dict):
                    val_copy = value.copy()
                    val_copy.setdefault("site_id", key)
                    results.append(Statistic(**val_copy))
                else:
                    try:
                        consumption = float(value) if value is not None else None
                    except (ValueError, TypeError):
                        consumption = None
                    results.append(
                        Statistic(site_id=key, current_consumption_kw=consumption)
                    )
            return results
        return []

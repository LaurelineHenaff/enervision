from mock_client.client import get_json
from mock_client.schemas.stats import StatsSummary


async def get_stats_summary() -> StatsSummary:
    return StatsSummary.model_validate(await get_json("/stats/summary"))

from api_mock.client import get_json
from api_mock.schemas.stats import StatsSummary


async def get_stats_summary() -> StatsSummary:
    return StatsSummary.model_validate(await get_json("/stats/summary"))

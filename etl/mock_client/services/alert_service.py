from typing import Literal

from mock_client.client import get_json
from mock_client.schemas.alert import Alert

Severity = Literal["low", "medium", "high", "critical"]


async def get_alerts(site_id: str | None = None, severity: Severity | None = None) -> list[Alert]:
    """Alertes de consommation actives (liste vide possible)."""
    params = {
        key: value
        for key, value in {"site_id": site_id, "severity": severity}.items()
        if value
    }
    return [Alert.model_validate(item) for item in await get_json("/alerts", params)]

from typing import Literal

import httpx2
from fastapi import APIRouter, HTTPException, Query

from api_mock.schemas.alert import Alert
from api_mock.services.alert_service import get_all_alerts

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=list[Alert], summary="Alertes actives")
async def list_alerts(
    site_id: str = Query(None, description="Filtrer par site"),
    severity: Literal["low", "medium", "high", "critical"] = Query(
        None, description="Filtrer par sévérité : low | medium | high | critical"
    ),
) -> list[Alert]:
    try:
        return await get_all_alerts(site_id=site_id, severity=severity)
    except httpx2.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"API Mock a répondu {e.response.status_code}",
        )
    except httpx2.RequestError:
        raise HTTPException(status_code=503, detail="API Mock injoignable")

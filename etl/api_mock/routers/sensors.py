import httpx2
from fastapi import APIRouter, HTTPException

from api_mock.schemas.sensor import SiteSensors
from api_mock.services.sensor_service import get_all_sensors

router = APIRouter(prefix="/sensors", tags=["Sensors"])


@router.get("", response_model=list[SiteSensors], summary="État des capteurs par site")
async def list_sensors() -> list[SiteSensors]:
    try:
        return await get_all_sensors()
    except httpx2.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"API Mock a répondu {e.response.status_code}",
        )
    except httpx2.RequestError:
        raise HTTPException(status_code=503, detail="API Mock injoignable")

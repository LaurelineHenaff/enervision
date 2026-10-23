
import httpx2
from fastapi import APIRouter, HTTPException

from api_mock.schemas.reading import Reading
from api_mock.services.reading_service import get_all_readings
from api_mock.services.site_service import get_current_site

router = APIRouter(prefix="/readings", tags=["Readings"])


@router.get("", response_model=list[Reading], summary="Historique des lectures")
async def list_readings() -> list[Reading]:
    try:
        return await get_all_readings()
    except httpx2.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"API Mock a répondu {e.response.status_code}",
        )
    except httpx2.RequestError:
        raise HTTPException(status_code=503, detail="API Mock injoignable")


@router.get(
    "/{site_id}/current", response_model=Reading, summary="Lecture temps réel d'un site"
)
async def get_site_current(site_id: str) -> Reading:
    try:
        return await get_current_site(site_id)
    except httpx2.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"API Mock a répondu {e.response.status_code}",
        )
    except httpx2.RequestError:
        raise HTTPException(status_code=503, detail="API Mock injoignable")

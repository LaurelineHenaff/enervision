import httpx2
from fastapi import APIRouter, HTTPException

from api_mock.schemas.site import Site
from api_mock.services.site_service import get_all_sites

router = APIRouter(prefix="/sites", tags=["sites"])


@router.get("", response_model=list[Site])
async def list_sites() -> list[Site]:
    try:
        return await get_all_sites()
    except httpx2.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"API Mock a répondu {e.response.status_code}",
        )
    except httpx2.RequestError:
        raise HTTPException(status_code=503, detail="API Mock injoignable")
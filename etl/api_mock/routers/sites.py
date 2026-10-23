import httpx2
from fastapi import APIRouter, HTTPException

from api_mock.schemas.site import Site
from api_mock.schemas.siteInfo import SiteInfo
from api_mock.services.site_service import get_all_sites, get_site_detail

router = APIRouter(prefix="/sites", tags=["Sites"])


@router.get("", response_model=list[Site], summary="Liste de tous les sites")
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


@router.get(
    "/{site_id}",
    response_model=SiteInfo,
    summary="Détail d'un site",
)
async def site_detail(site_id: str) -> SiteInfo:
    try:
        return await get_site_detail(site_id)

    except httpx2.HTTPStatusError as e:
        status_code = 404 if e.response.status_code == 404 else 502
        raise HTTPException(
            status_code=status_code,
            detail=f"API Mock a répondu {e.response.status_code}",
        ) from e

    except httpx2.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail="API Mock injoignable",
        ) from e

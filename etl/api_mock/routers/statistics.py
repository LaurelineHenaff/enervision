import httpx2
from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from api_mock.schemas.statistic import Statistic
from api_mock.services.statistic_service import get_all_statistics

router = APIRouter(prefix="/statistics", tags=["Statistics"])


@router.get("", response_model=list[Statistic], summary="Statistiques globales")
async def list_statistics() -> list[Statistic]:
    try:
        return await get_all_statistics()
    except httpx2.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"API Mock a répondu {e.response.status_code}",
        )
    except httpx2.RequestError:
        raise HTTPException(status_code=503, detail="API Mock injoignable")
    except ValidationError:
        raise HTTPException(
            status_code=502,
            detail="API Mock a renvoyé des données qui ne respectent pas le format attendu",
        )

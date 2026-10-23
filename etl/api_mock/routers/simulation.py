import httpx2
from fastapi import APIRouter, HTTPException, Query

from api_mock.services.simulation_service import simulate_spike

router = APIRouter(prefix="/simulation", tags=["Simulation"])


@router.post("/spike/{site_id}", summary="Simuler un pic de consommation")
async def create_simulation(
    site_id: str, duration_minutes: int = Query(30, ge=1, le=240)
) -> dict:
    try:
        return await simulate_spike(site_id, duration_minutes)
    except httpx2.HTTPStatusError as e:
        raise HTTPException(502, f"API Mock a répondu {e.response.status_code}") from e
    except httpx2.RequestError as e:
        raise HTTPException(503, "API Mock injoignable") from e

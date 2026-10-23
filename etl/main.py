from fastapi import FastAPI

from api_mock.routers.alerts import router as alerts_router
from api_mock.routers.readings import router as reading_router
from api_mock.routers.sensors import router as sensors_router
from api_mock.routers.simulation import router as simulation_router
from api_mock.routers.sites import router as sites_router
from api_mock.routers.statistics import router as statistics_router

app = FastAPI()

app.include_router(sites_router)
app.include_router(reading_router)
app.include_router(alerts_router)
app.include_router(statistics_router)
app.include_router(sensors_router)
app.include_router(simulation_router)

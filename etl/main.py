from fastapi import FastAPI

from api_mock.routers.sites import router as sites_router

app = FastAPI()

app.include_router(sites_router)
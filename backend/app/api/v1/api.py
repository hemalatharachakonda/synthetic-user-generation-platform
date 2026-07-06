from fastapi import APIRouter

from app.api.v1.endpoints import experiments, personas, surveys

api_router = APIRouter()
api_router.include_router(experiments.router)
api_router.include_router(personas.router)
api_router.include_router(surveys.router)

from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.prediction import router as prediction_router
from app.api.routes.history import router as history_router
from app.api.routes.reports import router as reports_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(prediction_router)
api_router.include_router(history_router)
api_router.include_router(reports_router)

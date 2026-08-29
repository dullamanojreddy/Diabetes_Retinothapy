from datetime import datetime
from fastapi import APIRouter
from app.core.config import settings
from app.ml.model import model_manager
from app.schemas.prediction import HealthResponse

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        model_loaded=model_manager.is_loaded,
        model="EfficientNet-B3",
        device=str(model_manager.device) if model_manager.device else "unknown",
        version=settings.VERSION,
        timestamp=datetime.utcnow()
    )

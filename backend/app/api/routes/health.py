from datetime import datetime
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.ml.model import model_manager
from app.schemas.prediction import HealthResponse

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
async def health_liveness():
    """
    Liveness probe reporting process status.
    """
    return HealthResponse(
        status="healthy",
        model_loaded=model_manager.is_loaded,
        model="EfficientNet-B3",
        device=str(model_manager.device) if model_manager.device else "unknown",
        version=settings.VERSION,
        timestamp=datetime.utcnow()
    )

@router.get("/health/ready")
async def health_readiness():
    """
    Readiness probe verifying model initialization and storage accessibility.
    Returns HTTP 200 when ready to accept traffic, or HTTP 503 if unready.
    """
    # Check model initialization
    model_ok = bool(model_manager.is_loaded and model_manager.model is not None)
    
    # Check storage directory accessibility
    storage_ok = False
    try:
        test_dir = settings.absolute_results_dir
        test_dir.mkdir(parents=True, exist_ok=True)
        test_file = test_dir / ".health_probe"
        test_file.write_text("ok")
        if test_file.exists():
            test_file.unlink()
            storage_ok = True
    except Exception:
        storage_ok = False

    is_ready = model_ok and storage_ok
    status_str = "ready" if is_ready else "not_ready"
    http_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    payload = {
        "status": status_str,
        "model_loaded": model_ok,
        "model_version": settings.MODEL_VERSION,
        "storage_available": storage_ok,
        "timestamp": datetime.utcnow().isoformat()
    }
    return JSONResponse(status_code=http_code, content=payload)

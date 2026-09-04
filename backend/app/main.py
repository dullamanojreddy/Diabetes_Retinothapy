from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging_config import logger
from app.api.routes import api_router
from app.ml.model import model_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load ML model once
    logger.info("Initializing application startup...")
    settings.absolute_results_dir.mkdir(parents=True, exist_ok=True)
    settings.absolute_upload_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        model_manager.load_model()
        logger.info("EfficientNet-B3 model successfully loaded into memory.")
    except Exception as e:
        logger.error(f"Critical error during model startup initialization: {e}")
        
    yield
    
    # Shutdown
    logger.info("Shutting down Explainable DR Screening API...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-grade AI API for Explainable Diabetic Retinopathy screening with Grad-CAM visual attention heatmaps.",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static storage for generated Grad-CAM heatmaps and overlays
settings.absolute_results_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    "/storage/results",
    StaticFiles(directory=str(settings.absolute_results_dir)),
    name="results_storage"
)
app.mount(
    "/results",
    StaticFiles(directory=str(settings.absolute_results_dir)),
    name="results"
)

# Include API Router
app.include_router(api_router, prefix=settings.API_PREFIX)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "An internal server error occurred while processing the request.",
            "detail": str(exc)
        }
    )

@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_PREFIX}/health",
        "status": "online"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

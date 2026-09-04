from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, status, Request
from fastapi.responses import JSONResponse
from app.services.prediction_service import prediction_service

router = APIRouter(tags=["Prediction"])

@router.post("/prediction")
@router.post("/predict")
async def screen_retinopathy(
    file: UploadFile = File(..., description="Retinal fundus image (JPEG, JPG, PNG)"),
    target_class: Optional[int] = Form(None, description="Optional class ID for Grad-CAM focus (0-4)")
):
    """
    End-to-end Diabetic Retinopathy screening workflow:
    1. File & security validation
    2. Multi-signal fundus validation gate
    3. Technical image quality checks
    4. FOV crop and 380x380 preprocessing
    5. EfficientNet-B3 model inference
    6. Calibrated referable DR threshold evaluation
    7. Grad-CAM visual attention heatmap generation
    8. History persistence
    """
    http_status, result = await prediction_service.process_screening(
        file,
        target_class_override=target_class
    )
    return JSONResponse(status_code=http_status, content=result)

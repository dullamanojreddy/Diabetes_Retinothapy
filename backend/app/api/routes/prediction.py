from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form
from app.services.prediction_service import prediction_service
from app.schemas.prediction import PredictionResponse

router = APIRouter(tags=["Prediction"])

@router.post("/predict", response_model=PredictionResponse)
async def predict_retinopathy(
    file: UploadFile = File(..., description="Retinal fundus image (PNG, JPG, JPEG, WEBP)"),
    target_class: Optional[int] = Form(None, description="Optional class ID for Grad-CAM focus (0-4)")
):
    """
    Analyzes an uploaded retinal fundus image:
    1. Preprocesses image (circular FOV crop + 380x380 resize + normalization)
    2. Runs trained EfficientNet-B3 5-class model
    3. Calculates DR severity & referable DR probability
    4. Generates authentic Grad-CAM heatmap & overlay
    5. Returns complete structured result with clinical guidance
    """
    result = await prediction_service.process_screening(file, target_class_override=target_class)
    return result

import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from PIL import Image

from app.core.config import settings
from app.core.logging_config import logger
from app.ml.model import model_manager
from app.ml.preprocessing import preprocess_fundus
from app.ml.inference import run_inference
from app.ml.gradcam import GradCAM
from app.ml.explainability import generate_explanation
from app.services.history_service import history_service
from app.utils.file_utils import generate_unique_id
from app.utils.image_utils import load_image_bytes, save_numpy_image
from app.schemas.prediction import (
    PredictionResponse,
    PredictionClassInfo,
    ReferableRiskInfo,
    ExplainabilityInfo
)

class PredictionService:
    def __init__(self):
        settings.absolute_uploads_dir = settings.absolute_upload_dir
        settings.absolute_results_dir.mkdir(parents=True, exist_ok=True)
        settings.absolute_uploads_dir.mkdir(parents=True, exist_ok=True)

    async def process_screening(
        self,
        file: UploadFile,
        target_class_override: Optional[int] = None
    ) -> PredictionResponse:
        start_time = time.time()
        
        # 1. Validation
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file must have a valid filename."
            )
            
        ext = file.filename.split(".")[-1].lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '.{ext}'. Supported formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
            
        contents = await file.read()
        if not contents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded image file is empty."
            )
            
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(contents) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds max size limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
            )

        # 2. Parse Image
        try:
            pil_image = load_image_bytes(contents)
        except Exception as e:
            logger.error(f"Image decode failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not decode the uploaded file as a valid image."
            )

        prediction_id = generate_unique_id()
        
        # 3. Preprocess Fundus (Crop FOV + 380x380 Resize + ImageNet Normalization)
        try:
            input_tensor, preprocessed_rgb_380 = preprocess_fundus(pil_image)
        except Exception as e:
            logger.error(f"Preprocessing error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error preprocessing retinal fundus image: {str(e)}"
            )

        # 4. Run EfficientNet-B3 Model Inference
        model = model_manager.get_model()
        device = model_manager.device
        
        try:
            inference_result = run_inference(model, input_tensor, device)
        except Exception as e:
            logger.error(f"Model inference failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Inference execution failed: {str(e)}"
            )

        predicted_class_id = inference_result["class_id"]
        confidence = inference_result["confidence"]
        referable_prob = inference_result["referable_probability"]
        is_referable = inference_result["is_referable"]
        probabilities = inference_result["probabilities"]

        # 5. Generate Grad-CAM Explainability Heatmap & Overlay
        gradcam_available = False
        target_explain_class = target_class_override if target_class_override is not None else predicted_class_id
        
        original_filename = f"original_{prediction_id}.jpg"
        heatmap_filename = f"heatmap_{prediction_id}.jpg"
        overlay_filename = f"overlay_{prediction_id}.jpg"
        
        original_path = settings.absolute_results_dir / original_filename
        heatmap_path = settings.absolute_results_dir / heatmap_filename
        overlay_path = settings.absolute_results_dir / overlay_filename

        try:
            # Save original preprocessed fundus
            save_numpy_image(preprocessed_rgb_380, original_path)
            
            # Generate Grad-CAM
            gradcam = GradCAM(model, model_manager.get_gradcam_layer())
            colored_heatmap_rgb, overlay_rgb, _ = gradcam.generate_visualizations(
                input_tensor=input_tensor.to(device),
                original_rgb_380=preprocessed_rgb_380,
                target_class=target_explain_class,
                alpha=0.45
            )
            gradcam.remove_hooks()

            # Save heatmap & overlay
            save_numpy_image(colored_heatmap_rgb, heatmap_path)
            save_numpy_image(overlay_rgb, overlay_path)
            gradcam_available = True
        except Exception as e:
            logger.error(f"Grad-CAM generation failed: {e}")
            # Non-fatal: still return prediction even if Grad-CAM fails

        # 6. Generate Clinical Explanation & Recommendation
        explanation_text, recommendation_text = generate_explanation(
            class_id=predicted_class_id,
            is_referable=is_referable,
            confidence=confidence
        )

        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        
        # Static asset URLs served via FastAPI static mount
        original_url = f"/storage/results/{original_filename}"
        heatmap_url = f"/storage/results/{heatmap_filename}"
        overlay_url = f"/storage/results/{overlay_filename}"

        # 7. Persist to History Database
        history_record = {
            "id": prediction_id,
            "timestamp": datetime.utcnow().isoformat(),
            "filename": file.filename,
            "predicted_class": predicted_class_id,
            "predicted_class_name": inference_result["class_name"],
            "confidence": confidence,
            "referable_probability": referable_prob,
            "is_referable": is_referable,
            "probabilities": probabilities,
            "heatmap_url": heatmap_url,
            "overlay_url": overlay_url,
            "original_url": original_url
        }
        history_service.save(history_record)

        return PredictionResponse(
            success=True,
            id=prediction_id,
            timestamp=datetime.utcnow(),
            filename=file.filename,
            prediction=PredictionClassInfo(
                class_id=predicted_class_id,
                class_name=inference_result["class_name"],
                confidence=confidence
            ),
            referable=ReferableRiskInfo(
                is_referable=is_referable,
                probability=referable_prob,
                threshold=settings.REFERABLE_THRESHOLD
            ),
            probabilities=probabilities,
            explainability=ExplainabilityInfo(
                gradcam_available=gradcam_available,
                heatmap_url=heatmap_url,
                overlay_url=overlay_url,
                original_url=original_url
            ),
            explanation_text=explanation_text,
            referral_recommendation=recommendation_text,
            inference_time_ms=elapsed_ms
        )

prediction_service = PredictionService()

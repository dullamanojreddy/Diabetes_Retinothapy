import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
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
from app.utils.file_utils import generate_unique_id, cleanup_file, sanitize_filename
from app.utils.image_utils import load_image_bytes, assess_fundus_and_quality, save_numpy_image
from app.schemas.prediction import (
    PredictionResponse,
    DiagnosisInfo,
    ReferableRiskInfo,
    ExplainabilityInfo,
    QualityInfo,
    ModelMetadata
)

class PredictionService:
    """
    Central orchestration point for the DR screening pipeline.
    Order:
      1. File validation
      2. Image decoding
      3. Fundus validation gate (multi-signal)
      4. Technical quality checks
      5. Preprocessing (preprocess_fundus)
      6. EfficientNet-B3 inference
      7. Referable DR threshold logic (0.13)
      8. Grad-CAM explainability
      9. History persistence (valid and non-prediction outcomes)
      10. Server-side temporary file cleanup
    """
    def __init__(self):
        settings.absolute_results_dir.mkdir(parents=True, exist_ok=True)
        settings.absolute_upload_dir.mkdir(parents=True, exist_ok=True)

    async def process_screening(
        self,
        file: UploadFile,
        target_class_override: Optional[int] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Processes an uploaded fundus image.
        Returns: (http_status_code, response_dict_or_model)
        """
        start_time = time.time()
        screening_id = generate_unique_id()
        temp_saved_path: Optional[Path] = None

        try:
            # 1. File Validation
            if not file.filename:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded file must have a valid filename."
                )
            
            safe_filename = sanitize_filename(file.filename)
            ext = f".{safe_filename.split('.')[-1].lower()}" if "." in safe_filename else ""
            if ext not in settings.allowed_extension_list:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(settings.allowed_extension_list)}"
                )

            contents = await file.read()
            if not contents or len(contents) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The uploaded image file is empty (0 bytes)."
                )

            max_bytes = settings.effective_max_upload_mb * 1024 * 1024
            if len(contents) > max_bytes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File exceeds maximum allowed size of {settings.effective_max_upload_mb}MB."
                )

            # Save temporary file for server-side traceability
            temp_saved_path = settings.absolute_upload_dir / f"{screening_id}_{safe_filename}"
            with open(temp_saved_path, "wb") as f:
                f.write(contents)

            # 2. Image Decoding
            try:
                pil_image = load_image_bytes(contents)
            except Exception as e:
                logger.warning(f"Corrupt image upload rejected: {e}")
                rejection = {
                    "screening_id": screening_id,
                    "status": "INVALID_IMAGE",
                    "quality": {
                        "status": "INVALID",
                        "reasons": ["Uploaded image file is corrupted or unreadable."]
                    },
                    "created_at": datetime.utcnow().isoformat()
                }
                history_service.save({
                    "screening_id": screening_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "filename": safe_filename,
                    "status": "INVALID_IMAGE",
                    "quality": rejection["quality"]
                })
                return 422, rejection

            # 3. Fundus Validation Gate & Quality Assessment
            quality_result = assess_fundus_and_quality(pil_image)
            
            # If rejected as non-retinal or fundamentally invalid
            if quality_result.status == "INVALID":
                logger.info(f"Non-retinal or invalid image rejected: {quality_result.reasons}")
                rejection = {
                    "screening_id": screening_id,
                    "status": "INVALID_IMAGE",
                    "quality": {
                        "status": "INVALID",
                        "reasons": quality_result.reasons,
                        "width": quality_result.width,
                        "height": quality_result.height,
                        "brightness": quality_result.brightness,
                        "contrast": quality_result.contrast,
                        "blur_score": quality_result.blur_score
                    },
                    "created_at": datetime.utcnow().isoformat()
                }
                history_service.save({
                    "screening_id": screening_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "filename": safe_filename,
                    "status": "INVALID_IMAGE",
                    "quality": rejection["quality"]
                })
                return 422, rejection

            # If rejected as low quality (e.g. excessively blurry, dark)
            if quality_result.status == "LOW_QUALITY":
                logger.info(f"Low quality fundus rejected: {quality_result.reasons}")
                rejection = {
                    "screening_id": screening_id,
                    "status": "LOW_QUALITY",
                    "quality": {
                        "status": "LOW_QUALITY",
                        "reasons": quality_result.reasons,
                        "width": quality_result.width,
                        "height": quality_result.height,
                        "brightness": quality_result.brightness,
                        "contrast": quality_result.contrast,
                        "blur_score": quality_result.blur_score
                    },
                    "created_at": datetime.utcnow().isoformat()
                }
                history_service.save({
                    "screening_id": screening_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "filename": safe_filename,
                    "status": "LOW_QUALITY",
                    "quality": rejection["quality"]
                })
                return 422, rejection

            # 4. Existing Working Preprocessing Pipeline
            try:
                input_tensor, preprocessed_rgb_380 = preprocess_fundus(pil_image)
            except Exception as e:
                logger.error(f"Preprocessing error: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "screening_id": screening_id,
                        "status": "MODEL_ERROR",
                        "detail": f"Error during fundus preprocessing: {str(e)}"
                    }
                )

            # 5. Existing EfficientNet-B3 Model Inference
            try:
                model = model_manager.get_model()
                device = model_manager.device
                inference_result = run_inference(model, input_tensor, device)
            except Exception as e:
                logger.error(f"Inference execution error: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "screening_id": screening_id,
                        "status": "MODEL_ERROR",
                        "detail": f"Model inference execution failed: {str(e)}"
                    }
                )

            predicted_class_id = inference_result["class_id"]
            confidence = round(float(inference_result["confidence"]), 4)
            referable_prob = round(float(inference_result["referable_probability"]), 4)
            threshold = float(settings.REFERABLE_THRESHOLD)
            referable_status = "REFERABLE" if referable_prob >= threshold else "NON_REFERABLE"
            is_referable = bool(referable_status == "REFERABLE")

            # Map probabilities to standardized keys (both snake_case and label names for compatibility)
            class_key_map = {
                0: "no_dr",
                1: "mild_dr",
                2: "moderate_dr",
                3: "severe_dr",
                4: "proliferative_dr"
            }
            raw_probs = inference_result["raw_probabilities"]
            formatted_probs = {
                class_key_map[i]: round(float(raw_probs[i]), 4)
                for i in range(5)
            }
            # Add label name keys for frontend chart compatibility
            for i in range(5):
                formatted_probs[settings.CLASS_MAPPING[i]] = round(float(raw_probs[i]), 4)

            # 6. Grad-CAM Explainability (same model and forward pass)
            target_explain_class = target_class_override if target_class_override is not None else predicted_class_id
            original_filename = f"original_{screening_id}.jpg"
            heatmap_filename = f"heatmap_{screening_id}.jpg"
            overlay_filename = f"overlay_{screening_id}.jpg"

            original_path = settings.absolute_results_dir / original_filename
            heatmap_path = settings.absolute_results_dir / heatmap_filename
            overlay_path = settings.absolute_results_dir / overlay_filename

            gradcam_available = False
            try:
                # Save preprocessed fundus
                save_numpy_image(preprocessed_rgb_380, original_path)

                gradcam = GradCAM(model, model_manager.get_gradcam_layer())
                colored_heatmap_rgb, overlay_rgb, _ = gradcam.generate_visualizations(
                    input_tensor=input_tensor.to(device),
                    original_rgb_380=preprocessed_rgb_380,
                    target_class=target_explain_class,
                    alpha=0.45
                )
                gradcam.remove_hooks()

                save_numpy_image(colored_heatmap_rgb, heatmap_path)
                save_numpy_image(overlay_rgb, overlay_path)
                gradcam_available = True
            except Exception as e:
                logger.error(f"Grad-CAM generation error: {e}")

            original_url = f"/storage/results/{original_filename}"
            heatmap_url = f"/storage/results/{heatmap_filename}"
            overlay_url = f"/storage/results/{overlay_filename}"

            # 7. Clinical Explanation & Recommendation
            explanation_text, recommendation_text = generate_explanation(
                class_id=predicted_class_id,
                is_referable=is_referable,
                confidence=confidence
            )

            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            timestamp_now = datetime.utcnow().isoformat()

            # 8. Build Structured Prediction Response
            response = PredictionResponse(
                screening_id=screening_id,
                status="VALID",
                diagnosis=DiagnosisInfo(
                    class_id=predicted_class_id,
                    label=settings.CLASS_MAPPING[predicted_class_id],
                    confidence=confidence
                ),
                probabilities=formatted_probs,
                referable=ReferableRiskInfo(
                    probability=referable_prob,
                    threshold=threshold,
                    status=referable_status
                ),
                quality=QualityInfo(
                    status="ACCEPT",
                    reasons=[],
                    width=quality_result.width,
                    height=quality_result.height,
                    brightness=quality_result.brightness,
                    contrast=quality_result.contrast,
                    blur_score=quality_result.blur_score
                ),
                explainability=ExplainabilityInfo(
                    available=gradcam_available,
                    overlay_url=overlay_url,
                    heatmap_url=heatmap_url,
                    original_url=original_url
                ),
                model=ModelMetadata(
                    name="EfficientNet-B3",
                    version=settings.MODEL_VERSION
                ),
                created_at=timestamp_now,
                # Backward-compatibility fields
                id=screening_id,
                success=True,
                filename=safe_filename,
                prediction=DiagnosisInfo(
                    class_id=predicted_class_id,
                    label=settings.CLASS_MAPPING[predicted_class_id],
                    confidence=confidence
                ),
                explanation_text=explanation_text,
                referral_recommendation=recommendation_text,
                inference_time_ms=elapsed_ms
            )

            # 9. Persist Result to History
            history_service.save({
                "screening_id": screening_id,
                "timestamp": timestamp_now,
                "filename": safe_filename,
                "status": "VALID",
                "model_version": settings.MODEL_VERSION,
                "predicted_class": predicted_class_id,
                "predicted_class_name": settings.CLASS_MAPPING[predicted_class_id],
                "confidence": confidence,
                "referable_probability": referable_prob,
                "is_referable": is_referable,
                "probabilities": formatted_probs,
                "quality": {
                    "status": "ACCEPT",
                    "reasons": [],
                    "blur_score": quality_result.blur_score,
                    "brightness": quality_result.brightness,
                    "contrast": quality_result.contrast
                },
                "heatmap_url": heatmap_url,
                "overlay_url": overlay_url,
                "original_url": original_url
            })

            return status.HTTP_200_OK, response.model_dump(mode="json")

        finally:
            # 10. Clean up temporary uploaded file
            cleanup_file(temp_saved_path)

prediction_service = PredictionService()

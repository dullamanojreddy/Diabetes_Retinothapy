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
from app.ml.enhancement import fundus_enhancer
from app.ml.calibration import temperature_scaler
from app.retina import analyze_retinal_structure, analyze_lesions
from app.services.timing_service import PipelineTimer
import numpy as np
from app.services.history_service import history_service
from app.services.quality_service import quality_service
from app.utils.file_utils import generate_unique_id, cleanup_file, sanitize_filename
from app.utils.image_utils import load_image_bytes, assess_fundus_and_quality, save_numpy_image
from app.schemas.prediction import (
    PredictionResponse,
    DiagnosisInfo,
    ReferableRiskInfo,
    ExplainabilityInfo,
    QualityInfo,
    CalibrationInfo,
    TimingInfo,
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
        timer = PipelineTimer()

        try:
            # 1. File Validation
            with timer.track("file_validation"):
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
                        "blur_score": quality_result.blur_score,
                        "signals": quality_result.signals.to_dict() if quality_result.signals else None
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

            # 4. Phase 3 Complete Image-Quality Assessment
            img_np = np.array(pil_image)
            quality_assessment = quality_service.assess(
                img_np,
                fov_gate_score=quality_result.signals.fov_score if quality_result.signals else 1.0
            )

            # If rejected as low quality or ungradeable
            if quality_result.status == "LOW_QUALITY" or quality_assessment.status == "UNGRADEABLE":
                combined_reasons = list(dict.fromkeys(quality_result.reasons + quality_assessment.reasons))
                logger.info(f"Low quality or ungradeable fundus rejected: {combined_reasons}")
                rejection = {
                    "screening_id": screening_id,
                    "status": "LOW_QUALITY",
                    "quality": {
                        "status": "LOW_QUALITY",
                        "grade": quality_assessment.grade,
                        "score": quality_assessment.score,
                        "reasons": combined_reasons,
                        "recapture_guidance": quality_assessment.recapture_guidance,
                        "focus": quality_assessment.focus.to_dict(),
                        "illumination": quality_assessment.illumination.to_dict(),
                        "contrast_detail": quality_assessment.contrast.to_dict(),
                        "field_of_view": quality_assessment.field_of_view.to_dict(),
                        "glare": quality_assessment.glare.to_dict(),
                        "width": quality_result.width,
                        "height": quality_result.height,
                        "brightness": quality_result.brightness,
                        "contrast": quality_result.contrast,
                        "blur_score": quality_result.blur_score,
                        "signals": quality_result.signals.to_dict() if quality_result.signals else None
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

            # Phase 4: Borderline Fundus Enhancement and Safety Verification
            enhancement_result = fundus_enhancer.enhance(img_np, quality_assessment)
            if enhancement_result.applied and enhancement_result.accepted:
                logger.info(f"Phase 4 enhancement accepted for borderline fundus: {enhancement_result.reasons}")
                model_pil_image = Image.fromarray(enhancement_result.image_rgb)
            else:
                model_pil_image = pil_image

            # 4. Existing Working Preprocessing Pipeline
            try:
                with timer.track("preprocessing"):
                    input_tensor, preprocessed_rgb_380 = preprocess_fundus(model_pil_image)
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
                with timer.track("inference"):
                    model = model_manager.get_model()
                    device = model_manager.device
                    inference_result = run_inference(model, input_tensor, device)
                    timer.record_inference_executed()
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

            # Phase 5: Retinal Structure Analysis (optic disc, fovea, vessels)
            try:
                with timer.track("retinal_structures"):
                    structures_result, vessel_mask, skeleton_mask = analyze_retinal_structure(img_np)
                    structures_dict = structures_result.to_dict()
            except Exception as e:
                logger.warning(f"Retinal structure analysis error: {e}")
                structures_dict = {"status": "UNAVAILABLE", "error": str(e)}
                vessel_mask, skeleton_mask = None, None

            # Phase 6: Lesion Candidate Analysis (microaneurysms, exudates, hemorrhages, neovascularization)
            try:
                with timer.track("lesion_analysis"):
                    lesions_result = analyze_lesions(
                        img_np,
                        structures=structures_result if 'structures_result' in locals() else None,
                        vessel_mask=vessel_mask,
                        skeleton_mask=skeleton_mask
                    )
                    lesions_dict = lesions_result.to_dict()
            except Exception as e:
                logger.warning(f"Lesion candidate analysis error: {e}")
                lesions_dict = {"research_only": True, "status": "UNAVAILABLE", "error": str(e)}

            # Phase 7: Post-Hoc Confidence Calibration (Temperature Scaling)
            try:
                with timer.track("calibration"):
                    cal_res = temperature_scaler.calibrate_probabilities(
                        {settings.CLASS_MAPPING[i]: float(raw_probs[i]) for i in range(5)}
                    )
                    calibration_info = CalibrationInfo(
                        temperature=cal_res.temperature,
                        is_calibrated=cal_res.is_calibrated,
                        calibrated_confidence=cal_res.calibrated_confidence,
                        uncalibrated_confidence=cal_res.uncalibrated_confidence,
                        uncalibrated_probabilities=cal_res.uncalibrated_probabilities,
                        calibrated_probabilities=cal_res.calibrated_probabilities,
                        metrics=cal_res.metrics
                    )
                    calibration_dict = cal_res.to_dict()
            except Exception as e:
                logger.warning(f"Confidence calibration error: {e}")
                calibration_info = None
                calibration_dict = None

            timing_summary = timer.get_summary()
            timing_info = TimingInfo(
                total_pipeline_ms=timing_summary["total_pipeline_ms"],
                inference_ms=timing_summary["inference_ms"],
                is_warmup=timing_summary["is_warmup"],
                stages_ms=timing_summary["stages_ms"]
            )
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
                    grade=quality_assessment.grade,
                    score=enhancement_result.enhanced_quality_score if (enhancement_result.applied and enhancement_result.accepted) else quality_assessment.score,
                    reasons=quality_assessment.reasons,
                    recapture_guidance=quality_assessment.recapture_guidance,
                    focus=quality_assessment.focus.to_dict(),
                    illumination=quality_assessment.illumination.to_dict(),
                    contrast_detail=quality_assessment.contrast.to_dict(),
                    field_of_view=quality_assessment.field_of_view.to_dict(),
                    glare=quality_assessment.glare.to_dict(),
                    width=quality_result.width,
                    height=quality_result.height,
                    brightness=quality_result.brightness,
                    contrast=quality_result.contrast,
                    blur_score=quality_result.blur_score,
                    signals=quality_result.signals.to_dict() if quality_result.signals else None,
                    enhancement_applied=enhancement_result.applied,
                    enhancement_accepted=enhancement_result.accepted,
                    enhancement_method=enhancement_result.method,
                    enhancement_details=enhancement_result.to_dict()
                ),
                explainability=ExplainabilityInfo(
                    available=gradcam_available,
                    overlay_url=overlay_url,
                    heatmap_url=heatmap_url,
                    original_url=original_url
                ),
                structures=structures_dict,
                lesions=lesions_dict,
                calibration=calibration_info,
                timing=timing_info,
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
                inference_time_ms=timing_summary["total_pipeline_ms"]
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
                "original_url": original_url,
                "structures": structures_dict,
                "lesions": lesions_dict,
                "calibration": calibration_dict,
                "timing": timing_summary
            })

            return status.HTTP_200_OK, response.model_dump(mode="json")

        finally:
            # 10. Clean up temporary uploaded file
            cleanup_file(temp_saved_path)

prediction_service = PredictionService()

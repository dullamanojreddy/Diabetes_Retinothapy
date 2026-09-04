import io
import cv2
import numpy as np
import pytest
from PIL import Image
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings
from app.services.quality_service import quality_service, QualityAssessment
from tests.test_prediction import get_valid_fundus_bytes, create_low_quality_blurry_fundus_bytes

@pytest.fixture
def valid_fundus_image():
    raw = get_valid_fundus_bytes()
    return np.array(Image.open(io.BytesIO(raw)).convert("RGB"))

def test_quality_assessment_good_fundus(valid_fundus_image):
    """
    Verifies that a known clear, properly illuminated fundus image evaluates to GOOD.
    """
    assessment = quality_service.assess(valid_fundus_image)
    assert isinstance(assessment, QualityAssessment)
    assert assessment.status == "GOOD"
    assert assessment.grade == "GOOD"
    assert assessment.score >= 0.70
    assert assessment.focus.status == "GOOD"
    assert assessment.illumination.status == "GOOD"
    assert assessment.contrast.status == "GOOD"
    assert assessment.field_of_view.status == "GOOD"
    assert assessment.glare.status == "GOOD"
    assert len(assessment.reasons) == 0

def test_quality_assessment_blurry_fundus_ungradeable(valid_fundus_image):
    """
    Verifies that an out-of-focus / severely blurred fundus is flagged as UNGRADEABLE
    with actionable focus stabilization guidance.
    """
    blurry_np = cv2.GaussianBlur(valid_fundus_image, (51, 51), 30)
    assessment = quality_service.assess(blurry_np)
    
    assert assessment.status == "UNGRADEABLE"
    assert assessment.grade == "POOR"
    assert assessment.focus.status == "POOR"
    assert any("blur" in r.lower() or "focus" in r.lower() for r in assessment.reasons)
    assert any("chin rest" in g.lower() or "autofocus" in g.lower() for g in assessment.recapture_guidance)

def test_quality_assessment_dark_fundus_ungradeable(valid_fundus_image):
    """
    Verifies that a severely underexposed fundus evaluates to UNGRADEABLE with illumination guidance.
    """
    dark_np = np.clip(valid_fundus_image.astype(np.int16) - 130, 0, 255).astype(np.uint8)
    assessment = quality_service.assess(dark_np)
    
    assert assessment.status == "UNGRADEABLE"
    assert assessment.grade == "POOR"
    assert assessment.illumination.status == "POOR"
    assert any("underexposed" in r.lower() or "dark" in r.lower() for r in assessment.reasons)
    assert any("increase flash" in g.lower() or "illumination" in g.lower() for g in assessment.recapture_guidance)

def test_quality_assessment_overexposed_fundus(valid_fundus_image):
    """
    Verifies that an overexposed / washed out fundus is flagged with glare/illumination warnings.
    """
    bright_np = np.clip(valid_fundus_image.astype(np.int16) + 140, 0, 255).astype(np.uint8)
    assessment = quality_service.assess(bright_np)
    
    assert assessment.status in ("BORDERLINE", "UNGRADEABLE")
    assert assessment.illumination.status in ("BORDERLINE", "POOR")
    assert any("decrease" in g.lower() or "glare" in g.lower() or "illumination" in g.lower() for g in assessment.recapture_guidance)

def test_quality_assessment_borderline_fundus(valid_fundus_image):
    """
    Verifies that mild, recoverable degradation evaluates to BORDERLINE (eligible for Phase 4 enhancement).
    """
    # Mild Gaussian blur with subtle focus degradation into BORDERLINE territory (10 <= laplacian < 30)
    mild_blur = cv2.GaussianBlur(valid_fundus_image, (5, 5), 1.0)
    assessment = quality_service.assess(mild_blur)
    
    assert assessment.status == "BORDERLINE"
    assert assessment.grade == "ACCEPTABLE"
    assert assessment.focus.status == "BORDERLINE"
    assert len(assessment.recapture_guidance) > 0

@pytest.mark.asyncio
async def test_quality_assessment_zero_inference_on_ungradeable():
    """
    Acceptance Criterion:
    UNGRADEABLE retinal fundus
    -> QUALITY SERVICE REJECT
    -> HTTP 422 LOW_QUALITY
    -> ZERO MODEL INFERENCE (call_count == 0)
    -> ZERO PREPROCESSING (call_count == 0)
    -> ZERO GRAD-CAM (call_count == 0)
    """
    blurry_bytes = create_low_quality_blurry_fundus_bytes()

    with patch("app.services.prediction_service.run_inference") as mock_inference, \
         patch("app.services.prediction_service.preprocess_fundus") as mock_preprocess, \
         patch("app.services.prediction_service.GradCAM") as mock_gradcam, \
         patch("app.services.prediction_service.generate_explanation") as mock_explain:

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/prediction",
                files={"file": ("blurry_fundus.jpg", blurry_bytes, "image/jpeg")}
            )

        assert response.status_code == 422
        data = response.json()

        # Strict zero-inference assertions
        assert mock_inference.call_count == 0
        assert mock_preprocess.call_count == 0
        assert mock_gradcam.call_count == 0
        assert mock_explain.call_count == 0

        # Structured response verification
        assert data["status"] == "LOW_QUALITY"
        assert "quality" in data
        assert "recapture_guidance" in data["quality"]
        assert len(data["quality"]["recapture_guidance"]) > 0
        assert "focus" in data["quality"]
        assert "illumination" in data["quality"]
        assert "diagnosis" not in data or data["diagnosis"] is None

def test_quality_service_isolation():
    """
    Confirms QualityService runs locally without deep learning models or external APIs.
    """
    import app.services.quality_service as qs_module
    
    # Must not import torch, model_manager, or gradcam
    assert not hasattr(qs_module, "torch")
    assert not hasattr(qs_module, "model_manager")
    assert not hasattr(qs_module, "GradCAM")
    assert not hasattr(qs_module, "run_inference")

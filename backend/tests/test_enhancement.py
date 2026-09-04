import io
import cv2
import numpy as np
import pytest
from PIL import Image
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings
from app.ml.enhancement import fundus_enhancer, FundusEnhancer, EnhancementResult
from app.services.quality_service import quality_service
from tests.test_prediction import get_valid_fundus_bytes, create_low_quality_blurry_fundus_bytes

@pytest.fixture
def valid_fundus_rgb():
    raw = get_valid_fundus_bytes()
    return np.array(Image.open(io.BytesIO(raw)).convert("RGB"))

@pytest.fixture
def borderline_fundus_rgb(valid_fundus_rgb):
    # Mild focus blur placing image into BORDERLINE quality territory (10 <= laplacian < 30)
    return cv2.GaussianBlur(valid_fundus_rgb, (5, 5), 1.0)

def test_enhancement_bypasses_good_fundus(valid_fundus_rgb):
    """
    Test 1: A GOOD quality fundus image must bypass enhancement completely.
    """
    quality = quality_service.assess(valid_fundus_rgb)
    assert quality.status == "GOOD"
    
    res = fundus_enhancer.enhance(valid_fundus_rgb, quality)
    assert isinstance(res, EnhancementResult)
    assert res.applied is False
    assert res.accepted is False
    assert "BYPASS_NON_BORDERLINE" in res.method
    assert res.original_image_preserved is True
    assert np.array_equal(res.image_rgb, valid_fundus_rgb)

def test_enhancement_activates_on_borderline_fundus(borderline_fundus_rgb):
    """
    Test 2: A BORDERLINE fundus image enters enhancement, improves quality, and is accepted.
    """
    quality = quality_service.assess(borderline_fundus_rgb)
    assert quality.status == "BORDERLINE"
    
    res = fundus_enhancer.enhance(borderline_fundus_rgb, quality)
    assert res.applied is True
    assert res.accepted is True
    assert "LAB_CLAHE" in res.method
    assert res.enhanced_quality_score >= res.original_quality_score
    assert len(res.operations) > 0
    assert "lab_clahe" in res.operations[0]

def test_enhancement_bypasses_ungradeable_fundus(valid_fundus_rgb):
    """
    Test 3: An UNGRADEABLE fundus image must bypass enhancement.
    """
    ungradeable_rgb = cv2.GaussianBlur(valid_fundus_rgb, (51, 51), 30)
    quality = quality_service.assess(ungradeable_rgb)
    assert quality.status == "UNGRADEABLE"
    
    res = fundus_enhancer.enhance(ungradeable_rgb, quality)
    assert res.applied is False
    assert res.accepted is False
    assert np.array_equal(res.image_rgb, ungradeable_rgb)

def test_enhancement_preserves_original_image_array(borderline_fundus_rgb):
    """
    Test 4: Enhancement must never mutate the input image array in place.
    """
    original_copy = borderline_fundus_rgb.copy()
    quality = quality_service.assess(borderline_fundus_rgb)
    
    res = fundus_enhancer.enhance(borderline_fundus_rgb, quality)
    assert np.array_equal(borderline_fundus_rgb, original_copy), "Input array was mutated in place!"
    assert res.original_image_preserved is True

def test_enhancement_lab_dimensions_and_type(borderline_fundus_rgb):
    """
    Test 5: Enhanced output must maintain identical dimensions, uint8 data type, and RGB bounds.
    """
    quality = quality_service.assess(borderline_fundus_rgb)
    res = fundus_enhancer.enhance(borderline_fundus_rgb, quality)
    
    assert res.image_rgb.shape == borderline_fundus_rgb.shape
    assert res.image_rgb.dtype == np.uint8
    assert np.min(res.image_rgb) >= 0
    assert np.max(res.image_rgb) <= 255

def test_enhancement_clahe_parameters_conservative():
    """
    Test 6: Verifies that CLAHE parameters are conservative (clip limit <= 2.0, grid == 8x8).
    """
    enhancer = FundusEnhancer()
    assert enhancer.clahe_clip_limit <= 2.0
    assert enhancer.clahe_tile_grid == (8, 8)

def test_enhancement_safety_reversion_on_degradation(borderline_fundus_rgb):
    """
    Test 7 & 8: Safety verification reverts to the original image if enhancement candidate degrades quality.
    """
    enhancer = FundusEnhancer()
    quality = quality_service.assess(borderline_fundus_rgb)
    
    # Mock _verify_safety to simulate a safety violation
    with patch.object(enhancer, "_verify_safety", return_value=(False, ["Simulated safety degradation"])):
        res = enhancer.enhance(borderline_fundus_rgb, quality)
        assert res.applied is True
        assert res.accepted is False
        assert "REVERTED" in res.method
        assert any("safety" in r.lower() for r in res.reasons)
        assert np.array_equal(res.image_rgb, borderline_fundus_rgb)

@pytest.mark.asyncio
async def test_enhancement_api_good_fundus_bypasses():
    """
    Test 9: End-to-end API test with GOOD fundus verifies enhancement is marked as not applied.
    """
    raw = get_valid_fundus_bytes()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/prediction",
            files={"file": ("good_fundus.jpg", raw, "image/jpeg")}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["quality"]["enhancement_applied"] is False
    assert data["diagnosis"] is not None

@pytest.mark.asyncio
async def test_enhancement_api_borderline_fundus_applied():
    """
    Test 10: End-to-end API test with BORDERLINE fundus verifies enhancement is executed and accepted.
    """
    raw = get_valid_fundus_bytes()
    img_np = np.array(Image.open(io.BytesIO(raw)).convert("RGB"))
    borderline_np = cv2.GaussianBlur(img_np, (5, 5), 1.0)
    buf = io.BytesIO()
    Image.fromarray(borderline_np).save(buf, format="JPEG", quality=95)
    borderline_bytes = buf.getvalue()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/prediction",
            files={"file": ("borderline_fundus.jpg", borderline_bytes, "image/jpeg")}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["quality"]["enhancement_applied"] is True
    assert data["quality"]["enhancement_accepted"] is True
    assert "LAB_CLAHE" in data["quality"]["enhancement_method"]
    assert data["diagnosis"] is not None
    assert data["referable"] is not None

@pytest.mark.asyncio
async def test_enhancement_api_ungradeable_fundus_zero_inference():
    """
    Test 11: UNGRADEABLE fundus halts at quality check; enhancement does not execute, inference == 0.
    """
    blurry_bytes = create_low_quality_blurry_fundus_bytes()

    with patch("app.services.prediction_service.run_inference") as mock_inference, \
         patch("app.services.prediction_service.preprocess_fundus") as mock_preprocess, \
         patch("app.services.prediction_service.GradCAM") as mock_gradcam, \
         patch("app.ml.enhancement.FundusEnhancer.enhance") as mock_enhance:

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/prediction",
                files={"file": ("blurry_fundus.jpg", blurry_bytes, "image/jpeg")}
            )

        assert response.status_code == 422
        assert mock_enhance.call_count == 0
        assert mock_inference.call_count == 0
        assert mock_preprocess.call_count == 0
        assert mock_gradcam.call_count == 0

@pytest.mark.asyncio
async def test_enhancement_adversarial_non_retinal_images_zero_enhancement():
    """
    Test 12: Adversarial non-retinal images (sun, plain orange, kettle) are rejected
    at Phase 2 fundus gate; enhancement is never invoked.
    """
    from tests.test_prediction import create_non_retinal_sun_bytes
    sun_bytes = create_non_retinal_sun_bytes()

    with patch("app.ml.enhancement.FundusEnhancer.enhance") as mock_enhance, \
         patch("app.services.prediction_service.run_inference") as mock_inference:

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/prediction",
                files={"file": ("sun.jpg", sun_bytes, "image/jpeg")}
            )

        assert response.status_code == 422
        data = response.json()
        assert data["status"] == "INVALID_IMAGE"
        assert mock_enhance.call_count == 0
        assert mock_inference.call_count == 0

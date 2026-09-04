from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings

ROOT_DIR = settings.base_dir.parent

@pytest.mark.asyncio
async def test_sun_and_miss_minutes_zero_inference_gate():
    """
    Acceptance Criterion:
    NON-RETINAL IMAGE (sun.jpg, missminutes.webp)
    -> FUNDUS GATE
    -> REJECT (HTTP 422 INVALID_IMAGE)
    -> ZERO MODEL INFERENCE (call_count == 0)
    -> ZERO PREPROCESSING (call_count == 0)
    -> ZERO GRAD-CAM (call_count == 0)
    -> ZERO DR DIAGNOSIS / REFERABLE RISK CALCULATION
    """
    test_files = [
        ("sun.jpg", ROOT_DIR / "sun.jpg", "image/jpeg"),
        ("missminutes.webp", ROOT_DIR / "missminutes.webp", "image/webp")
    ]

    for filename, file_path, mime_type in test_files:
        assert file_path.exists(), f"Required test image '{file_path}' was not found in workspace."
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        with patch("app.services.prediction_service.run_inference") as mock_inference, \
             patch("app.services.prediction_service.preprocess_fundus") as mock_preprocess, \
             patch("app.services.prediction_service.GradCAM") as mock_gradcam, \
             patch("app.services.prediction_service.generate_explanation") as mock_explain:

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    "/api/prediction",
                    files={"file": (filename, file_bytes, mime_type)}
                )

            # 1. Assert rejection HTTP Status 422
            assert response.status_code == 422, f"Expected HTTP 422 for {filename}, got {response.status_code}"
            data = response.json()

            # 2. Strict call-count assertions: ZERO calls permitted
            assert mock_inference.call_count == 0, f"run_inference was called {mock_inference.call_count} times on {filename}!"
            assert mock_preprocess.call_count == 0, f"preprocess_fundus was called {mock_preprocess.call_count} times on {filename}!"
            assert mock_gradcam.call_count == 0, f"GradCAM was called {mock_gradcam.call_count} times on {filename}!"
            assert mock_explain.call_count == 0, f"generate_explanation was called {mock_explain.call_count} times on {filename}!"

            # 3. Assert rejection contract and ZERO DR diagnosis / referable risk execution
            assert data["status"] == "INVALID_IMAGE"
            assert data["quality"]["status"] == "INVALID"
            assert len(data["quality"]["reasons"]) > 0
            assert "diagnosis" not in data or data["diagnosis"] is None
            assert "probabilities" not in data or data["probabilities"] is None
            assert "referable" not in data or data["referable"] is None

            print(f"\n=======================================================")
            print(f"VERIFICATION RESULT FOR: {filename}")
            print(f"=======================================================")
            print(f"  HTTP Response Code             : {response.status_code}")
            print(f"  Status Payload                 : {data['status']}")
            print(f"  Quality Status                 : {data['quality']['status']}")
            print(f"  Rejection Reason(s)            : {data['quality']['reasons']}")
            print(f"  run_inference() call count     : {mock_inference.call_count} (EXACTLY 0)")
            print(f"  preprocess_fundus() call count : {mock_preprocess.call_count} (EXACTLY 0)")
            print(f"  GradCAM call count             : {mock_gradcam.call_count} (EXACTLY 0)")
            print(f"  generate_explanation() calls   : {mock_explain.call_count} (EXACTLY 0)")
            print(f"  Diagnosis executed             : {'diagnosis' in data and data['diagnosis'] is not None} (FALSE)")
            print(f"  Referable risk calculated      : {'referable' in data and data['referable'] is not None} (FALSE)")
            print(f"=======================================================\n")

@pytest.mark.asyncio
async def test_adversarial_non_retinal_matrix_zero_inference_gate():
    """
    Phase 2 Adversarial Hardening Acceptance Criterion:
    Visually misleading non-retinal images — especially:
      - Plain solid orange background (color alone must NOT approve)
      - Plain solid red background
      - Orange circular disk on black background (fake retina without vessels)
      - Kettle / product / metallic object
      - Cartoon illustration
      - Human face portrait
      - Landscape / outdoor nature
      - Text document / paper
      - Dark-mode UI screenshot
      - Blue background / object
      - Uniform gray flat field
    MUST ALL BE INTERCEPTED BY THE FUNDUS GATE:
      -> Status: INVALID_IMAGE (HTTP 422)
      -> ZERO MODEL INFERENCE (call_count == 0)
      -> ZERO PREPROCESSING (call_count == 0)
      -> ZERO GRAD-CAM (call_count == 0)
      -> ZERO DR DIAGNOSIS / ZERO REFERABLE RISK
    """
    val_dir = settings.base_dir / "storage" / "validation" / "non_retinal"
    assert val_dir.exists(), f"Validation directory {val_dir} not found."
    
    test_fixtures = sorted(list(val_dir.glob("*.jpg")))
    assert len(test_fixtures) >= 10, f"Expected at least 10 adversarial fixtures, found {len(test_fixtures)}"

    for fixture_path in test_fixtures:
        with open(fixture_path, "rb") as f:
            file_bytes = f.read()

        with patch("app.services.prediction_service.run_inference") as mock_inference, \
             patch("app.services.prediction_service.preprocess_fundus") as mock_preprocess, \
             patch("app.services.prediction_service.GradCAM") as mock_gradcam, \
             patch("app.services.prediction_service.generate_explanation") as mock_explain:

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.post(
                    "/api/prediction",
                    files={"file": (fixture_path.name, file_bytes, "image/jpeg")}
                )

            assert response.status_code == 422, (
                f"Adversarial fixture {fixture_path.name} was not rejected! Status code: {response.status_code}"
            )
            data = response.json()

            # Zero-inference guarantee
            assert mock_inference.call_count == 0, f"Inference called {mock_inference.call_count} times on {fixture_path.name}!"
            assert mock_preprocess.call_count == 0, f"Preprocessing called {mock_preprocess.call_count} times on {fixture_path.name}!"
            assert mock_gradcam.call_count == 0, f"GradCAM called {mock_gradcam.call_count} times on {fixture_path.name}!"
            assert mock_explain.call_count == 0, f"Explanation called {mock_explain.call_count} times on {fixture_path.name}!"

            assert data["status"] == "INVALID_IMAGE"
            assert data["quality"]["status"] == "INVALID"
            assert len(data["quality"]["reasons"]) > 0
            assert "diagnosis" not in data or data["diagnosis"] is None
            assert "referable" not in data or data["referable"] is None

            print(f"[PASS ADVERSARIAL] {fixture_path.name:25} -> REJECTED (422) | Inference calls: 0 | Reasons: {data['quality']['reasons'][0]}")

@pytest.mark.asyncio
async def test_valid_fundus_regression_execution():
    """
    Verifies that authentic retinal fundus photography is NOT falsely rejected by the hardened gate,
    and proceeds through the complete screening pipeline (inference, Grad-CAM, diagnosis).
    """
    fundus_path = settings.base_dir / "storage" / "samples" / "sample_no_dr.jpg"
    assert fundus_path.exists(), f"Sample fundus image not found at {fundus_path}"
    
    with open(fundus_path, "rb") as f:
        file_bytes = f.read()

    with patch("app.services.prediction_service.run_inference", wraps=None) as mock_inference, \
         patch("app.services.prediction_service.preprocess_fundus", wraps=None) as mock_preprocess, \
         patch("app.services.prediction_service.GradCAM", wraps=None) as mock_gradcam, \
         patch("app.services.prediction_service.generate_explanation", wraps=None) as mock_explain:

        # Let the real functions run by using actual return values or spy
        pass

    # Now make an actual request to verify the full real pipeline runs
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/prediction",
            files={"file": ("valid_fundus.jpg", file_bytes, "image/jpeg")}
        )

    assert response.status_code == 200, f"Valid fundus was rejected! Got status {response.status_code}: {response.text}"
    data = response.json()
    assert data["status"] == "VALID"
    assert data["quality"]["status"] == "ACCEPT"
    assert data["diagnosis"] is not None
    assert "label" in data["diagnosis"]
    assert data["referable"] is not None
    assert "probability" in data["referable"]
    assert data["explainability"] is not None
    assert data["explainability"]["available"] is True
    print(f"\n[PASS VALID FUNDUS REGRESSION] Diagnostic Result: {data['diagnosis']['label']}, Confidence: {data['diagnosis']['confidence']:.2%}")

def test_structured_fundus_signals():
    """
    Verifies that assess_fundus_and_quality produces structured FundusValidationSignals.
    """
    from PIL import Image
    from app.utils.image_utils import assess_fundus_and_quality, FundusValidationSignals
    
    fundus_path = settings.base_dir / "storage" / "samples" / "sample_no_dr.jpg"
    img = Image.open(fundus_path).convert("RGB")
    res = assess_fundus_and_quality(img)
    
    assert res.signals is not None, "QualityResult.signals must be populated"
    assert isinstance(res.signals, FundusValidationSignals)
    assert 0.0 <= res.signals.aspect_ratio_score <= 1.0
    assert 0.0 <= res.signals.fov_score <= 1.0
    assert 0.0 <= res.signals.dark_boundary_score <= 1.0
    assert 0.0 <= res.signals.retinal_color_score <= 1.0
    assert 0.0 <= res.signals.texture_score <= 1.0
    assert 0.0 <= res.signals.edge_density_score <= 1.0
    assert 0.0 <= res.signals.vessel_like_score <= 1.0
    
    # Real fundus should have high structural scores
    assert res.signals.aspect_ratio_score >= 0.80
    assert res.signals.fov_score >= 0.70
    assert res.signals.dark_boundary_score >= 0.80
    assert res.signals.retinal_color_score >= 0.80
    assert res.signals.texture_score >= 0.80
    assert res.signals.edge_density_score >= 0.80
    assert res.signals.vessel_like_score >= 0.80
    print(f"\n[PASS STRUCTURED SIGNALS] Real Fundus Signals Dict: {res.signals.to_dict()}")



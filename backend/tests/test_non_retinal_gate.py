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



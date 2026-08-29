import io
import pytest
import numpy as np
from PIL import Image
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings

def create_test_fundus_bytes() -> bytes:
    img = Image.new("RGB", (300, 300), color=(180, 70, 30))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

@pytest.mark.asyncio
async def test_predict_endpoint_valid_image():
    img_bytes = create_test_fundus_bytes()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/predict",
            files={"file": ("test_fundus.jpg", img_bytes, "image/jpeg")}
        )
        
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "id" in data
    assert "prediction" in data
    assert 0 <= data["prediction"]["class_id"] <= 4
    assert data["prediction"]["class_name"] in settings.CLASS_MAPPING.values()
    assert 0.0 <= data["prediction"]["confidence"] <= 1.0
    
    # Verify probabilities
    probs = data["probabilities"]
    assert len(probs) == 5
    prob_sum = sum(probs.values())
    assert abs(prob_sum - 1.0) < 1e-3
    
    # Verify referable metrics
    assert "referable" in data
    assert data["referable"]["threshold"] == settings.REFERABLE_THRESHOLD
    expected_ref_prob = sum(probs[settings.CLASS_MAPPING[i]] for i in range(1, 5))
    assert abs(data["referable"]["probability"] - expected_ref_prob) < 1e-4
    assert data["referable"]["is_referable"] == (expected_ref_prob >= settings.REFERABLE_THRESHOLD)
    
    # Verify explainability URLs
    assert data["explainability"]["gradcam_available"] is True
    assert "heatmap_url" in data["explainability"]
    assert "overlay_url" in data["explainability"]

@pytest.mark.asyncio
async def test_predict_endpoint_rejects_invalid_format():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/predict",
            files={"file": ("test.pdf", b"%PDF-1.4...", "application/pdf")}
        )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]

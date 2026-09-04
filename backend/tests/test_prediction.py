import io
import os
from pathlib import Path
import pytest
import numpy as np
import cv2
from PIL import Image
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings
from app.schemas.prediction import PredictionResponse

def get_valid_fundus_bytes() -> bytes:
    sample_path = settings.base_dir / "storage" / "samples" / "sample_no_dr.jpg"
    if sample_path.exists():
        with open(sample_path, "rb") as f:
            return f.read()
            
    # Fallback: create realistic synthetic circular fundus image with dark background
    img = np.zeros((400, 400, 3), dtype=np.uint8)
    cv2.circle(img, (200, 200), 160, (160, 65, 20), -1)
    # Add retinal texture variation
    noise = np.random.randint(-15, 15, (400, 400, 3), dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    # Add optic disc and vessel-like line
    cv2.circle(img, (140, 200), 25, (220, 180, 80), -1)
    cv2.line(img, (140, 200), (280, 150), (90, 30, 10), 3)
    
    pil_img = Image.fromarray(img)
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()

def create_non_retinal_sun_bytes() -> bytes:
    # Blue sky with yellow sun (high blue reflectance, bright corners)
    img = np.zeros((400, 400, 3), dtype=np.uint8)
    img[:, :] = [100, 180, 255]  # Sky
    cv2.circle(img, (200, 200), 100, (255, 255, 0), -1)  # Yellow sun
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="JPEG")
    return buf.getvalue()

def create_non_retinal_cartoon_bytes() -> bytes:
    # White background with flat orange circle (Marvel/Miss Minutes cartoon character)
    img = np.ones((400, 400, 3), dtype=np.uint8) * 240
    cv2.circle(img, (200, 200), 120, (250, 130, 20), -1)
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="JPEG")
    return buf.getvalue()

def create_low_quality_blurry_fundus_bytes() -> bytes:
    # Retinal fundus heavily blurred (Gaussian blur kernel 51)
    raw = get_valid_fundus_bytes()
    pil_img = Image.open(io.BytesIO(raw))
    arr = np.array(pil_img)
    blurred = cv2.GaussianBlur(arr, (51, 51), 30)
    buf = io.BytesIO()
    Image.fromarray(blurred).save(buf, format="JPEG")
    return buf.getvalue()

# -------------------------------------------------------------------
# AT-01: Valid fundus image -> VALID, DR grade 0-4, probabilities, referable result
# -------------------------------------------------------------------
@pytest.mark.asyncio
async def test_at01_valid_fundus_image():
    img_bytes = get_valid_fundus_bytes()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/prediction",
            files={"file": ("fundus_screening.jpg", img_bytes, "image/jpeg")}
        )
        
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "VALID"
    assert "screening_id" in data
    assert "diagnosis" in data
    assert 0 <= data["diagnosis"]["class_id"] <= 4
    assert data["diagnosis"]["label"] in settings.CLASS_MAPPING.values()
    assert 0.0 <= data["diagnosis"]["confidence"] <= 1.0
    
    # Probabilities
    probs = data["probabilities"]
    assert "no_dr" in probs
    assert "proliferative_dr" in probs
    
    # Referable risk
    assert "referable" in data
    assert data["referable"]["threshold"] == settings.REFERABLE_THRESHOLD
    assert data["referable"]["status"] in ["REFERABLE", "NON_REFERABLE"]
    
    # Explainability artifact
    assert data["explainability"]["available"] is True
    assert "overlay_url" in data["explainability"]

# -------------------------------------------------------------------
# AT-02: Non-retinal image (Marvel/Sun) -> Rejected as INVALID_IMAGE
# -------------------------------------------------------------------
@pytest.mark.asyncio
async def test_at02_non_retinal_sun_image_rejected():
    sun_bytes = create_non_retinal_sun_bytes()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/prediction",
            files={"file": ("sun_sky.jpg", sun_bytes, "image/jpeg")}
        )
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "INVALID_IMAGE"
    assert data["quality"]["status"] == "INVALID"
    assert len(data["quality"]["reasons"]) > 0
    # Must NOT have diagnosis or probabilities
    assert "diagnosis" not in data or data["diagnosis"] is None

@pytest.mark.asyncio
async def test_at02_non_retinal_cartoon_rejected():
    cartoon_bytes = create_non_retinal_cartoon_bytes()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/prediction",
            files={"file": ("cartoon.jpg", cartoon_bytes, "image/jpeg")}
        )
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "INVALID_IMAGE"
    assert data["quality"]["status"] == "INVALID"

# -------------------------------------------------------------------
# AT-03: Corrupt PNG/JPG bytes -> 422 INVALID_IMAGE
# -------------------------------------------------------------------
@pytest.mark.asyncio
async def test_at03_corrupt_image_bytes():
    corrupt_bytes = b"CorruptedJFIFHeaderNotAValidImage1234567890"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/prediction",
            files={"file": ("corrupt.jpg", corrupt_bytes, "image/jpeg")}
        )
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "INVALID_IMAGE"
    assert data["quality"]["status"] == "INVALID"

# -------------------------------------------------------------------
# AT-04: Oversized / unsupported file -> rejected with HTTP 400
# -------------------------------------------------------------------
@pytest.mark.asyncio
async def test_at04_unsupported_file_extension():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/prediction",
            files={"file": ("test.pdf", b"%PDF-1.4...", "application/pdf")}
        )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]

@pytest.mark.asyncio
async def test_at04_empty_file():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/prediction",
            files={"file": ("empty.jpg", b"", "image/jpeg")}
        )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"]

# -------------------------------------------------------------------
# AT-05: Low-quality retinal image -> 422 LOW_QUALITY with no DR prediction
# -------------------------------------------------------------------
@pytest.mark.asyncio
async def test_at05_low_quality_blurry_fundus():
    blurry_bytes = create_low_quality_blurry_fundus_bytes()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/prediction",
            files={"file": ("blurry_fundus.jpg", blurry_bytes, "image/jpeg")}
        )
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "LOW_QUALITY"
    assert data["quality"]["status"] == "LOW_QUALITY"
    assert any("blur" in r.lower() for r in data["quality"]["reasons"])
    # Must NOT have diagnosis or probabilities
    assert "diagnosis" not in data or data["diagnosis"] is None

# -------------------------------------------------------------------
# AT-06: Grad-CAM overlay exists and corresponds to prediction
# -------------------------------------------------------------------
@pytest.mark.asyncio
async def test_at06_gradcam_overlay_generated():
    img_bytes = get_valid_fundus_bytes()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/prediction",
            files={"file": ("test_gradcam.jpg", img_bytes, "image/jpeg")}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["explainability"]["available"] is True
    overlay_url = data["explainability"]["overlay_url"]
    assert overlay_url is not None
    # Artifact file exists on disk
    artifact_path = settings.absolute_results_dir / Path(overlay_url).name
    assert artifact_path.exists()

# -------------------------------------------------------------------
# AT-07: History persistence and retrieval
# -------------------------------------------------------------------
@pytest.mark.asyncio
async def test_at07_history_retrieval():
    img_bytes = get_valid_fundus_bytes()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create a screening
        resp = await ac.post(
            "/api/prediction",
            files={"file": ("history_test.jpg", img_bytes, "image/jpeg")}
        )
        assert resp.status_code == 200
        sid = resp.json()["screening_id"]
        
        # Fetch history list
        hist_resp = await ac.get("/api/history")
        assert hist_resp.status_code == 200
        hist_data = hist_resp.json()
        assert hist_data["total"] >= 1
        
        # Fetch single record
        detail_resp = await ac.get(f"/api/history/{sid}")
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["screening_id"] == sid

# -------------------------------------------------------------------
# AT-08: Model readiness check
# -------------------------------------------------------------------
@pytest.mark.asyncio
async def test_at08_readiness_probe():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/health/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["model_loaded"] is True
        assert data["storage_available"] is True

# -------------------------------------------------------------------
# AT-10: UI/API alias and consistency test (/predict alias works)
# -------------------------------------------------------------------
@pytest.mark.asyncio
async def test_at10_predict_endpoint_alias():
    img_bytes = get_valid_fundus_bytes()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/predict",
            files={"file": ("alias_fundus.jpg", img_bytes, "image/jpeg")}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "prediction" in data
    assert "referable" in data

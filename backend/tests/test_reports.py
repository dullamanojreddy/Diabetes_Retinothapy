import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.report_service import report_service
from app.services.history_service import history_service
from tests.test_prediction import get_valid_fundus_bytes

@pytest.fixture
def sample_screening_record():
    return {
        "screening_id": "test-screening-12345",
        "timestamp": "2026-09-04T12:00:00.000Z",
        "filename": "fundus_left_eye.jpg",
        "status": "VALID",
        "model_version": "b3-aptos-epoch7",
        "predicted_class": 2,
        "predicted_class_name": "Moderate DR",
        "confidence": 0.8845,
        "referable_probability": 0.9215,
        "is_referable": True,
        "probabilities": {
            "No DR": 0.0210,
            "Mild": 0.0575,
            "Moderate": 0.8845,
            "Severe": 0.0250,
            "Proliferative": 0.0120
        },
        "quality": {
            "status": "ACCEPT",
            "grade": "GOOD",
            "reasons": [],
            "recapture_guidance": []
        },
        "structures": {
            "optic_disc": {"detected": True, "center_x": 450, "center_y": 250, "radius": 45.0, "confidence": 0.92},
            "fovea": {"detected": True, "center_x": 220, "center_y": 255},
            "vessels": {"detected": True, "vessel_coverage": 0.125, "branch_density": 0.025}
        },
        "lesions": {
            "research_only": True,
            "microaneurysms": {"candidate_count": 5, "heuristic_score": 0.65},
            "exudates": {"candidate_count": 2, "heuristic_score": 0.40},
            "hemorrhages": {"candidate_count": 3, "heuristic_score": 0.55},
            "neovascularization": {"indicator": "NOT_DETECTED", "heuristic_score": 0.10}
        },
        "calibration": {
            "temperature": 1.18,
            "is_calibrated": True,
            "calibrated_confidence": 0.8412,
            "uncalibrated_confidence": 0.8845
        },
        "heatmap_url": "/storage/results/heatmap_test.jpg",
        "overlay_url": "/storage/results/overlay_test.jpg",
        "original_url": "/storage/results/original_test.jpg"
    }

def test_report_service_renders_html_from_stored_record(sample_screening_record):
    """
    Verifies that generate_html_report outputs well-structured HTML containing core clinical elements.
    """
    html_output = report_service.generate_html_report(sample_screening_record)
    assert "<!DOCTYPE html>" in html_output
    assert "test-screening-12345" in html_output
    assert "Moderate DR" in html_output
    assert "REFERABLE DR" in html_output
    assert "Grad-CAM Heatmap" in html_output
    assert "Optic Disc" in html_output
    assert "Research Only" in html_output
    assert "MEDICAL &amp; REGULATORY NOTICE:" in html_output

def test_report_service_zero_inference_called(sample_screening_record):
    """
    Verifies that NO model inference is invoked during report generation.
    """
    with patch("app.ml.inference.run_inference") as mock_inference:
        report_service.generate_html_report(sample_screening_record)
        mock_inference.assert_not_called()

def test_report_service_escapes_dynamic_content():
    """
    Verifies that potentially malicious scripts or HTML tags in dynamic values are properly escaped.
    """
    xss_record = {
        "screening_id": "<script>alert('xss')</script>",
        "filename": "<img src=x onerror=alert('img')>",
        "status": "VALID",
        "predicted_class": 0,
        "predicted_class_name": "No DR <script>",
        "quality": {
            "reasons": ["<script>bad</script>"],
            "recapture_guidance": ["<svg onload=alert(1)>"]
        }
    }
    html_output = report_service.generate_html_report(xss_record)
    assert "<script>alert('xss')</script>" not in html_output
    assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in html_output
    assert "<img src=x onerror=alert('img')>" not in html_output
    assert "&lt;img src=x onerror=alert(&#x27;img&#x27;)&gt;" in html_output
    assert "<svg onload=alert(1)>" not in html_output

def test_report_service_handles_missing_optional_artifacts():
    """
    Verifies safe degradation when optional artifacts (structures, lesions, images) are missing or None.
    """
    minimal_record = {
        "screening_id": "minimal-001",
        "status": "VALID",
        "predicted_class": 1,
        "predicted_class_name": "Mild DR",
        "confidence": 0.65
    }
    html_output = report_service.generate_html_report(minimal_record)
    assert "<!DOCTYPE html>" in html_output
    assert "minimal-001" in html_output
    assert "Mild DR" in html_output
    assert "Artifact Not Available" in html_output
    assert "Not Localized" in html_output

@pytest.mark.asyncio
async def test_api_get_html_report_success():
    """
    Integration test: Performs a real screening, retrieves the generated report via GET /api/reports/{id}.
    """
    raw_img = get_valid_fundus_bytes()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Step 1: Create prediction
        pred_resp = await ac.post(
            "/api/prediction",
            files={"file": ("report_test.jpg", raw_img, "image/jpeg")}
        )
        assert pred_resp.status_code == 200
        screening_id = pred_resp.json()["screening_id"]

        # Step 2: Retrieve HTML report
        report_resp = await ac.get(f"/api/reports/{screening_id}")
        assert report_resp.status_code == 200
        assert "text/html" in report_resp.headers["content-type"]
        assert screening_id in report_resp.text
        assert "DIABETIC RETINOPATHY SCREENING AUDIT REPORT" in report_resp.text

@pytest.mark.asyncio
async def test_api_get_html_report_not_found():
    """
    Verifies that requesting a non-existent screening ID returns HTTP 404.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/reports/non-existent-uuid-99999")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

@pytest.mark.asyncio
async def test_api_get_json_report():
    """
    Integration test: Retrieves structured JSON report telemetry via GET /api/reports/{id}/json.
    """
    raw_img = get_valid_fundus_bytes()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        pred_resp = await ac.post(
            "/api/prediction",
            files={"file": ("report_json_test.jpg", raw_img, "image/jpeg")}
        )
        assert pred_resp.status_code == 200
        screening_id = pred_resp.json()["screening_id"]

        json_resp = await ac.get(f"/api/reports/{screening_id}/json")
        assert json_resp.status_code == 200
        data = json_resp.json()
        assert data["screening_id"] == screening_id
        assert "status" in data
        assert "predicted_class" in data

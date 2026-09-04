import io
import numpy as np
import pytest
from PIL import Image
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.retina import (
    detect_optic_disc,
    detect_fovea,
    segment_vessels,
    analyze_retinal_structure,
    StructureFinding,
    VesselFinding,
    RetinalStructureResult
)
from tests.test_prediction import get_valid_fundus_bytes

@pytest.fixture
def valid_fundus_np():
    raw = get_valid_fundus_bytes()
    return np.array(Image.open(io.BytesIO(raw)).convert("RGB"))

def test_detect_optic_disc(valid_fundus_np):
    """
    Verifies that optic disc candidate detection accurately returns coordinates and radius.
    """
    od = detect_optic_disc(valid_fundus_np)
    assert isinstance(od, StructureFinding)
    assert od.detected is True
    assert od.center_x is not None and 0 < od.center_x < valid_fundus_np.shape[1]
    assert od.center_y is not None and 0 < od.center_y < valid_fundus_np.shape[0]
    assert od.radius is not None and od.radius > 5.0
    assert 0.0 <= od.confidence <= 1.0
    assert od.bbox is not None and len(od.bbox) == 4

def test_detect_fovea(valid_fundus_np):
    """
    Verifies that fovea is estimated relative to the localized optic disc.
    """
    od = detect_optic_disc(valid_fundus_np)
    fovea = detect_fovea(valid_fundus_np, od)
    assert isinstance(fovea, StructureFinding)
    assert fovea.detected is True
    assert fovea.center_x is not None and 0 < fovea.center_x < valid_fundus_np.shape[1]
    assert fovea.center_y is not None and 0 < fovea.center_y < valid_fundus_np.shape[0]
    assert fovea.center_x != od.center_x

def test_detect_fovea_unavailable_without_optic_disc(valid_fundus_np):
    """
    Verifies safe UNAVAILABLE state when optic disc is not detected.
    """
    dummy_od = StructureFinding(detected=False, status="UNAVAILABLE")
    fovea = detect_fovea(valid_fundus_np, dummy_od)
    assert fovea.detected is False
    assert fovea.status == "UNAVAILABLE"

def test_segment_vessels(valid_fundus_np):
    """
    Verifies vessel segmentation yields valid binary masks, bounded coverage, and branch density.
    """
    vessels, v_mask, s_mask = segment_vessels(valid_fundus_np)
    assert isinstance(vessels, VesselFinding)
    assert vessels.detected is True
    assert 0.0 < vessels.vessel_coverage <= 1.0
    assert 0.0 <= vessels.branch_density <= 1.0
    assert v_mask.shape == valid_fundus_np.shape[:2]
    assert s_mask.shape == valid_fundus_np.shape[:2]
    assert np.count_nonzero(v_mask) > 0

def test_analyze_retinal_structure_orchestrator(valid_fundus_np):
    """
    Verifies that the orchestrator coordinates all three modules into RetinalStructureResult.
    """
    res, v_mask, s_mask = analyze_retinal_structure(valid_fundus_np)
    assert isinstance(res, RetinalStructureResult)
    assert res.status in ("AVAILABLE", "PARTIAL")
    assert res.optic_disc.detected is True
    assert res.fovea.detected is True
    assert res.vessels.detected is True
    assert "optic_disc" in res.to_dict()
    assert "fovea" in res.to_dict()
    assert "vessels" in res.to_dict()

def test_retinal_structures_failure_isolation():
    """
    Verifies that empty/invalid images yield safe UNAVAILABLE state without crashing.
    """
    empty_img = np.zeros((100, 100, 3), dtype=np.uint8)
    res, _, _ = analyze_retinal_structure(empty_img)
    assert res.status in ("UNAVAILABLE", "PARTIAL")

@pytest.mark.asyncio
async def test_retinal_structures_in_api_response():
    """
    Integration test: Verifies that POST /api/prediction response includes 'structures' telemetry.
    """
    raw = get_valid_fundus_bytes()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/prediction",
            files={"file": ("test_structures.jpg", raw, "image/jpeg")}
        )
    assert response.status_code == 200
    data = response.json()
    assert "structures" in data
    assert data["structures"] is not None
    assert "optic_disc" in data["structures"]
    assert "fovea" in data["structures"]
    assert "vessels" in data["structures"]
    assert data["structures"]["optic_disc"]["detected"] is True

import io
import numpy as np
import pytest
from PIL import Image
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.retina import (
    analyze_retinal_structure,
    detect_microaneurysms,
    detect_exudates,
    detect_hemorrhages,
    detect_neovascularization,
    analyze_lesions,
    CandidateFinding,
    LesionEvidence
)
from tests.test_prediction import get_valid_fundus_bytes

@pytest.fixture
def valid_fundus_np():
    raw = get_valid_fundus_bytes()
    return np.array(Image.open(io.BytesIO(raw)).convert("RGB"))

def test_detect_microaneurysms(valid_fundus_np):
    """
    Verifies microaneurysm candidate detection outputs bounded regions and candidate counts.
    """
    structures, v_mask, _ = analyze_retinal_structure(valid_fundus_np)
    ma = detect_microaneurysms(valid_fundus_np, v_mask, structures.optic_disc.bbox)
    
    assert isinstance(ma, CandidateFinding)
    assert ma.name == "microaneurysms"
    assert ma.candidate_count >= 0
    assert 0.0 <= ma.heuristic_score <= 1.0
    for r in ma.regions:
        assert len(r) == 4
        x, y, w, h = r
        assert 0 <= x < valid_fundus_np.shape[1]
        assert 0 <= y < valid_fundus_np.shape[0]

def test_detect_exudates(valid_fundus_np):
    """
    Verifies hard exudate candidate detection outputs bounded regions and candidate counts.
    """
    structures, _, _ = analyze_retinal_structure(valid_fundus_np)
    ex = detect_exudates(valid_fundus_np, structures.optic_disc.bbox)
    
    assert isinstance(ex, CandidateFinding)
    assert ex.name == "exudates"
    assert ex.candidate_count >= 0
    assert 0.0 <= ex.heuristic_score <= 1.0
    for r in ex.regions:
        assert len(r) == 4

def test_detect_hemorrhages(valid_fundus_np):
    """
    Verifies hemorrhage candidate detection outputs bounded regions and candidate counts.
    """
    structures, v_mask, _ = analyze_retinal_structure(valid_fundus_np)
    he = detect_hemorrhages(valid_fundus_np, v_mask, structures.optic_disc.bbox)
    
    assert isinstance(he, CandidateFinding)
    assert he.name == "hemorrhages"
    assert he.candidate_count >= 0
    assert 0.0 <= he.heuristic_score <= 1.0

def test_detect_neovascularization(valid_fundus_np):
    """
    Verifies neovascularization heuristic evaluates skeleton branching and tortuosity cues.
    """
    structures, v_mask, s_mask = analyze_retinal_structure(valid_fundus_np)
    nv = detect_neovascularization(valid_fundus_np, s_mask, v_mask)
    
    assert isinstance(nv, CandidateFinding)
    assert nv.name == "neovascularization"
    assert nv.indicator in ("NOT_DETECTED", "SUSPECTED", "UNDETERMINED")

def test_analyze_lesions_orchestrator(valid_fundus_np):
    """
    Verifies orchestrator aggregates all 4 lesion findings with research_only = True and disclaimer.
    """
    structures, v_mask, s_mask = analyze_retinal_structure(valid_fundus_np)
    evidence = analyze_lesions(valid_fundus_np, structures, v_mask, s_mask)
    
    assert isinstance(evidence, LesionEvidence)
    assert evidence.research_only is True
    assert "research" in evidence.disclaimer.lower()
    assert evidence.status in ("AVAILABLE", "PARTIAL")
    assert evidence.microaneurysms.name == "microaneurysms"
    assert evidence.exudates.name == "exudates"
    assert evidence.hemorrhages.name == "hemorrhages"
    assert evidence.neovascularization.name == "neovascularization"

def test_lesion_analysis_failure_isolation():
    """
    Verifies that empty/corrupted images yield safe UNAVAILABLE state without crashing.
    """
    empty_img = np.zeros((50, 50, 3), dtype=np.uint8)
    evidence = analyze_lesions(empty_img)
    assert evidence.research_only is True
    assert evidence.status in ("UNAVAILABLE", "PARTIAL")

@pytest.mark.asyncio
async def test_lesions_in_api_response():
    """
    Integration test: Verifies that POST /api/prediction returns 'lesions' marked research_only.
    """
    raw = get_valid_fundus_bytes()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/prediction",
            files={"file": ("test_lesions.jpg", raw, "image/jpeg")}
        )
    assert response.status_code == 200
    data = response.json()
    assert "lesions" in data
    assert data["lesions"] is not None
    assert data["lesions"]["research_only"] is True
    assert "microaneurysms" in data["lesions"]
    assert "exudates" in data["lesions"]
    assert "hemorrhages" in data["lesions"]
    assert "neovascularization" in data["lesions"]
    assert "disclaimer" in data["lesions"]

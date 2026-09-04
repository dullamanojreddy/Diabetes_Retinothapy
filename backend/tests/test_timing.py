import time
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.timing_service import PipelineTimer
from tests.test_prediction import get_valid_fundus_bytes

def test_pipeline_timer_tracks_stages():
    """
    Verifies that PipelineTimer records stages accurately with positive milliseconds.
    """
    timer = PipelineTimer()
    
    with timer.track("test_stage_a"):
        time.sleep(0.01)  # 10ms
        
    with timer.track("test_stage_b"):
        time.sleep(0.005) # 5ms
        
    summary = timer.get_summary()
    assert summary["total_pipeline_ms"] >= 15.0
    assert "test_stage_a" in summary["stages_ms"]
    assert "test_stage_b" in summary["stages_ms"]
    assert summary["stages_ms"]["test_stage_a"] >= 8.0
    assert summary["stages_ms"]["test_stage_b"] >= 3.0

def test_pipeline_timer_warmup_transition():
    """
    Verifies that recording inference transitions warmup state from cold to warm.
    """
    timer = PipelineTimer()
    timer.record_inference_executed()
    
    next_timer = PipelineTimer()
    summary = next_timer.get_summary()
    # Once an inference has occurred in process lifetime, subsequent timers are not cold start
    assert summary["is_warmup"] is False

@pytest.mark.asyncio
async def test_timing_in_api_response():
    """
    Integration test: Verifies that POST /api/prediction returns 'timing' telemetry for valid fundus.
    """
    raw_img = get_valid_fundus_bytes()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/prediction",
            files={"file": ("timing_test.jpg", raw_img, "image/jpeg")}
        )
    assert response.status_code == 200
    data = response.json()
    assert "timing" in data
    timing = data["timing"]
    assert timing is not None
    assert timing["total_pipeline_ms"] > 0.0
    assert timing["inference_ms"] >= 0.0
    assert "stages_ms" in timing
    assert "inference" in timing["stages_ms"]
    assert "preprocessing" in timing["stages_ms"]

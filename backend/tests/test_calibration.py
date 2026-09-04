import io
import numpy as np
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.ml.calibration import TemperatureScaler, compute_ece, CalibrationResult
from tests.test_prediction import get_valid_fundus_bytes

def test_temperature_scaling_unity():
    """
    Verifies that T = 1.0 leaves probabilities exactly unchanged.
    """
    scaler = TemperatureScaler()
    scaler.temperature = 1.0
    
    raw = {"No DR": 0.80, "Mild": 0.10, "Moderate": 0.05, "Severe": 0.03, "Proliferative": 0.02}
    res = scaler.calibrate_probabilities(raw)
    
    assert isinstance(res, CalibrationResult)
    assert res.is_calibrated is True
    assert res.temperature == 1.0
    for k in raw:
        assert pytest.approx(res.calibrated_probabilities[k], rel=1e-4) == raw[k]
    assert pytest.approx(res.calibrated_confidence, rel=1e-4) == 0.80

def test_temperature_scaling_smooths_overconfidence():
    """
    Verifies that T > 1.0 moderates peak overconfidence while strictly preserving the argmax class.
    """
    scaler = TemperatureScaler()
    scaler.temperature = 1.5
    
    raw = {"No DR": 0.95, "Mild": 0.02, "Moderate": 0.015, "Severe": 0.01, "Proliferative": 0.005}
    res = scaler.calibrate_probabilities(raw)
    
    # Peak confidence should decrease (overconfidence mitigated)
    assert res.calibrated_confidence < res.uncalibrated_confidence
    # Argmax class must remain "No DR"
    best_class = max(res.calibrated_probabilities, key=res.calibrated_probabilities.get)
    assert best_class == "No DR"
    # Probabilities must sum to 1.0
    assert pytest.approx(sum(res.calibrated_probabilities.values()), rel=1e-5) == 1.0

def test_temperature_scaling_preserves_normalization():
    """
    Verifies that calibrated probabilities sum to 1.0 across diverse arrays.
    """
    scaler = TemperatureScaler()
    scaler.temperature = 1.25
    
    random_probs = np.random.dirichlet(np.ones(5))
    res = scaler.calibrate_probabilities(random_probs)
    
    total = sum(res.calibrated_probabilities.values())
    assert pytest.approx(total, rel=1e-5) == 1.0

def test_ece_computation():
    """
    Verifies Expected Calibration Error (ECE) metric calculations.
    """
    # Perfectly calibrated case: 100% confident and 100% accurate
    perfect_probs = np.array([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 1.0]])
    perfect_labels = np.array([0, 0, 1, 1])
    ece_perfect = compute_ece(perfect_probs, perfect_labels, n_bins=5)
    assert pytest.approx(ece_perfect, abs=1e-5) == 0.0

    # Completely wrong overconfident case: 100% confident and 0% accurate
    wrong_probs = np.array([[1.0, 0.0], [1.0, 0.0]])
    wrong_labels = np.array([1, 1])
    ece_wrong = compute_ece(wrong_probs, wrong_labels, n_bins=5)
    assert ece_wrong > 0.5

def test_calibration_result_dictionary():
    """
    Verifies serialization of CalibrationResult.
    """
    scaler = TemperatureScaler()
    res = scaler.calibrate_probabilities({"ClassA": 0.7, "ClassB": 0.3})
    d = res.to_dict()
    assert "temperature" in d
    assert "calibrated_confidence" in d
    assert "uncalibrated_confidence" in d
    assert "calibrated_probabilities" in d
    assert "uncalibrated_probabilities" in d

@pytest.mark.asyncio
async def test_calibration_in_api_response():
    """
    Integration test: Verifies that POST /api/prediction returns 'calibration' telemetry for valid fundus.
    """
    raw_img = get_valid_fundus_bytes()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/prediction",
            files={"file": ("fundus.jpg", raw_img, "image/jpeg")}
        )
    assert response.status_code == 200
    data = response.json()
    assert "calibration" in data
    assert data["calibration"] is not None
    cal = data["calibration"]
    assert cal["is_calibrated"] is True
    assert cal["temperature"] > 0
    assert 0.0 <= cal["calibrated_confidence"] <= 1.0
    assert 0.0 <= cal["uncalibrated_confidence"] <= 1.0
    assert "calibrated_probabilities" in cal
    assert "uncalibrated_probabilities" in cal

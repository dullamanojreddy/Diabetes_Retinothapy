import pytest
import numpy as np
import torch
import torch.nn as nn
from unittest.mock import MagicMock

from app.core.config import settings
from app.ml.inference import run_inference

class MockLogitsModel(nn.Module):
    """
    Mock PyTorch model that returns pre-configured logits to test exact softmax distributions.
    """
    def __init__(self, logits: torch.Tensor):
        super().__init__()
        self.logits = logits

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.logits

def test_referable_probability_aggregation_level_2_plus():
    """
    Verifies that referable DR probability aggregation uses indices 2, 3, 4 only
    (Level 2+ clinical standard: Moderate, Severe, Proliferative DR),
    and does NOT include index 1 (Mild DR).
    """
    # Create logits that yield exact probabilities:
    # [0.10, 0.40, 0.20, 0.15, 0.15]
    # Class 0: 0.10
    # Class 1: 0.40
    # Class 2: 0.20
    # Class 3: 0.15
    # Class 4: 0.15
    #
    # Expected Level 2+ referable probability: 0.20 + 0.15 + 0.15 = 0.50
    # Under old logic (sum of 1..4), it would be 0.40 + 0.50 = 0.90
    probs = np.array([0.10, 0.40, 0.20, 0.15, 0.15], dtype=np.float32)
    logits = torch.tensor(np.array([np.log(probs)]), dtype=torch.float32)
    
    mock_model = MockLogitsModel(logits)
    dummy_input = torch.zeros((1, 3, 380, 380), dtype=torch.float32)
    device = torch.device("cpu")

    result = run_inference(mock_model, dummy_input, device)

    # Assert probability calculation exactly matches indices 2, 3, 4
    expected_referable_prob = float(probs[2] + probs[3] + probs[4])
    assert abs(result["referable_probability"] - expected_referable_prob) < 1e-4, (
        f"Expected referable_probability ~ {expected_referable_prob}, got {result['referable_probability']}"
    )

    # Ensure Class 1 (Mild DR probability 0.40) was NOT added
    assert result["referable_probability"] < 0.85, (
        "Mild DR (Class 1) was incorrectly included in the referable probability sum!"
    )

def test_clinical_referable_status_mapping_grades_0_to_4():
    """
    Verifies clinical classification mapping:
      Class 0 (No DR)            -> Non-referable
      Class 1 (Mild DR)          -> Non-referable
      Class 2 (Moderate DR)      -> Referable
      Class 3 (Severe DR)        -> Referable
      Class 4 (Proliferative DR) -> Referable
    """
    dummy_input = torch.zeros((1, 3, 380, 380), dtype=torch.float32)
    device = torch.device("cpu")

    # Test each dominant class (90% confidence on target class)
    test_cases = [
        (0, "No DR", False),
        (1, "Mild DR", False),
        (2, "Moderate DR", True),
        (3, "Severe DR", True),
        (4, "Proliferative DR", True),
    ]

    for class_id, class_name, should_be_referable in test_cases:
        probs = np.zeros(5, dtype=np.float32) + 0.01
        probs[class_id] = 0.96
        probs = probs / np.sum(probs)  # Normalize
        
        logits = torch.tensor(np.array([np.log(probs)]), dtype=torch.float32)
        mock_model = MockLogitsModel(logits)

        result = run_inference(mock_model, dummy_input, device)

        assert result["class_id"] == class_id
        assert result["class_name"] == class_name
        
        if should_be_referable:
            assert result["is_referable"] is True, (
                f"Class {class_id} ({class_name}) was expected to be REFERABLE (True), but got {result['is_referable']}"
            )
        else:
            assert result["is_referable"] is False, (
                f"Class {class_id} ({class_name}) was expected to be NON-REFERABLE (False), but got {result['is_referable']}"
            )

def test_configurable_min_grade_setting():
    """
    Verifies that REFERABLE_MIN_GRADE defaults to 2 and is configurable.
    """
    assert hasattr(settings, "REFERABLE_MIN_GRADE"), "settings.REFERABLE_MIN_GRADE must be defined"
    assert settings.REFERABLE_MIN_GRADE == 2, f"Expected default REFERABLE_MIN_GRADE=2, got {settings.REFERABLE_MIN_GRADE}"

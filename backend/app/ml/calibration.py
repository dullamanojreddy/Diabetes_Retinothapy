import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import numpy as np

from app.core.logging_config import logger
from app.core.config import settings

@dataclass
class CalibrationResult:
    temperature: float
    is_calibrated: bool
    calibrated_confidence: float
    uncalibrated_confidence: float
    uncalibrated_probabilities: Dict[str, float]
    calibrated_probabilities: Dict[str, float]
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "temperature": round(self.temperature, 4),
            "is_calibrated": self.is_calibrated,
            "calibrated_confidence": round(self.calibrated_confidence, 4),
            "uncalibrated_confidence": round(self.uncalibrated_confidence, 4),
            "uncalibrated_probabilities": {k: round(v, 4) for k, v in self.uncalibrated_probabilities.items()},
            "calibrated_probabilities": {k: round(v, 4) for k, v in self.calibrated_probabilities.items()},
            "metrics": self.metrics
        }

def compute_ece(
    probabilities: np.ndarray,
    labels: np.ndarray,
    n_bins: int = 10
) -> float:
    """
    Computes Expected Calibration Error (ECE) for multiclass classification.
    ECE measures the difference between expected accuracy and confidence across probability bins.
    """
    if len(probabilities) == 0 or len(labels) == 0:
        return 0.0

    confidences = np.max(probabilities, axis=1)
    predictions = np.argmax(probabilities, axis=1)
    accuracies = predictions == labels

    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    total_samples = len(labels)

    for bin_idx in range(n_bins):
        bin_lower = bin_boundaries[bin_idx]
        bin_upper = bin_boundaries[bin_idx + 1]

        in_bin = (confidences > bin_lower) & (confidences <= bin_upper) if bin_idx > 0 else (confidences >= bin_lower) & (confidences <= bin_upper)
        bin_size = np.sum(in_bin)

        if bin_size > 0:
            bin_accuracy = np.mean(accuracies[in_bin])
            bin_confidence = np.mean(confidences[in_bin])
            ece += (bin_size / total_samples) * np.abs(bin_accuracy - bin_confidence)

    return float(ece)

class TemperatureScaler:
    """
    Phase 7: Post-Hoc Confidence Calibration.
    Applies temperature scaling (p_i^(1/T) / sum_j(p_j^(1/T))) to mitigate overconfidence
    in deep network predictions while preserving predicted class rank and decision boundaries.
    """
    def __init__(self, calibration_path: Optional[Path] = None):
        self.calibration_path = calibration_path or Path(__file__).resolve().parent.parent.parent / "models" / "calibration.json"
        self.temperature: float = 1.18
        self.metrics: Dict[str, Any] = {}
        self.load_calibration()

    def load_calibration(self) -> None:
        """
        Loads calibrated temperature and metrics from persisted calibration.json.
        """
        if self.calibration_path.exists():
            try:
                with open(self.calibration_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    temp = float(data.get("temperature", 1.18))
                    if temp > 0:
                        self.temperature = temp
                    self.metrics = data.get("metrics", {})
                    logger.info(f"Loaded confidence calibration: T={self.temperature:.4f}")
            except Exception as e:
                logger.warning(f"Failed to load calibration from {self.calibration_path}: {e}. Using default T={self.temperature}")
        else:
            logger.info(f"Calibration file {self.calibration_path} not found. Using default T={self.temperature}")

    def calibrate_probabilities(
        self,
        raw_probabilities: Union[Dict[str, float], np.ndarray, List[float]]
    ) -> CalibrationResult:
        """
        Calibrates raw probabilities using the loaded temperature scaling factor T.
        Preserves original class ordering and dictionary keys.
        """
        if isinstance(raw_probabilities, dict):
            keys = list(raw_probabilities.keys())
            raw_vals = np.array([raw_probabilities[k] for k in keys], dtype=np.float64)
        else:
            keys = [settings.CLASS_MAPPING.get(i, f"Class_{i}") for i in range(len(raw_probabilities))]
            raw_vals = np.array(raw_probabilities, dtype=np.float64)

        # Normalize raw values to ensure sum=1
        sum_raw = np.sum(raw_vals)
        if sum_raw > 0:
            raw_vals = raw_vals / sum_raw
        else:
            raw_vals = np.ones_like(raw_vals) / len(raw_vals)

        # Apply temperature scaling: p_cal = softmax(log(p) / T) = (p^(1/T)) / sum(p^(1/T))
        clipped_p = np.clip(raw_vals, 1e-12, 1.0)
        powered_p = np.power(clipped_p, 1.0 / self.temperature)
        calibrated_vals = powered_p / np.sum(powered_p)

        uncalibrated_dict = {keys[i]: float(raw_vals[i]) for i in range(len(keys))}
        calibrated_dict = {keys[i]: float(calibrated_vals[i]) for i in range(len(keys))}

        uncal_conf = float(np.max(raw_vals))
        cal_conf = float(np.max(calibrated_vals))

        return CalibrationResult(
            temperature=self.temperature,
            is_calibrated=True,
            calibrated_confidence=cal_conf,
            uncalibrated_confidence=uncal_conf,
            uncalibrated_probabilities=uncalibrated_dict,
            calibrated_probabilities=calibrated_dict,
            metrics=self.metrics
        )

# Global singleton
temperature_scaler = TemperatureScaler()

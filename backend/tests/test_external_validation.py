import json
import csv
import numpy as np
import pytest
from pathlib import Path

from scripts.evaluate_external import (
    compute_quadratic_weighted_kappa,
    compute_clinical_metrics,
    run_evaluation
)
from scripts.export_predictions import export_predictions

def test_quadratic_weighted_kappa_perfect():
    """
    Verifies that identical predictions yield QWK = 1.0.
    """
    y_true = np.array([0, 1, 2, 3, 4, 0, 1, 2, 3, 4])
    y_pred = np.array([0, 1, 2, 3, 4, 0, 1, 2, 3, 4])
    qwk = compute_quadratic_weighted_kappa(y_true, y_pred, num_classes=5)
    assert pytest.approx(qwk, abs=1e-4) == 1.0

def test_quadratic_weighted_kappa_penalizes_large_discrepancies():
    """
    Verifies that off-by-one errors receive higher QWK than extreme off-by-four errors.
    """
    y_true = np.array([0, 1, 2, 3, 4, 0, 1, 2, 3, 4])
    y_close = np.array([0, 1, 2, 3, 3, 0, 1, 2, 3, 3])  # Off by 1 on class 4
    y_far = np.array([4, 3, 2, 1, 0, 4, 3, 2, 1, 0])    # Inverted / off by 4

    qwk_close = compute_quadratic_weighted_kappa(y_true, y_close, num_classes=5)
    qwk_far = compute_quadratic_weighted_kappa(y_true, y_far, num_classes=5)
    assert qwk_close > qwk_far
    assert qwk_close > 0.8
    assert qwk_far < 0.2

def test_clinical_metrics_calculation():
    """
    Verifies sensitivity, specificity, accuracy, and confusion matrix computation.
    """
    # Ground truth: 2 non-referable (0, 1), 2 referable (2, 3)
    y_true = np.array([0, 1, 2, 3])
    # Predictions: 0 -> 0 (TN), 1 -> 2 (FP), 2 -> 2 (TP), 3 -> 3 (TP)
    y_pred = np.array([0, 2, 2, 3])

    metrics = compute_clinical_metrics(y_true, y_pred, referable_min_grade=2)
    assert metrics["num_samples"] == 4
    assert metrics["multi_class"]["accuracy"] == 0.75

    ref = metrics["referable_dr_level_2_plus"]
    # 2 true referable (grades 2, 3): both predicted as referable -> TP = 2, FN = 0 -> Sensitivity = 1.0
    assert ref["sensitivity"] == 1.0
    # 2 true non-referable (grades 0, 1): one predicted as 0 (TN=1), one as 2 (FP=1) -> Specificity = 0.5
    assert ref["specificity"] == 0.5
    assert ref["tp"] == 2
    assert ref["fp"] == 1
    assert ref["fn"] == 0
    assert ref["tn"] == 1

def test_export_predictions_generates_valid_files(tmp_path):
    """
    Verifies that export_predictions produces valid CSV and JSON exports.
    """
    csv_file, json_file = export_predictions(output_dir=tmp_path, limit=20)
    assert csv_file.exists()
    assert json_file.exists()

    # Verify JSON format
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert isinstance(data, list)

    # Verify CSV format
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert "screening_id" in header
        assert "predicted_class" in header
        assert "referable_probability" in header

def test_run_evaluation_reproducibility(tmp_path):
    """
    Verifies that run_evaluation executes successfully and outputs valid metrics JSON.
    """
    results = run_evaluation(output_dir=tmp_path)
    assert "Messidor-2" in results
    assert "IDRiD" in results
    assert results["Messidor-2"]["referable_dr_level_2_plus"]["sensitivity"] > 0.90
    assert results["Messidor-2"]["multi_class"]["quadratic_weighted_kappa"] > 0.85

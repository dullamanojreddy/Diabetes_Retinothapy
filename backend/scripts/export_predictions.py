"""
Phase 11: Export Predictions Utility.
Exports stored predictions and clinical screening history into standardized CSV and JSON formats
for clinical trial auditing, statistical analysis, and MATLAB interoperability.
"""

import sys
import csv
import json
from typing import Optional, Tuple
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.services.history_service import history_service

def export_predictions(
    output_dir: Optional[Path] = None,
    limit: int = 500
) -> Tuple[Path, Path]:
    output_dir = output_dir or ROOT_DIR / "benchmarks" / "exports"
    output_dir.mkdir(parents=True, exist_ok=True)

    records = history_service.get_all(limit=limit)

    csv_file = output_dir / "screening_predictions.csv"
    json_file = output_dir / "screening_predictions.json"

    # Export JSON
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    # Export CSV
    fieldnames = [
        "screening_id",
        "timestamp",
        "filename",
        "status",
        "predicted_class",
        "predicted_class_name",
        "confidence",
        "calibrated_confidence",
        "temperature",
        "referable_probability",
        "is_referable",
        "quality_status",
        "blur_score",
        "brightness",
        "contrast",
        "od_detected",
        "fovea_detected",
        "vessel_coverage",
        "ma_count",
        "exudates_count",
        "hemorrhages_count",
        "pipeline_latency_ms"
    ]

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for r in records:
            cal = r.get("calibration") or {}
            qual = r.get("quality") or {}
            struct = r.get("structures") or {}
            les = r.get("lesions") or {}
            timing = r.get("timing") or {}

            od = struct.get("optic_disc") or {}
            fov = struct.get("fovea") or {}
            ves = struct.get("vessels") or {}

            ma = les.get("microaneurysms") or {}
            ex = les.get("exudates") or {}
            he = les.get("hemorrhages") or {}

            row = {
                "screening_id": r.get("screening_id", ""),
                "timestamp": r.get("timestamp", ""),
                "filename": r.get("filename", ""),
                "status": r.get("status", ""),
                "predicted_class": r.get("predicted_class", ""),
                "predicted_class_name": r.get("predicted_class_name", ""),
                "confidence": r.get("confidence", ""),
                "calibrated_confidence": cal.get("calibrated_confidence", ""),
                "temperature": cal.get("temperature", ""),
                "referable_probability": r.get("referable_probability", ""),
                "is_referable": r.get("is_referable", ""),
                "quality_status": qual.get("status", ""),
                "blur_score": qual.get("blur_score", ""),
                "brightness": qual.get("brightness", ""),
                "contrast": qual.get("contrast", ""),
                "od_detected": od.get("detected", False),
                "fovea_detected": fov.get("detected", False),
                "vessel_coverage": ves.get("vessel_coverage", ""),
                "ma_count": ma.get("candidate_count", 0),
                "exudates_count": ex.get("candidate_count", 0),
                "hemorrhages_count": he.get("candidate_count", 0),
                "pipeline_latency_ms": timing.get("total_pipeline_ms", r.get("inference_time_ms", ""))
            }
            writer.writerow(row)

    print(f"Successfully exported {len(records)} predictions:")
    print(f" - CSV:  {csv_file}")
    print(f" - JSON: {json_file}")
    return csv_file, json_file

if __name__ == "__main__":
    export_predictions()

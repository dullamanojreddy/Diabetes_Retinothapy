from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
import numpy as np

from app.retina.optic_disc import StructureFinding, detect_optic_disc
from app.retina.fovea import detect_fovea
from app.retina.vessels import VesselFinding, segment_vessels

@dataclass
class RetinalStructureResult:
    status: str  # "AVAILABLE" | "PARTIAL" | "UNAVAILABLE"
    optic_disc: StructureFinding
    fovea: StructureFinding
    vessels: VesselFinding
    artifacts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "optic_disc": self.optic_disc.to_dict(),
            "fovea": self.fovea.to_dict(),
            "vessels": self.vessels.to_dict(),
            "artifacts": self.artifacts
        }

def analyze_retinal_structure(image_rgb: np.ndarray) -> Tuple[RetinalStructureResult, np.ndarray, np.ndarray]:
    """
    Phase 5 Orchestrator: Retinal Structure Analysis.
    Extracts optic disc, fovea, and vessel morphology.
    Guarantees isolation: exceptions in any individual module are caught
    and marked as PARTIAL or UNAVAILABLE without halting the screening pipeline.
    """
    artifacts: List[str] = []
    h, w = image_rgb.shape[:2] if image_rgb is not None and image_rgb.size > 0 else (100, 100)
    empty_mask = np.zeros((h, w), dtype=np.uint8)

    # 1. Optic Disc Localization
    try:
        od_finding = detect_optic_disc(image_rgb)
    except Exception as e:
        artifacts.append(f"optic_disc_error: {str(e)}")
        od_finding = StructureFinding(detected=False, status="UNAVAILABLE", notes=[f"Error: {str(e)}"])

    # 2. Fovea Localization
    try:
        fovea_finding = detect_fovea(image_rgb, od_finding)
    except Exception as e:
        artifacts.append(f"fovea_error: {str(e)}")
        fovea_finding = StructureFinding(detected=False, status="UNAVAILABLE", notes=[f"Error: {str(e)}"])

    # 3. Vessel Segmentation
    try:
        vessel_finding, vessel_mask, skeleton_mask = segment_vessels(image_rgb)
    except Exception as e:
        artifacts.append(f"vessels_error: {str(e)}")
        vessel_finding = VesselFinding(detected=False, vessel_coverage=0.0, branch_density=0.0, vessel_pixel_count=0, status="UNAVAILABLE")
        vessel_mask, skeleton_mask = empty_mask, empty_mask

    # Derive overall status
    found_count = sum([od_finding.detected, fovea_finding.detected, vessel_finding.detected])
    if found_count == 3:
        status = "AVAILABLE"
    elif found_count > 0:
        status = "PARTIAL"
    else:
        status = "UNAVAILABLE"

    result = RetinalStructureResult(
        status=status,
        optic_disc=od_finding,
        fovea=fovea_finding,
        vessels=vessel_finding,
        artifacts=artifacts
    )

    return result, vessel_mask, skeleton_mask

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import numpy as np

from app.retina.retinal_analysis import RetinalStructureResult
from app.retina.microaneurysms import CandidateFinding, detect_microaneurysms
from app.retina.exudates import detect_exudates
from app.retina.hemorrhages import detect_hemorrhages
from app.retina.neovascularization import detect_neovascularization

@dataclass
class LesionEvidence:
    """
    Phase 6: Lesion Candidate Evidence (Research-Only).
    Captures candidate lesion findings for computational explainability and research exploration.
    Does NOT override or modify the deep learning model's DR severity classification.
    """
    research_only: bool = True
    status: str = "AVAILABLE"  # "AVAILABLE" | "PARTIAL" | "UNAVAILABLE"
    microaneurysms: CandidateFinding = field(default_factory=lambda: CandidateFinding(name="microaneurysms", status="UNAVAILABLE", candidate_count=0))
    exudates: CandidateFinding = field(default_factory=lambda: CandidateFinding(name="exudates", status="UNAVAILABLE", candidate_count=0))
    hemorrhages: CandidateFinding = field(default_factory=lambda: CandidateFinding(name="hemorrhages", status="UNAVAILABLE", candidate_count=0))
    neovascularization: CandidateFinding = field(default_factory=lambda: CandidateFinding(name="neovascularization", status="UNAVAILABLE", candidate_count=0, indicator="UNDETERMINED"))
    disclaimer: str = "Candidate lesion detections are for research investigation and computational explainability only. Not for clinical diagnostic use."
    artifacts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "research_only": self.research_only,
            "status": self.status,
            "microaneurysms": self.microaneurysms.to_dict(),
            "exudates": self.exudates.to_dict(),
            "hemorrhages": self.hemorrhages.to_dict(),
            "neovascularization": self.neovascularization.to_dict(),
            "disclaimer": self.disclaimer,
            "artifacts": self.artifacts
        }

def analyze_lesions(image_rgb: np.ndarray,
                    structures: Optional[RetinalStructureResult] = None,
                    vessel_mask: Optional[np.ndarray] = None,
                    skeleton_mask: Optional[np.ndarray] = None) -> LesionEvidence:
    """
    Phase 6 Orchestrator: Analyzes candidate microaneurysms, exudates, hemorrhages,
    and neovascularization cues. Guarantees failure isolation.
    """
    artifacts: List[str] = []

    od_bbox = None
    if structures and structures.optic_disc and structures.optic_disc.detected:
        od_bbox = structures.optic_disc.bbox

    # 1. Microaneurysms
    try:
        ma_finding = detect_microaneurysms(image_rgb, vessel_mask, od_bbox)
    except Exception as e:
        artifacts.append(f"microaneurysms_error: {str(e)}")
        ma_finding = CandidateFinding(name="microaneurysms", status="UNAVAILABLE", candidate_count=0, notes=[f"Error: {str(e)}"])

    # 2. Hard Exudates
    try:
        ex_finding = detect_exudates(image_rgb, od_bbox)
    except Exception as e:
        artifacts.append(f"exudates_error: {str(e)}")
        ex_finding = CandidateFinding(name="exudates", status="UNAVAILABLE", candidate_count=0, notes=[f"Error: {str(e)}"])

    # 3. Retinal Hemorrhages
    try:
        he_finding = detect_hemorrhages(image_rgb, vessel_mask, od_bbox)
    except Exception as e:
        artifacts.append(f"hemorrhages_error: {str(e)}")
        he_finding = CandidateFinding(name="hemorrhages", status="UNAVAILABLE", candidate_count=0, notes=[f"Error: {str(e)}"])

    # 4. Neovascularization
    try:
        nv_finding = detect_neovascularization(image_rgb, skeleton_mask, vessel_mask)
    except Exception as e:
        artifacts.append(f"neovascularization_error: {str(e)}")
        nv_finding = CandidateFinding(name="neovascularization", status="UNAVAILABLE", candidate_count=0, indicator="UNDETERMINED", notes=[f"Error: {str(e)}"])

    # Derive overall status
    available_count = sum([f.status == "AVAILABLE" for f in [ma_finding, ex_finding, he_finding, nv_finding]])
    if available_count == 4:
        overall_status = "AVAILABLE"
    elif available_count > 0:
        overall_status = "PARTIAL"
    else:
        overall_status = "UNAVAILABLE"

    return LesionEvidence(
        research_only=True,
        status=overall_status,
        microaneurysms=ma_finding,
        exudates=ex_finding,
        hemorrhages=he_finding,
        neovascularization=nv_finding,
        artifacts=artifacts
    )

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import cv2
import numpy as np

@dataclass
class CandidateFinding:
    name: str
    status: str  # "AVAILABLE" | "PARTIAL" | "UNAVAILABLE"
    candidate_count: int
    regions: List[List[int]] = field(default_factory=list)  # [[x, y, w, h], ...]
    points: List[List[int]] = field(default_factory=list)   # [[cx, cy], ...]
    heuristic_score: float = 0.0
    indicator: Optional[str] = None  # For neovascularization ("SUSPECTED" | "NOT_DETECTED" | "UNDETERMINED")
    method: str = "classical_morphology"
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "candidate_count": int(self.candidate_count),
            "regions": self.regions[:50],  # Cap to top 50 to avoid massive payloads
            "points": self.points[:50],
            "heuristic_score": round(float(self.heuristic_score), 3),
            "indicator": self.indicator,
            "method": self.method,
            "notes": self.notes
        }

def detect_microaneurysms(image_rgb: np.ndarray,
                          vessel_mask: Optional[np.ndarray] = None,
                          optic_disc_bbox: Optional[List[int]] = None) -> CandidateFinding:
    """
    Phase 6: Microaneurysm Candidate Detection (Research-Only).
    Detects small isolated dark punctate capillary dilations in green channel
    after subtracting the vascular tree and optic disc region.
    """
    if image_rgb is None or image_rgb.size == 0:
        return CandidateFinding(name="microaneurysms", status="UNAVAILABLE", candidate_count=0, notes=["Empty input image."])

    h, w = image_rgb.shape[:2]
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    fg_mask = gray > 20
    if not np.any(fg_mask):
        return CandidateFinding(name="microaneurysms", status="UNAVAILABLE", candidate_count=0, notes=["No retinal foreground detected."])

    green = image_rgb[:, :, 1]

    # Background estimation via median blur (removes punctate spots while preserving background)
    bg_est = cv2.medianBlur(green, 15)
    diff = cv2.subtract(bg_est, green)
    diff[~fg_mask] = 0

    # Vessel exclusion
    if vessel_mask is not None and vessel_mask.shape == diff.shape:
        dilated_vessels = cv2.dilate(vessel_mask, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
        diff[dilated_vessels > 0] = 0

    # Optic disc exclusion
    if optic_disc_bbox is not None and len(optic_disc_bbox) == 4:
        ox, oy, ow, oh = optic_disc_bbox
        # Dilate optic disc mask by 20%
        ox1 = max(0, int(ox - ow * 0.1))
        oy1 = max(0, int(oy - oh * 0.1))
        ox2 = min(w, int(ox + ow * 1.1))
        oy2 = min(h, int(oy + oh * 1.1))
        diff[oy1:oy2, ox1:ox2] = 0

    # Threshold small dark local residuals
    vals = diff[fg_mask]
    thresh_val = np.percentile(vals, 98.0) if len(vals) > 0 else 25
    _, candidates = cv2.threshold(diff, int(thresh_val), 255, cv2.THRESH_BINARY)

    # Connected component size/shape filter (diameter 2 to 12 px, area 3 to 100 px)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(candidates, connectivity=8)
    regions: List[List[int]] = []
    points: List[List[int]] = []

    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        bw = stats[i, cv2.CC_STAT_WIDTH]
        bh = stats[i, cv2.CC_STAT_HEIGHT]
        aspect = float(bw) / float(max(1, bh))

        if 3 <= area <= 120 and 0.4 <= aspect <= 2.5:
            cx, cy = centroids[i]
            x, y = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP]
            regions.append([int(x), int(y), int(bw), int(bh)])
            points.append([int(cx), int(cy)])

    count = len(regions)
    heuristic_score = min(1.0, count / 25.0)

    return CandidateFinding(
        name="microaneurysms",
        status="AVAILABLE",
        candidate_count=count,
        regions=regions,
        points=points,
        heuristic_score=heuristic_score,
        method="green_background_subtraction_vessel_exclusion",
        notes=[f"Found {count} candidate punctate microaneurysm blobs (research only)."]
    )

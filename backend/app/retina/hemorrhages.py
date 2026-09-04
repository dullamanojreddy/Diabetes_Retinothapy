from typing import List, Optional
import cv2
import numpy as np
from app.retina.microaneurysms import CandidateFinding

def detect_hemorrhages(image_rgb: np.ndarray,
                       vessel_mask: Optional[np.ndarray] = None,
                       optic_disc_bbox: Optional[List[int]] = None) -> CandidateFinding:
    """
    Phase 6: Retinal Hemorrhage Candidate Detection (Research-Only).
    Detects intraretinal dot/blot and flame-shaped hemorrhage candidates
    larger than focal microaneurysms, with vessel and optic disc exclusions.
    """
    if image_rgb is None or image_rgb.size == 0:
        return CandidateFinding(name="hemorrhages", status="UNAVAILABLE", candidate_count=0, notes=["Empty input image."])

    h, w = image_rgb.shape[:2]
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    fg_mask = gray > 20
    if not np.any(fg_mask):
        return CandidateFinding(name="hemorrhages", status="UNAVAILABLE", candidate_count=0, notes=["No retinal foreground detected."])

    green = image_rgb[:, :, 1]
    
    # Large background illumination profile
    bg_green = cv2.GaussianBlur(green, (35, 35), 0)
    dark_residual = cv2.subtract(bg_green, green)
    dark_residual[~fg_mask] = 0

    # Vessel exclusion
    if vessel_mask is not None and vessel_mask.shape == dark_residual.shape:
        dilated_vessels = cv2.dilate(vessel_mask, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)))
        dark_residual[dilated_vessels > 0] = 0

    # Optic disc exclusion
    if optic_disc_bbox is not None and len(optic_disc_bbox) == 4:
        ox, oy, ow, oh = optic_disc_bbox
        ox1 = max(0, int(ox - ow * 0.2))
        oy1 = max(0, int(oy - oh * 0.2))
        ox2 = min(w, int(ox + ow * 1.2))
        oy2 = min(h, int(oy + oh * 1.2))
        dark_residual[oy1:oy2, ox1:ox2] = 0

    vals = dark_residual[fg_mask]
    thresh_val = np.percentile(vals, 97.0) if len(vals) > 0 else 30
    _, candidates = cv2.threshold(dark_residual, int(thresh_val), 255, cv2.THRESH_BINARY)

    # Hemorrhages are larger than microaneurysms (area 60 to 2000 pixels)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(candidates, connectivity=8)
    regions: List[List[int]] = []
    points: List[List[int]] = []

    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if 60 <= area <= 2500:
            cx, cy = centroids[i]
            x, y = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP]
            bw, bh = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
            regions.append([int(x), int(y), int(bw), int(bh)])
            points.append([int(cx), int(cy)])

    count = len(regions)
    heuristic_score = min(1.0, count / 15.0)

    return CandidateFinding(
        name="hemorrhages",
        status="AVAILABLE",
        candidate_count=count,
        regions=regions,
        points=points,
        heuristic_score=heuristic_score,
        method="background_dark_residual_morphology",
        notes=[f"Found {count} candidate intraretinal hemorrhage regions (research only)."]
    )

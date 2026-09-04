from typing import List, Optional
import cv2
import numpy as np
from app.retina.microaneurysms import CandidateFinding

def detect_exudates(image_rgb: np.ndarray, optic_disc_bbox: Optional[List[int]] = None) -> CandidateFinding:
    """
    Phase 6: Hard Exudate Candidate Detection (Research-Only).
    Detects bright yellowish lipid/protein deposits with sharp boundaries,
    excluding the physiological optic nerve head.
    """
    if image_rgb is None or image_rgb.size == 0:
        return CandidateFinding(name="exudates", status="UNAVAILABLE", candidate_count=0, notes=["Empty input image."])

    h, w = image_rgb.shape[:2]
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    fg_mask = gray > 20
    if not np.any(fg_mask):
        return CandidateFinding(name="exudates", status="UNAVAILABLE", candidate_count=0, notes=["No retinal foreground detected."])

    # Convert to LAB (Luminance) and HSV (Saturation)
    lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB)
    l_channel = lab[:, :, 0]
    
    # Exudates exhibit high luminance and distinct yellow contrast (R > 120, G > 80, B < 80)
    r = image_rgb[:, :, 0].astype(np.float32)
    g = image_rgb[:, :, 1].astype(np.float32)
    b = image_rgb[:, :, 2].astype(np.float32)
    yellow_score = (r + g) * 0.5 - b
    yellow_score[~fg_mask] = 0

    # Local background illumination subtraction
    bg_l = cv2.GaussianBlur(l_channel, (25, 25), 0)
    bright_diff = cv2.subtract(l_channel, bg_l)
    bright_diff[~fg_mask] = 0

    # Optic disc exclusion (optic disc is naturally bright and must not be marked as exudate)
    if optic_disc_bbox is not None and len(optic_disc_bbox) == 4:
        ox, oy, ow, oh = optic_disc_bbox
        ox1 = max(0, int(ox - ow * 0.15))
        oy1 = max(0, int(oy - oh * 0.15))
        ox2 = min(w, int(ox + ow * 1.15))
        oy2 = min(h, int(oy + oh * 1.15))
        bright_diff[oy1:oy2, ox1:ox2] = 0
        yellow_score[oy1:oy2, ox1:ox2] = 0

    # Threshold for sharp bright peaks with yellow tint
    vals = bright_diff[fg_mask]
    thresh_val = np.percentile(vals, 97.5) if len(vals) > 0 else 30
    _, candidates = cv2.threshold(bright_diff, int(thresh_val), 255, cv2.THRESH_BINARY)
    candidates[yellow_score < 15] = 0

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(candidates, connectivity=8)
    regions: List[List[int]] = []
    points: List[List[int]] = []

    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if 8 <= area <= 800:
            cx, cy = centroids[i]
            x, y = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP]
            bw, bh = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
            regions.append([int(x), int(y), int(bw), int(bh)])
            points.append([int(cx), int(cy)])

    count = len(regions)
    heuristic_score = min(1.0, count / 20.0)

    return CandidateFinding(
        name="exudates",
        status="AVAILABLE",
        candidate_count=count,
        regions=regions,
        points=points,
        heuristic_score=heuristic_score,
        method="luminance_contrast_yellow_spectral_filtering",
        notes=[f"Found {count} candidate hard exudate clusters (research only)."]
    )

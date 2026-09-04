from typing import Optional
import cv2
import numpy as np
from app.retina.microaneurysms import CandidateFinding

def detect_neovascularization(image_rgb: np.ndarray,
                             skeleton_mask: Optional[np.ndarray] = None,
                             vessel_mask: Optional[np.ndarray] = None) -> CandidateFinding:
    """
    Phase 6: Neovascularization Screening Heuristic (Research-Only).
    Analyzes vessel branching complexity, local skeleton cluster density,
    and tortuosity cues to identify patterns characteristic of proliferative neovascularization.
    """
    if image_rgb is None or image_rgb.size == 0 or skeleton_mask is None:
        return CandidateFinding(
            name="neovascularization",
            status="UNAVAILABLE",
            candidate_count=0,
            indicator="UNDETERMINED",
            notes=["Vessel skeleton prerequisite unavailable."]
        )

    h, w = image_rgb.shape[:2]
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    fg_mask = gray > 20
    fg_count = int(np.count_nonzero(fg_mask))

    skeleton_pixels = int(np.count_nonzero(skeleton_mask))
    if skeleton_pixels < 100 or fg_count == 0:
        return CandidateFinding(
            name="neovascularization",
            status="PARTIAL",
            candidate_count=0,
            indicator="UNDETERMINED",
            notes=["Insufficient vessel skeleton density to evaluate neovascularization."]
        )

    # 1. Local branch point detection on skeleton
    # A skeleton branch point has >= 3 neighbors in 3x3 window
    kernel = np.array([[1, 1, 1],
                       [1, 0, 1],
                       [1, 1, 1]], dtype=np.uint8)
    neighbor_count = cv2.filter2D(skeleton_mask.astype(np.float32) / 255.0, -1, kernel)
    branch_points = (skeleton_mask > 0) & (neighbor_count >= 3.0)
    branch_count = int(np.count_nonzero(branch_points))

    # 2. Measure local cluster density via Gaussian smoothing of branch points
    density_map = cv2.GaussianBlur(branch_points.astype(np.float32), (31, 31), 0)
    max_density = float(np.max(density_map)) if np.any(fg_mask) else 0.0

    # 3. Ratio of branch points to total skeleton length
    branching_ratio = float(branch_count) / float(max(1, skeleton_pixels))

    # Neovascularization heuristic
    # High local cluster of tangled branching indicates abnormal vessel proliferation
    if max_density > 0.035 or branching_ratio > 0.08:
        indicator = "SUSPECTED"
        score = min(0.90, max_density * 20.0)
        notes = ["High-density clustered vessel arborization detected (research finding)."]
    else:
        indicator = "NOT_DETECTED"
        score = min(0.25, max_density * 5.0)
        notes = ["Normal organized vascular branching architecture observed."]

    return CandidateFinding(
        name="neovascularization",
        status="AVAILABLE",
        candidate_count=branch_count,
        heuristic_score=score,
        indicator=indicator,
        method="skeleton_branch_density_cluster_analysis",
        notes=notes
    )

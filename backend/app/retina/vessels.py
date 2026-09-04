from dataclasses import dataclass
from typing import Dict, Any, Tuple
import cv2
import numpy as np

@dataclass
class VesselFinding:
    detected: bool
    vessel_coverage: float  # [0.0, 1.0] fraction of retinal foreground
    branch_density: float   # [0.0, 1.0] skeleton branch density
    vessel_pixel_count: int
    method: str = "green_clahe_morphological_blackhat"
    status: str = "AVAILABLE"  # "AVAILABLE" | "UNAVAILABLE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "detected": self.detected,
            "vessel_coverage": round(float(self.vessel_coverage), 4),
            "branch_density": round(float(self.branch_density), 4),
            "vessel_pixel_count": int(self.vessel_pixel_count),
            "method": self.method,
            "status": self.status
        }

def segment_vessels(image_rgb: np.ndarray) -> Tuple[VesselFinding, np.ndarray, np.ndarray]:
    """
    Phase 5: Retinal Vessel Segmentation.
    Extracts the retinal vascular tree using green-channel optical absorption,
    contrast enhancement, and morphological linear tubular filtering.
    Returns: (VesselFinding, vessel_mask, skeleton_mask)
    """
    if image_rgb is None or image_rgb.size == 0:
        empty = np.zeros((100, 100), dtype=np.uint8)
        return VesselFinding(detected=False, vessel_coverage=0.0, branch_density=0.0, vessel_pixel_count=0, status="UNAVAILABLE"), empty, empty

    h, w = image_rgb.shape[:2]
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    fg_mask = gray > 18
    fg_count = int(np.count_nonzero(fg_mask))
    if fg_count == 0:
        empty = np.zeros((h, w), dtype=np.uint8)
        return VesselFinding(detected=False, vessel_coverage=0.0, branch_density=0.0, vessel_pixel_count=0, status="UNAVAILABLE"), empty, empty

    # 1. Green channel extraction (maximum hemoglobin contrast)
    green = image_rgb[:, :, 1]

    # 2. CLAHE contrast equalization
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    cl_g = clahe.apply(green)

    # 3. Morphological Black-Hat to extract dark tubular structures
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    blackhat = cv2.morphologyEx(cl_g, cv2.MORPH_BLACKHAT, kernel)
    blackhat[~fg_mask] = 0

    # 4. Adaptive thresholding on filtered vessel signal
    bh_fg = blackhat[fg_mask]
    thresh_val = np.percentile(bh_fg, 88.0) if len(bh_fg) > 0 else 25
    _, binary = cv2.threshold(blackhat, int(thresh_val), 255, cv2.THRESH_BINARY)
    binary[~fg_mask] = 0

    # 5. Connected Component Area Filtering (remove tiny isolated speckles < 12 px)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    vessel_mask = np.zeros_like(binary)
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= 12:
            vessel_mask[labels == i] = 255

    vessel_pixels = int(np.count_nonzero(vessel_mask))
    coverage = float(vessel_pixels) / float(max(1, fg_count))

    # 6. Skeletonization / Thinning
    skeleton = cv2.ximgproc.thinning(vessel_mask) if hasattr(cv2, "ximgproc") else _simple_thinning(vessel_mask)
    skeleton_pixels = int(np.count_nonzero(skeleton))
    branch_density = float(skeleton_pixels) / float(max(1, fg_count))

    finding = VesselFinding(
        detected=vessel_pixels > 50,
        vessel_coverage=coverage,
        branch_density=branch_density,
        vessel_pixel_count=vessel_pixels,
        method="green_clahe_morphological_blackhat",
        status="AVAILABLE"
    )

    return finding, vessel_mask, skeleton

def _simple_thinning(binary: np.ndarray) -> np.ndarray:
    """Morphological erosion-based skeletonization fallback."""
    skel = np.zeros(binary.shape, np.uint8)
    img = binary.copy()
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    for _ in range(30):
        eroded = cv2.erode(img, element)
        temp = cv2.dilate(eroded, element)
        temp = cv2.subtract(img, temp)
        skel = cv2.bitwise_or(skel, temp)
        img = eroded.copy()
        if cv2.countNonZero(img) == 0:
            break
    return skel

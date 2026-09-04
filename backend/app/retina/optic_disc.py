from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import cv2
import numpy as np

@dataclass
class StructureFinding:
    detected: bool
    center_x: Optional[float] = None
    center_y: Optional[float] = None
    radius: Optional[float] = None
    confidence: float = 0.0
    method: str = "classical_cv"
    status: str = "AVAILABLE"  # "AVAILABLE" | "PARTIAL" | "UNAVAILABLE"
    bbox: Optional[List[int]] = None  # [x, y, w, h]
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "detected": self.detected,
            "center_x": round(float(self.center_x), 1) if self.center_x is not None else None,
            "center_y": round(float(self.center_y), 1) if self.center_y is not None else None,
            "radius": round(float(self.radius), 1) if self.radius is not None else None,
            "confidence": round(float(self.confidence), 3),
            "method": self.method,
            "status": self.status,
            "bbox": self.bbox,
            "notes": self.notes
        }

def detect_optic_disc(image_rgb: np.ndarray) -> StructureFinding:
    """
    Phase 5: Classical CV Optic Disc Localization.
    Locates the optic nerve head (optic disc) candidate based on peak local luminance,
    morphological circularity, and expected biological size constraints.
    Does NOT use heavy neural networks or modify DR classification.
    """
    if image_rgb is None or image_rgb.size == 0:
        return StructureFinding(detected=False, status="UNAVAILABLE", notes=["Empty input image."])

    h, w = image_rgb.shape[:2]
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    fg_mask = gray > 20
    if not np.any(fg_mask):
        return StructureFinding(detected=False, status="UNAVAILABLE", notes=["No retinal foreground detected."])

    # Optic disc is brightest in Red channel and prominently delineated
    red = image_rgb[:, :, 0]
    green = image_rgb[:, :, 1]
    
    # Combined brightness highlighting optic disc pallor
    bright_map = (red.astype(np.float32) * 0.6 + green.astype(np.float32) * 0.4).astype(np.uint8)
    bright_map[~fg_mask] = 0

    # Smooth local vessel crossings
    blurred = cv2.GaussianBlur(bright_map, (15, 15), 0)

    # Threshold the top 2-3% brightest retinal pixels
    fg_vals = blurred[fg_mask]
    thresh_val = np.percentile(fg_vals, 97.5) if len(fg_vals) > 0 else 200
    _, binary = cv2.threshold(blurred, int(thresh_val), 255, cv2.THRESH_BINARY)
    binary[~fg_mask] = 0

    # Morphological closing to coalesce bright optic disc core
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return StructureFinding(detected=False, status="UNAVAILABLE", notes=["No candidate bright regions found."])

    # Expected optic disc diameter is ~1/15th to 1/6th of image width
    min_area = (w * 0.03) ** 2 * np.pi * 0.25
    max_area = (w * 0.20) ** 2 * np.pi * 0.25

    best_candidate = None
    best_score = -1.0

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area or area > max_area:
            continue

        perimeter = cv2.arcLength(cnt, True)
        if perimeter <= 0:
            continue

        circularity = 4 * np.pi * (area / (perimeter * perimeter))
        (cx, cy), radius = cv2.minEnclosingCircle(cnt)

        # Distance from peripheral borders (disc is not on the extreme camera edge)
        margin = min(w, h) * 0.08
        if cx < margin or cx > (w - margin) or cy < margin or cy > (h - margin):
            continue

        # Score candidate based on brightness, area consistency, and circularity
        mask_c = np.zeros_like(gray)
        cv2.drawContours(mask_c, [cnt], -1, 255, -1)
        mean_lum = float(np.mean(bright_map[mask_c > 0])) if np.any(mask_c > 0) else 0.0

        score = (mean_lum / 255.0) * 0.5 + min(1.0, circularity) * 0.3 + min(1.0, area / min_area) * 0.2
        if score > best_score:
            best_score = score
            x, y, bw, bh = cv2.boundingRect(cnt)
            best_candidate = (cx, cy, radius, [x, y, bw, bh], score)

    if best_candidate is not None:
        cx, cy, radius, bbox, score = best_candidate
        heuristic_conf = min(0.95, max(0.50, score))
        return StructureFinding(
            detected=True,
            center_x=float(cx),
            center_y=float(cy),
            radius=float(radius),
            confidence=heuristic_conf,
            method="luminance_morphology_circularity",
            status="AVAILABLE",
            bbox=bbox,
            notes=["Optic disc localized successfully."]
        )

    # Fallback: argmax centroid of smoothed luminance
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(blurred)
    fallback_x, fallback_y = float(max_loc[0]), float(max_loc[1])
    est_radius = float(min(w, h) * 0.06)
    return StructureFinding(
        detected=True,
        center_x=fallback_x,
        center_y=fallback_y,
        radius=est_radius,
        confidence=0.45,
        method="peak_luminance_centroid_fallback",
        status="PARTIAL",
        bbox=[int(fallback_x - est_radius), int(fallback_y - est_radius), int(est_radius * 2), int(est_radius * 2)],
        notes=["Optic disc localized with fallback peak centroid."]
    )

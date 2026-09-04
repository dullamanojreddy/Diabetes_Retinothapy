import cv2
import numpy as np
from app.retina.optic_disc import StructureFinding

def detect_fovea(image_rgb: np.ndarray, optic_disc: StructureFinding) -> StructureFinding:
    """
    Phase 5: Fovea Localization Module.
    Estimates fovea position relative to the localized optic disc and local macular darkness.
    The fovea is anatomical center of the macula, situated ~2.0 to 2.8 optic disc diameters
    horizontally from the optic nerve head.
    """
    if image_rgb is None or image_rgb.size == 0:
        return StructureFinding(detected=False, status="UNAVAILABLE", notes=["Empty input image."])

    if not optic_disc.detected or optic_disc.center_x is None or optic_disc.center_y is None:
        return StructureFinding(
            detected=False,
            status="UNAVAILABLE",
            notes=["Optic disc localization required for fovea estimation."]
        )

    h, w = image_rgb.shape[:2]
    od_x = optic_disc.center_x
    od_y = optic_disc.center_y
    od_radius = optic_disc.radius if optic_disc.radius else float(min(w, h) * 0.06)

    # Direction: If optic disc is in the left half, fovea is to the right (+x);
    # If optic disc is in the right half, fovea is to the left (-x).
    direction = 1.0 if od_x < (w * 0.5) else -1.0
    expected_dist = od_radius * 2.5 * 2.0  # Approx 2.5 disc diameters

    est_fovea_x = od_x + (direction * expected_dist)
    est_fovea_y = od_y + (od_radius * 0.25)  # Slight physiological vertical depression

    # Clamp within retinal frame
    est_fovea_x = max(od_radius, min(w - od_radius, est_fovea_x))
    est_fovea_y = max(od_radius, min(h - od_radius, est_fovea_y))

    # Refine in local macular ROI (search for local darkness minimum in green/blue channels)
    roi_r = int(od_radius * 1.2)
    x1 = max(0, int(est_fovea_x - roi_r))
    x2 = min(w, int(est_fovea_x + roi_r))
    y1 = max(0, int(est_fovea_y - roi_r))
    y2 = min(h, int(est_fovea_y + roi_r))

    if x2 > x1 and y2 > y1:
        green = image_rgb[y1:y2, x1:x2, 1]
        blurred_roi = cv2.GaussianBlur(green, (15, 15), 0)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(blurred_roi)
        refined_x = float(x1 + min_loc[0])
        refined_y = float(y1 + min_loc[1])
    else:
        refined_x = float(est_fovea_x)
        refined_y = float(est_fovea_y)

    fovea_radius = float(od_radius * 0.4)
    confidence = float(optic_disc.confidence * 0.88)

    return StructureFinding(
        detected=True,
        center_x=refined_x,
        center_y=refined_y,
        radius=fovea_radius,
        confidence=confidence,
        method="relative_macular_darkness_geometry",
        status="AVAILABLE",
        bbox=[int(refined_x - fovea_radius), int(refined_y - fovea_radius), int(fovea_radius * 2), int(fovea_radius * 2)],
        notes=["Fovea localized relative to optic disc center and macular luminance minimum."]
    )

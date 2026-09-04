from dataclasses import dataclass, field
import io
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image
import numpy as np
import cv2

from app.core.config import settings
from app.core.logging_config import logger

@dataclass
class FundusValidationSignals:
    aspect_ratio_score: float
    fov_score: float
    dark_boundary_score: float
    retinal_color_score: float
    texture_score: float
    edge_density_score: float
    vessel_like_score: float

    def to_dict(self) -> dict:
        return {
            "aspect_ratio_score": round(self.aspect_ratio_score, 3),
            "fov_score": round(self.fov_score, 3),
            "dark_boundary_score": round(self.dark_boundary_score, 3),
            "retinal_color_score": round(self.retinal_color_score, 3),
            "texture_score": round(self.texture_score, 3),
            "edge_density_score": round(self.edge_density_score, 3),
            "vessel_like_score": round(self.vessel_like_score, 3),
        }

@dataclass
class QualityResult:
    width: int
    height: int
    brightness: float
    contrast: float
    blur_score: float
    status: str  # "ACCEPT" | "LOW_QUALITY" | "INVALID"
    reasons: List[str] = field(default_factory=list)
    signals: Optional[FundusValidationSignals] = None

def load_image_bytes(contents: bytes) -> Image.Image:
    """
    Safely decodes raw bytes into a PIL RGB Image.
    Raises ValueError on empty, corrupt, or unreadable files.
    """
    if not contents:
        raise ValueError("Image byte buffer is empty.")
    try:
        img = Image.open(io.BytesIO(contents))
        img.load()  # Force decode to catch truncated/corrupted images
        img = img.convert("RGB")
        return img
    except Exception as e:
        raise ValueError(f"Invalid or corrupted image content: {str(e)}")

def assess_fundus_and_quality(pil_image: Image.Image) -> QualityResult:
    """
    Hardened multi-signal deterministic heuristic gate for fundus validation and technical quality:
    1. Aspect Ratio: standard retinal photography is ~1:1 to 4:3 (expected 0.70 - 1.45)
    2. Camera FOV Aperture: circular/elliptical optical aperture geometry (not full rectangular bleed)
    3. Peripheral Optical Camera Boundary: unilluminated dark corners from camera mask
    4. Retinal Hemoglobin Absorption Spectrum: R > G >= B, low blue reflectance, hemoglobin absorption
    5. Biological Retinal Luminance Texture: natural organic variance and gradient across retina
    6. Retinal Vascular Tree: green-channel morphological tubular dark structures (vessels)
    7. Technical quality: exposure, contrast, Laplacian blur score

    Returns QualityResult with status in {"ACCEPT", "LOW_QUALITY", "INVALID"}, descriptive reasons,
    and structured validation signals.
    """
    width, height = pil_image.size
    img_np = np.array(pil_image)
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    
    # 1. Dimension check
    if width < settings.MIN_IMAGE_DIMENSION or height < settings.MIN_IMAGE_DIMENSION:
        return QualityResult(
            width=width,
            height=height,
            brightness=float(np.mean(gray)),
            contrast=float(np.std(gray)),
            blur_score=0.0,
            status="INVALID",
            reasons=[f"Image dimensions ({width}x{height}) are smaller than minimum allowed ({settings.MIN_IMAGE_DIMENSION}x{settings.MIN_IMAGE_DIMENSION})."],
            signals=None
        )
    
    # 2. Aspect Ratio Signal
    aspect_ratio = width / max(1, height)
    ar_score = 1.0 if (0.75 <= aspect_ratio <= 1.35) else (0.8 if (0.70 <= aspect_ratio <= 1.45) else 0.0)
    if aspect_ratio < 0.70 or aspect_ratio > 1.45:
        signals = FundusValidationSignals(
            aspect_ratio_score=0.0,
            fov_score=0.0,
            dark_boundary_score=0.0,
            retinal_color_score=0.0,
            texture_score=0.0,
            edge_density_score=0.0,
            vessel_like_score=0.0
        )
        return QualityResult(
            width=width,
            height=height,
            brightness=float(np.mean(gray)),
            contrast=float(np.std(gray)),
            blur_score=0.0,
            status="INVALID",
            reasons=[f"Image aspect ratio ({aspect_ratio:.2f}) deviates from standard retinal fundus photography format (expected 0.70 - 1.45)."],
            signals=signals
        )

    # Calculate core metrics
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    
    # 3. Peripheral Optical Camera Boundary (Corner Darkness)
    cw, ch = max(2, int(width * 0.08)), max(2, int(height * 0.08))
    corner_patches = [
        gray[:ch, :cw],
        gray[:ch, -cw:],
        gray[-ch:, :cw],
        gray[-ch:, -cw:]
    ]
    corner_means = [float(np.mean(patch)) for patch in corner_patches]
    avg_corner_mean = float(np.mean(corner_means))
    dark_corners_count = sum(1 for cm in corner_means if cm < 45.0)
    dark_boundary_score = max(0.0, min(1.0, (120.0 - avg_corner_mean) / 100.0))
    has_camera_mask = (dark_corners_count >= 3 and avg_corner_mean < 45.0)
    
    # 4. Circular FOV Aperture & Foreground Geometry
    _, thresh = cv2.threshold(gray, 18, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    fov_score = 0.0
    area_ratio = 0.0
    circularity = 0.0
    obj_aspect = 0.0
    
    if contours:
        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)
        perimeter = cv2.arcLength(c, True)
        circularity = 4 * np.pi * (area / (perimeter * perimeter)) if perimeter > 0 else 0.0
        x, y, bw, bh = cv2.boundingRect(c)
        obj_aspect = bw / max(1, bh)
        area_ratio = area / (width * height)
        
        if circularity >= 0.55 and (0.75 <= obj_aspect <= 1.30):
            if area_ratio < 0.92 or has_camera_mask:
                fov_score = min(1.0, circularity)
            else:
                fov_score = 0.20  # Full-bleed rectangular frame
        else:
            fov_score = max(0.0, circularity * 0.5)

    # 5. Retinal Hemoglobin Color Spectrum Physics
    r = img_np[:, :, 0].astype(np.float32)
    g = img_np[:, :, 1].astype(np.float32)
    b = img_np[:, :, 2].astype(np.float32)
    r_mean = float(np.mean(r))
    g_mean = float(np.mean(g))
    b_mean = float(np.mean(b))
    
    retinal_color_score = 1.0
    if b_mean > (r_mean * 0.72) or b_mean > 25.0:
        retinal_color_score -= 0.5
    if g_mean > (r_mean * 1.02):
        retinal_color_score -= 0.4
    if (r_mean - b_mean) < 18.0:
        retinal_color_score -= 0.4
    retinal_color_score = max(0.0, min(1.0, retinal_color_score))

    # 6. Biological Retinal Luminance Texture & Variance
    fg_mask = gray > 18
    blurred_macro = cv2.GaussianBlur(gray, (31, 31), 10)
    macro_std = float(np.std(blurred_macro[fg_mask])) if np.any(fg_mask) else 0.0
    texture_score = min(1.0, macro_std / 18.0)

    # 7. Retinal Edge Density (excludes text documents, screenshots, and flat images)
    edges = cv2.Canny(gray, 30, 100)
    edge_density = float(np.count_nonzero(edges[fg_mask])) / float(np.count_nonzero(fg_mask)) if np.any(fg_mask) else 0.0
    if 0.01 <= edge_density <= 0.15:
        edge_density_score = 1.0
    elif edge_density < 0.01:
        edge_density_score = edge_density / 0.01
    else:
        edge_density_score = max(0.0, 1.0 - (edge_density - 0.15) * 5.0)

    # 8. Retinal Vascular Tree (Morphological Tubular Structures in Green Channel)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl_g = clahe.apply(img_np[:, :, 1])
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    blackhat = cv2.morphologyEx(cl_g, cv2.MORPH_BLACKHAT, kernel)
    vessel_std = float(np.std(blackhat[fg_mask])) if np.any(fg_mask) else 0.0
    vessel_like_score = min(1.0, vessel_std / 12.0)

    # Package structured signals
    signals = FundusValidationSignals(
        aspect_ratio_score=ar_score,
        fov_score=fov_score,
        dark_boundary_score=dark_boundary_score,
        retinal_color_score=retinal_color_score,
        texture_score=texture_score,
        edge_density_score=edge_density_score,
        vessel_like_score=vessel_like_score
    )

    # --- HARD REJECTION RULES ---
    fundus_invalidation_reasons: List[str] = []
    
    # Check 1: Circular / Elliptical FOV aperture geometry
    if fov_score < 0.50 or (not has_camera_mask and area_ratio >= 0.92):
        fundus_invalidation_reasons.append("Image lacks circular field-of-view (FOV) aperture and camera boundaries.")
        
    # Check 2: Camera peripheral mask
    if dark_boundary_score < 0.35 and not has_camera_mask:
        fundus_invalidation_reasons.append("Image lacks peripheral optical camera boundary (bright corners).")
        
    # Check 3: Hemoglobin absorption profile
    if retinal_color_score < 0.60:
        fundus_invalidation_reasons.append("Color distribution lacks typical retinal hemoglobin absorption spectrum.")
        
    # Check 4: Biological texture (rejects solid orange/red, flat graphics)
    if texture_score < 0.35:
        fundus_invalidation_reasons.append("Image is flat or synthetic, lacking biological retinal luminance texture.")
        
    # Check 5: Retinal vascular tree and focus consistency
    if blur_score >= settings.MIN_BLUR_SCORE and vessel_like_score < 0.48:
        fundus_invalidation_reasons.append("Image lacks retinal vascular arborization in the green channel.")
    elif blur_score < settings.MIN_BLUR_SCORE and vessel_like_score < 0.30:
        if fov_score < 0.60 or dark_boundary_score < 0.60 or texture_score < 0.60:
            fundus_invalidation_reasons.append("Image lacks structural retinal characteristics.")

    # If any structural fundus requirement fails, intercept immediately
    if len(fundus_invalidation_reasons) > 0:
        return QualityResult(
            width=width,
            height=height,
            brightness=brightness,
            contrast=contrast,
            blur_score=blur_score,
            status="INVALID",
            reasons=fundus_invalidation_reasons,
            signals=signals
        )

    # 8. Technical Quality Checks (For confirmed authentic fundus images)
    quality_reasons: List[str] = []
    if brightness < settings.MIN_BRIGHTNESS:
        quality_reasons.append(f"Image is severely underexposed or dark (brightness: {brightness:.1f} < {settings.MIN_BRIGHTNESS}).")
    elif brightness > settings.MAX_BRIGHTNESS:
        quality_reasons.append(f"Image is severely overexposed or washed out (brightness: {brightness:.1f} > {settings.MAX_BRIGHTNESS}).")
        
    if contrast < settings.MIN_CONTRAST:
        quality_reasons.append(f"Image has insufficient contrast (contrast: {contrast:.1f} < {settings.MIN_CONTRAST}).")
        
    if blur_score < settings.MIN_BLUR_SCORE:
        quality_reasons.append(f"Image is excessively blurry or out of focus (blur score: {blur_score:.1f} < {settings.MIN_BLUR_SCORE}).")

    status = "LOW_QUALITY" if len(quality_reasons) > 0 else "ACCEPT"

    return QualityResult(
        width=width,
        height=height,
        brightness=round(brightness, 2),
        contrast=round(contrast, 2),
        blur_score=round(blur_score, 2),
        status=status,
        reasons=quality_reasons,
        signals=signals
    )

def save_numpy_image(img_array: np.ndarray, output_path: Path) -> Path:
    """
    Saves a numpy array (uint8 or float) as an image file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if img_array.dtype != np.uint8:
        if img_array.max() <= 1.0:
            img_array = (img_array * 255).astype(np.uint8)
        else:
            img_array = np.clip(img_array, 0, 255).astype(np.uint8)
    
    img = Image.fromarray(img_array)
    img.save(output_path, format="JPEG", quality=92)
    return output_path

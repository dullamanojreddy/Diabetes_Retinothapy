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
class QualityResult:
    width: int
    height: int
    brightness: float
    contrast: float
    blur_score: float
    status: str  # "ACCEPT" | "LOW_QUALITY" | "INVALID"
    reasons: List[str] = field(default_factory=list)

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
    Multi-signal deterministic heuristic gate for fundus validation and technical quality:
    1. Resolution & image aspect ratio (standard retinal photography is ~1:1 to 4:3)
    2. Circular / elliptical Field-of-View (FOV) aperture geometry
    3. Retinal color spectrum (R > G > B, low blue channel absorption)
    4. Vascular gradient texture & foreground entropy (rejects flat cartoon / synthetic graphics)
    5. Technical quality (exposure, contrast, blur score)
    
    Returns QualityResult with status in {"ACCEPT", "LOW_QUALITY", "INVALID"} and specific reasons.
    """
    width, height = pil_image.size
    img_np = np.array(pil_image)
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    
    reasons: List[str] = []
    
    # 1. Dimension & aspect ratio checks
    if width < settings.MIN_IMAGE_DIMENSION or height < settings.MIN_IMAGE_DIMENSION:
        return QualityResult(
            width=width,
            height=height,
            brightness=float(np.mean(gray)),
            contrast=float(np.std(gray)),
            blur_score=0.0,
            status="INVALID",
            reasons=[f"Image dimensions ({width}x{height}) are smaller than minimum allowed ({settings.MIN_IMAGE_DIMENSION}x{settings.MIN_IMAGE_DIMENSION})."]
        )
    
    aspect_ratio = width / max(1, height)
    # Retinal fundus photography is square (1:1) or standard sensor aspect (4:3); wide/ultrawide wallpapers/screenshots are non-retinal
    if aspect_ratio < 0.70 or aspect_ratio > 1.45:
        return QualityResult(
            width=width,
            height=height,
            brightness=float(np.mean(gray)),
            contrast=float(np.std(gray)),
            blur_score=0.0,
            status="INVALID",
            reasons=[f"Image aspect ratio ({aspect_ratio:.2f}) deviates from standard retinal fundus photography format (expected 0.70 - 1.45)."]
        )

    # Calculate core metrics
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    
    r = img_np[:, :, 0].astype(np.float32)
    g = img_np[:, :, 1].astype(np.float32)
    b = img_np[:, :, 2].astype(np.float32)
    
    r_mean = float(np.mean(r))
    g_mean = float(np.mean(g))
    b_mean = float(np.mean(b))
    
    # 2. Multi-signal Fundus Retinal Structure Check
    is_fundus_structure = True
    fundus_invalidation_reasons: List[str] = []
    
    # Check circular FOV contour
    _, thresh = cv2.threshold(gray, 18, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return QualityResult(
            width=width,
            height=height,
            brightness=brightness,
            contrast=contrast,
            blur_score=blur_score,
            status="INVALID",
            reasons=["Image contains no discernible foreground retinal structure."]
        )
        
    c = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(c)
    perimeter = cv2.arcLength(c, True)
    circularity = 4 * np.pi * (area / (perimeter * perimeter)) if perimeter > 0 else 0
    x, y, bw, bh = cv2.boundingRect(c)
    obj_aspect = bw / max(1, bh)
    
    if circularity < 0.55:
        is_fundus_structure = False
        fundus_invalidation_reasons.append(f"Foreground object lacks circular field-of-view (FOV) aperture geometry (circularity: {circularity:.2f} < 0.55).")
        
    if obj_aspect < 0.75 or obj_aspect > 1.30:
        is_fundus_structure = False
        fundus_invalidation_reasons.append(f"Foreground aperture aspect ratio ({obj_aspect:.2f}) is not circular/elliptical.")

    # Retinal tissue has strict color physics: Red >> Blue, Red >= Green
    if b_mean > (r_mean * 0.72) and b_mean > 30.0:
        is_fundus_structure = False
        fundus_invalidation_reasons.append("High blue-channel reflectance inconsistent with retinal fundus tissue.")
        
    if g_mean > (r_mean * 1.05):
        is_fundus_structure = False
        fundus_invalidation_reasons.append("Green channel exceeds red channel, characteristic of non-retinal scenes.")
        
    if (r_mean - b_mean) < 15.0 and brightness > 30.0:
        is_fundus_structure = False
        fundus_invalidation_reasons.append("Color distribution lacks typical retinal hemoglobin absorption spectrum.")
        
    # Check peripheral corners vs central illumination
    cw, ch = max(2, int(width * 0.08)), max(2, int(height * 0.08))
    corner_patches = [
        gray[:ch, :cw],
        gray[:ch, -cw:],
        gray[-ch:, :cw],
        gray[-ch:, -cw:]
    ]
    corner_mean = float(np.mean([np.mean(patch) for patch in corner_patches]))
    center_region = gray[int(height * 0.3):int(height * 0.7), int(width * 0.3):int(width * 0.7)]
    center_mean = float(np.mean(center_region)) if center_region.size > 0 else brightness
    
    if corner_mean > 60.0 and corner_mean > (center_mean * 0.85):
        if b_mean > (r_mean * 0.50) or corner_mean > 160.0:
            is_fundus_structure = False
            fundus_invalidation_reasons.append("Image lacks circular field-of-view (FOV) aperture and dark camera boundaries.")

    # Check foreground texture & vascular gradient (retinas have continuous vascular variance; cartoons/flat graphics have near zero)
    fg_mask = gray > 18
    if np.any(fg_mask):
        fg_std = float(np.std(gray[fg_mask]))
        sobel_g = cv2.Sobel(img_np[:, :, 1], cv2.CV_64F, 1, 1, ksize=3)
        fg_grad = float(np.std(sobel_g[fg_mask]))
        
        # Flat cartoon or synthetic graphic
        if fg_std < 6.0 and fg_grad < 6.0:
            is_fundus_structure = False
            fundus_invalidation_reasons.append(f"Image exhibits flat artificial graphics without retinal vascular texture.")
    else:
        is_fundus_structure = False
        fundus_invalidation_reasons.append("Image contains no discernible foreground retinal structure.")

    # If it fails the fundus structure checks, classify as INVALID (Non-retinal image)
    if not is_fundus_structure:
        return QualityResult(
            width=width,
            height=height,
            brightness=brightness,
            contrast=contrast,
            blur_score=blur_score,
            status="INVALID",
            reasons=fundus_invalidation_reasons
        )

    # 3. Technical Quality Checks (For confirmed fundus images)
    if brightness < settings.MIN_BRIGHTNESS:
        reasons.append(f"Image is severely underexposed or dark (brightness: {brightness:.1f} < {settings.MIN_BRIGHTNESS}).")
    elif brightness > settings.MAX_BRIGHTNESS:
        reasons.append(f"Image is severely overexposed or washed out (brightness: {brightness:.1f} > {settings.MAX_BRIGHTNESS}).")
        
    if contrast < settings.MIN_CONTRAST:
        reasons.append(f"Image has insufficient contrast (contrast: {contrast:.1f} < {settings.MIN_CONTRAST}).")
        
    if blur_score < settings.MIN_BLUR_SCORE:
        reasons.append(f"Image is excessively blurry or out of focus (blur score: {blur_score:.1f} < {settings.MIN_BLUR_SCORE}).")

    status = "LOW_QUALITY" if len(reasons) > 0 else "ACCEPT"

    return QualityResult(
        width=width,
        height=height,
        brightness=round(brightness, 2),
        contrast=round(contrast, 2),
        blur_score=round(blur_score, 2),
        status=status,
        reasons=reasons
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

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import cv2
import numpy as np

from app.services.quality_service import QualityAssessment, quality_service

@dataclass
class EnhancementResult:
    """
    Structured outcome of the Phase 4 borderline enhancement stage.
    """
    applied: bool
    accepted: bool
    method: str
    original_quality_score: float
    enhanced_quality_score: float
    improvement: float
    original_image_preserved: bool
    image_rgb: np.ndarray
    operations: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "applied": self.applied,
            "accepted": self.accepted,
            "method": self.method,
            "original_quality_score": round(float(self.original_quality_score), 3),
            "enhanced_quality_score": round(float(self.enhanced_quality_score), 3),
            "improvement": round(float(self.improvement), 3),
            "original_image_preserved": self.original_image_preserved,
            "operations": self.operations,
            "reasons": self.reasons
        }

class FundusEnhancer:
    """
    Phase 4: Borderline Fundus Enhancement and Safety Verification.
    
    Operates strictly and exclusively on technically BORDERLINE fundus images.
    Enhancement is an optional, signal-preserving transformation using classical
    deterministic image processing (LAB space, conservative CLAHE on luminance,
    mild illumination normalization).
    
    Safety rule:
      Enhancement is accepted ONLY if post-enhancement quality assessment
      demonstrates quality preservation or improvement without introducing
      corneal glare or artificial structures. If quality degrades, the enhancer
      strictly reverts to the untouched original image.
    """

    def __init__(self, clahe_clip_limit: float = 2.0, clahe_tile_grid: tuple = (8, 8)):
        self.clahe_clip_limit = clahe_clip_limit
        self.clahe_tile_grid = clahe_tile_grid

    def enhance(self, image_rgb: np.ndarray, quality: QualityAssessment) -> EnhancementResult:
        if image_rgb is None or image_rgb.size == 0:
            raise ValueError("Input image array is empty or None.")

        # STRICT GUARD: Enhancement operates ONLY on BORDERLINE images.
        # GOOD images bypass enhancement. UNGRADEABLE / INVALID images bypass enhancement.
        if quality.status != "BORDERLINE":
            return EnhancementResult(
                applied=False,
                accepted=False,
                method="BYPASS_NON_BORDERLINE",
                original_quality_score=quality.score,
                enhanced_quality_score=quality.score,
                improvement=0.0,
                original_image_preserved=True,
                image_rgb=image_rgb,  # Untouched reference
                operations=[],
                reasons=[f"Enhancement bypassed: image quality status is {quality.status} (only BORDERLINE images are eligible)."]
            )

        # STEP 1: Preserve original image explicitly (independent copy)
        original_rgb = image_rgb.copy()
        candidate_rgb = image_rgb.copy()
        operations_applied: List[str] = []

        # STEP 2 & 3: LAB Color Space & Conservative CLAHE on Luminance (L channel)
        lab = cv2.cvtColor(candidate_rgb, cv2.COLOR_RGB2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=self.clahe_clip_limit, tileGridSize=self.clahe_tile_grid)
        enhanced_l = clahe.apply(l_channel)
        operations_applied.append(f"lab_clahe(clip={self.clahe_clip_limit},grid={self.clahe_tile_grid[0]}x{self.clahe_tile_grid[1]})")

        # STEP 4: Mild Illumination Normalization (if illumination/contrast is suboptimal)
        if quality.illumination.status in ("BORDERLINE", "POOR") or quality.contrast.status in ("BORDERLINE", "POOR"):
            enhanced_l = self._normalize_illumination(enhanced_l)
            operations_applied.append("mild_illumination_normalization")

        # Recombine enhanced L channel with original A and B channels (preserves retinal color spectrum)
        enhanced_lab = cv2.merge([enhanced_l, a_channel, b_channel])
        candidate_rgb = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)

        # STEP 6: Safety Verification
        # Re-run Phase 3 quality assessment on candidate
        enhanced_quality = quality_service.assess(candidate_rgb)
        score_diff = enhanced_quality.score - quality.score

        is_safe, safety_reasons = self._verify_safety(quality, enhanced_quality)

        if is_safe and (score_diff >= -0.01):
            return EnhancementResult(
                applied=True,
                accepted=True,
                method="LAB_CLAHE_ILLUMINATION_NORMALIZATION",
                original_quality_score=quality.score,
                enhanced_quality_score=enhanced_quality.score,
                improvement=score_diff,
                original_image_preserved=True,
                image_rgb=candidate_rgb,
                operations=operations_applied,
                reasons=[f"Enhancement accepted: quality score improved by {score_diff:+.3f} (from {quality.score:.3f} to {enhanced_quality.score:.3f})."]
            )
        else:
            return EnhancementResult(
                applied=True,
                accepted=False,
                method="REVERTED_TO_ORIGINAL",
                original_quality_score=quality.score,
                enhanced_quality_score=enhanced_quality.score,
                improvement=score_diff,
                original_image_preserved=True,
                image_rgb=original_rgb,  # Strictly revert to untouched original
                operations=operations_applied,
                reasons=[
                    f"Enhancement candidate rejected: safety check failed or score degraded ({score_diff:+.3f}). Reverted to original image."
                ] + safety_reasons
            )

    def _normalize_illumination(self, l_channel: np.ndarray) -> np.ndarray:
        """
        Estimates low-frequency background illumination via large Gaussian kernel
        and applies mild additive normalization without sharpening noise.
        """
        # Low frequency illumination profile
        h, w = l_channel.shape
        ksize = (max(31, (w // 16) | 1), max(31, (h // 16) | 1))
        bg_estimate = cv2.GaussianBlur(l_channel, ksize, 0)
        
        # Additive normalization around local mean
        fg_mask = l_channel > 15
        mean_lum = float(np.mean(l_channel[fg_mask])) if np.any(fg_mask) else 128.0
        
        diff = l_channel.astype(np.float32) - bg_estimate.astype(np.float32)
        normalized = np.clip(mean_lum + diff * 0.75, 0, 255).astype(np.uint8)
        
        # Retain original dark camera border
        normalized[~fg_mask] = l_channel[~fg_mask]
        return normalized

    def _verify_safety(self, original_q: QualityAssessment, enhanced_q: QualityAssessment) -> tuple:
        reasons = []

        # Rule 1: Must not introduce new severe glare
        if enhanced_q.glare.status == "POOR" and original_q.glare.status != "POOR":
            reasons.append("Enhancement introduced unacceptable corneal glare or highlight saturation.")
            return False, reasons

        # Rule 2: Must not degrade an already acceptable FOV
        if enhanced_q.field_of_view.status == "POOR" and original_q.field_of_view.status != "POOR":
            reasons.append("Enhancement corrupted retinal field of view geometry.")
            return False, reasons

        # Rule 3: Must not cause overall status to become UNGRADEABLE if it was BORDERLINE
        if enhanced_q.status == "UNGRADEABLE" and original_q.status == "BORDERLINE":
            reasons.append("Enhancement caused overall quality to deteriorate into UNGRADEABLE.")
            return False, reasons

        return True, reasons

fundus_enhancer = FundusEnhancer()

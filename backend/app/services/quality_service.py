from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import cv2
import numpy as np
from app.core.config import settings

@dataclass
class MetricResult:
    name: str
    status: str  # "GOOD" | "BORDERLINE" | "POOR"
    value: float
    threshold_good: float
    threshold_borderline: float
    message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "value": round(float(self.value), 2),
            "threshold_good": round(float(self.threshold_good), 2),
            "threshold_borderline": round(float(self.threshold_borderline), 2),
            "message": self.message
        }

@dataclass
class QualityAssessment:
    status: str  # "GOOD" | "BORDERLINE" | "UNGRADEABLE"
    grade: str   # "GOOD" | "ACCEPTABLE" | "POOR"
    score: float # [0.0, 1.0]
    focus: MetricResult
    illumination: MetricResult
    contrast: MetricResult
    field_of_view: MetricResult
    glare: MetricResult
    reasons: List[str] = field(default_factory=list)
    recapture_guidance: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "grade": self.grade,
            "score": round(float(self.score), 3),
            "focus": self.focus.to_dict(),
            "illumination": self.illumination.to_dict(),
            "contrast": self.contrast.to_dict(),
            "field_of_view": self.field_of_view.to_dict(),
            "glare": self.glare.to_dict(),
            "reasons": self.reasons,
            "recapture_guidance": self.recapture_guidance
        }

class QualityService:
    """
    Phase 3: Complete Image-Quality Assessment Service.
    Determines whether an accepted retinal fundus photograph is sufficiently
    gradeable for diagnostic screening before expensive deep learning inference.
    
    Status states:
      - GOOD: High technical fidelity. Proceeds directly to model inference.
      - BORDERLINE: Recoverable technical artifacts. Eligible for safe Phase 4 enhancement.
      - UNGRADEABLE: Clinically insufficient quality. Halts pipeline immediately and returns
                     recapture guidance with zero inference calls.
    """

    def assess(self, image_rgb: np.ndarray, fov_gate_score: float = 1.0) -> QualityAssessment:
        if image_rgb is None or image_rgb.size == 0:
            raise ValueError("Input image array is empty or None.")

        h, w = image_rgb.shape[:2]
        gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
        fg_mask = gray > 15
        if not np.any(fg_mask):
            fg_mask = np.ones_like(gray, dtype=bool)

        fg_gray = gray[fg_mask]

        # 1. Focus Metric (Laplacian variance on retinal area)
        focus = self._focus_score(gray, fg_mask)

        # 2. Illumination Metric (Mean foreground luminance and distribution)
        illumination = self._illumination_score(fg_gray)

        # 3. Glare Metric (Saturated highlight pixel ratio)
        glare = self._glare_score(fg_gray)

        # 4. Contrast Metric (Robust dynamic range spread P95 - P5)
        contrast = self._contrast_score(fg_gray)

        # 5. Field of View Metric (Usable retinal coverage ratio)
        fov = self._fov_score(fg_mask, (h, w), fov_gate_score)

        # Aggregate overall status, clinical grade, and normalized quality score
        status, grade, score, reasons = self._aggregate_status(focus, illumination, contrast, fov, glare)

        # Generate deterministic, actionable recapture guidance
        guidance = self._build_recapture_guidance(focus, illumination, contrast, fov, glare)

        return QualityAssessment(
            status=status,
            grade=grade,
            score=score,
            focus=focus,
            illumination=illumination,
            contrast=contrast,
            field_of_view=fov,
            glare=glare,
            reasons=reasons,
            recapture_guidance=guidance
        )

    def _focus_score(self, gray: np.ndarray, fg_mask: np.ndarray) -> MetricResult:
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        t_good = settings.QUALITY_FOCUS_GOOD_MIN
        t_border = settings.QUALITY_FOCUS_BORDERLINE_MIN

        if laplacian_var >= t_good:
            status = "GOOD"
            msg = None
        elif laplacian_var >= t_border:
            status = "BORDERLINE"
            msg = f"Mild image blur detected (focus score: {laplacian_var:.1f}). Fine vascular arcades may be degraded."
        else:
            status = "POOR"
            msg = f"Excessive image blur or loss of focus (focus score: {laplacian_var:.1f} < {t_border}). Optic disc margin and microvasculature are ungradeable."

        return MetricResult(
            name="focus",
            status=status,
            value=laplacian_var,
            threshold_good=t_good,
            threshold_borderline=t_border,
            message=msg
        )

    def _illumination_score(self, fg_gray: np.ndarray) -> MetricResult:
        mean_lum = float(np.mean(fg_gray))
        lum_min_good = settings.QUALITY_LUMINANCE_MIN_GOOD
        lum_max_good = settings.QUALITY_LUMINANCE_MAX_GOOD
        lum_min_border = settings.QUALITY_LUMINANCE_MIN_BORDERLINE
        lum_max_border = settings.QUALITY_LUMINANCE_MAX_BORDERLINE

        if lum_min_good <= mean_lum <= lum_max_good:
            status = "GOOD"
            msg = None
        elif (lum_min_border <= mean_lum < lum_min_good) or (lum_max_good < mean_lum <= lum_max_border):
            status = "BORDERLINE"
            if mean_lum < lum_min_good:
                msg = f"Suboptimal illumination: underexposed (luminance: {mean_lum:.1f} < {lum_min_good})."
            else:
                msg = f"Suboptimal illumination: slightly overexposed (luminance: {mean_lum:.1f} > {lum_max_good})."
        else:
            status = "POOR"
            if mean_lum < lum_min_border:
                msg = f"Severely underexposed or dark (luminance: {mean_lum:.1f} < {lum_min_border}). Retinal landmarks cannot be discerned."
            else:
                msg = f"Severely overexposed or washed out (luminance: {mean_lum:.1f} > {lum_max_border}). Sensor clipping obscures retinal background."

        return MetricResult(
            name="illumination",
            status=status,
            value=mean_lum,
            threshold_good=lum_min_good,
            threshold_borderline=lum_min_border,
            message=msg
        )

    def _glare_score(self, fg_gray: np.ndarray) -> MetricResult:
        glare_ratio = float(np.count_nonzero(fg_gray > 240)) / float(max(1, len(fg_gray)))
        t_good = settings.QUALITY_GLARE_MAX_GOOD
        t_border = settings.QUALITY_GLARE_MAX_BORDERLINE

        if glare_ratio <= t_good:
            status = "GOOD"
            msg = None
        elif glare_ratio <= t_border:
            status = "BORDERLINE"
            msg = f"Minor corneal glare or reflection present (glare ratio: {glare_ratio:.1%})."
        else:
            status = "POOR"
            msg = f"Distracting corneal light reflection or flash glare artifact covering {glare_ratio:.1%} of retinal field."

        return MetricResult(
            name="glare",
            status=status,
            value=glare_ratio,
            threshold_good=t_good,
            threshold_borderline=t_border,
            message=msg
        )

    def _contrast_score(self, fg_gray: np.ndarray) -> MetricResult:
        p95 = np.percentile(fg_gray, 95)
        p5 = np.percentile(fg_gray, 5)
        spread = float(p95 - p5)
        t_good = settings.QUALITY_CONTRAST_GOOD_MIN
        t_border = settings.QUALITY_CONTRAST_BORDERLINE_MIN

        if spread >= t_good:
            status = "GOOD"
            msg = None
        elif spread >= t_border:
            status = "BORDERLINE"
            msg = f"Low dynamic range contrast (contrast spread: {spread:.1f}). Subtle microaneurysms may have reduced visibility."
        else:
            status = "POOR"
            msg = f"Severely deficient contrast (contrast spread: {spread:.1f} < {t_border}). Flat image prevents diagnostic evaluation."

        return MetricResult(
            name="contrast",
            status=status,
            value=spread,
            threshold_good=t_good,
            threshold_borderline=t_border,
            message=msg
        )

    def _fov_score(self, fg_mask: np.ndarray, dims: tuple, fov_gate_score: float) -> MetricResult:
        h, w = dims
        area_ratio = float(np.count_nonzero(fg_mask)) / float(max(1, h * w))
        effective_fov = min(area_ratio, fov_gate_score)
        t_good = settings.QUALITY_FOV_MIN_GOOD
        t_border = settings.QUALITY_FOV_MIN_BORDERLINE

        if effective_fov >= t_good:
            status = "GOOD"
            msg = None
        elif effective_fov >= t_border:
            status = "BORDERLINE"
            msg = f"Partially restricted field of view (FOV ratio: {effective_fov:.1%})."
        else:
            status = "POOR"
            msg = f"Inadequate retinal field-of-view (FOV ratio: {effective_fov:.1%} < {t_border:.0%}). Insufficient retinal area visible."

        return MetricResult(
            name="field_of_view",
            status=status,
            value=effective_fov,
            threshold_good=t_good,
            threshold_borderline=t_border,
            message=msg
        )

    def _aggregate_status(self, focus: MetricResult, illumination: MetricResult,
                          contrast: MetricResult, fov: MetricResult,
                          glare: MetricResult) -> tuple:
        reasons = []
        metrics = [focus, illumination, glare, contrast, fov]

        for m in metrics:
            if m.message:
                reasons.append(m.message)

        # Critical failure leading to ungradeable capture
        if any(m.status == "POOR" for m in metrics):
            status = "UNGRADEABLE"
            grade = "POOR"
        elif any(m.status == "BORDERLINE" for m in metrics):
            status = "BORDERLINE"
            grade = "ACCEPTABLE"
        else:
            status = "GOOD"
            grade = "GOOD"

        # Compute continuous quality score [0.0, 1.0]
        focus_norm = min(1.0, focus.value / 100.0)
        illum_norm = 1.0 - min(1.0, abs(illumination.value - 110.0) / 100.0)
        contrast_norm = min(1.0, contrast.value / 80.0)
        glare_penalty = max(0.0, 1.0 - glare.value * 5.0)
        fov_norm = min(1.0, fov.value / 0.65)

        composite_score = float(
            focus_norm * 0.35 +
            illum_norm * 0.25 +
            contrast_norm * 0.20 +
            fov_norm * 0.10 +
            glare_penalty * 0.10
        )
        composite_score = max(0.0, min(1.0, composite_score))

        return status, grade, composite_score, reasons

    def _build_recapture_guidance(self, focus: MetricResult, illumination: MetricResult,
                                 contrast: MetricResult, fov: MetricResult,
                                 glare: MetricResult) -> List[str]:
        guidance = []

        if focus.status in ("POOR", "BORDERLINE"):
            guidance.append(
                "Stabilize patient head on chin rest, verify autofocus lock on retinal vascular arcade, and ask patient to blink before capture."
            )

        if illumination.status in ("POOR", "BORDERLINE"):
            if illumination.value < settings.QUALITY_LUMINANCE_MIN_GOOD:
                guidance.append(
                    "Increase flash illumination intensity and ensure adequate pupil dilation (minimum 4mm for non-mydriatic cameras)."
                )
            else:
                guidance.append(
                    "Decrease camera illumination/flash level to prevent oversaturation and washout of background retinal pigment."
                )

        if glare.status in ("POOR", "BORDERLINE"):
            guidance.append(
                "Adjust fundus camera angle and align optical axis to eliminate anterior segment corneal light reflections."
            )

        if contrast.status in ("POOR", "BORDERLINE"):
            guidance.append(
                "Clean camera objective lens to remove dust or smudges and check for media opacities (e.g. dense cataract)."
            )

        if fov.status in ("POOR", "BORDERLINE"):
            guidance.append(
                "Instruct patient to focus on internal green fixation cross to properly center the 45-degree field of view across macula and optic disc."
            )

        return guidance

quality_service = QualityService()

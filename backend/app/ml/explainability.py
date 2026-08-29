from typing import Tuple

CLASS_EXPLANATIONS = {
    0: "AI screening indicates no detectable diabetic retinopathy pattern in the submitted retinal fundus image.",
    1: "AI screening indicates features associated with mild diabetic retinopathy (such as isolated microaneurysms).",
    2: "AI screening indicates features associated with moderate diabetic retinopathy (such as multiple microaneurysms, dot-and-blot hemorrhages, or hard exudates).",
    3: "AI screening indicates features associated with severe diabetic retinopathy (such as extensive intraretinal hemorrhages in multiple quadrants, venous beading, or microvascular abnormalities).",
    4: "AI screening indicates features associated with proliferative diabetic retinopathy (such as neovascularization or preretinal/vitreous hemorrhage patterns)."
}

REFERABLE_RECOMMENDATIONS = {
    True: "Screening recommendation: Referable DR detected. Follow-up clinical evaluation by an ophthalmologist or certified eye-care professional is recommended in accordance with standard diabetic eye screening protocols.",
    False: "Screening recommendation: Non-referable DR. Routine periodic surveillance and annual diabetic eye screening are advised as per clinical screening guidelines."
}

def generate_explanation(class_id: int, is_referable: bool, confidence: float) -> Tuple[str, str]:
    """
    Generates human-readable clinical screening explanation and referral recommendation.
    Uses non-diagnostic, screening-focused terminology.
    """
    base_explanation = CLASS_EXPLANATIONS.get(
        class_id,
        "AI screening indicates detected retinal fundus morphological patterns."
    )
    
    recommendation = REFERABLE_RECOMMENDATIONS.get(
        is_referable,
        "Follow-up examination with a qualified eye-care provider is advised."
    )
    
    return base_explanation, recommendation

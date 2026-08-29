from typing import Dict, Any
import numpy as np
import torch
import torch.nn as nn
from app.core.config import settings

def run_inference(
    model: nn.Module,
    input_tensor: torch.Tensor,
    device: torch.device
) -> Dict[str, Any]:
    """
    Executes deterministic inference on the preprocessed retinal fundus tensor.
    Returns predicted class, confidence, referable risk metrics, and softmax distribution.
    """
    model.eval()
    tensor = input_tensor.to(device)
    
    with torch.inference_mode():
        logits = model(tensor)
        probabilities = torch.softmax(logits, dim=1).squeeze(0).cpu().numpy()
        
    predicted_class_id = int(np.argmax(probabilities))
    confidence = float(probabilities[predicted_class_id])
    
    # Referable DR is defined as class >= 1 (Mild, Moderate, Severe, Proliferative)
    # Sum probabilities of classes 1, 2, 3, 4
    referable_probability = float(np.sum(probabilities[1:]))
    is_referable = bool(referable_probability >= settings.REFERABLE_THRESHOLD)
    
    probabilities_dict = {
        settings.CLASS_MAPPING[i]: float(probabilities[i])
        for i in range(len(settings.CLASS_MAPPING))
    }
    
    return {
        "class_id": predicted_class_id,
        "class_name": settings.CLASS_MAPPING[predicted_class_id],
        "confidence": confidence,
        "referable_probability": referable_probability,
        "is_referable": is_referable,
        "threshold": settings.REFERABLE_THRESHOLD,
        "probabilities": probabilities_dict,
        "raw_probabilities": probabilities
    }

import sys
import os
from pathlib import Path
import numpy as np
import torch

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.ml.model import model_manager
from app.ml.inference import run_inference
from app.ml.preprocessing import preprocess_fundus
from app.ml.gradcam import GradCAM

def create_synthetic_fundus() -> np.ndarray:
    """Generates a synthetic circular fundus test image for verification."""
    img = np.zeros((512, 512, 3), dtype=np.uint8)
    center = (256, 256)
    radius = 220
    # Orange-red retinal background
    import cv2
    cv2.circle(img, center, radius, (190, 80, 20), -1)
    # Optic disc (yellowish circle)
    cv2.circle(img, (180, 256), 35, (230, 210, 100), -1)
    # Blood vessels (dark red curves)
    cv2.line(img, (180, 256), (320, 160), (100, 20, 10), 3)
    cv2.line(img, (180, 256), (340, 360), (100, 20, 10), 3)
    return img

def main():
    print("=" * 60)
    print("EXPLAINABLE DR SCREENING - MODEL & GRAD-CAM VERIFICATION")
    print("=" * 60)
    
    # 1. Model Loading
    print("\n[Step 1] Loading EfficientNet-B3 Checkpoint...")
    try:
        model_manager.load_model()
        model = model_manager.get_model()
        device = model_manager.device
        target_layer = model_manager.get_gradcam_layer()
        print(f"  Architecture: EfficientNet-B3 (5 classes)")
        print(f"  Device: {device}")
        print(f"  Target Layer: {type(target_layer).__name__}")
        print(f"  Checkpoint Metadata: {model_manager.metadata}")
        print("  --> MODEL LOAD: PASS")
    except Exception as e:
        print(f"  --> MODEL LOAD: FAIL ({e})")
        sys.exit(1)

    # 2. Preprocessing & Inference
    print("\n[Step 2] Testing Preprocessing & Forward Inference...")
    try:
        sample_img = create_synthetic_fundus()
        tensor, preprocessed_rgb_380 = preprocess_fundus(sample_img)
        print(f"  Input Tensor Shape: {tensor.shape}")
        print(f"  Preprocessed Image Shape: {preprocessed_rgb_380.shape}")
        
        result = run_inference(model, tensor, device)
        print("\n  Softmax Class Probabilities:")
        for cls_name, prob in result["probabilities"].items():
            print(f"    - {cls_name:18s}: {prob * 100:6.2f}%")
            
        prob_sum = sum(result["probabilities"].values())
        print(f"\n  Sum of Probabilities: {prob_sum:.4f}")
        print(f"  Predicted DR Grade   : {result['class_name']} (Class {result['class_id']})")
        print(f"  Confidence           : {result['confidence'] * 100:.2f}%")
        print(f"  Referable DR Prob    : {result['referable_probability'] * 100:.2f}%")
        print(f"  Is Referable (>=0.13): {result['is_referable']}")
        
        assert 0 <= result["class_id"] <= 4, "Predicted class ID out of bounds [0..4]"
        assert abs(prob_sum - 1.0) < 1e-4, "Softmax probabilities do not sum to 1.0"
        print("  --> INFERENCE: PASS")
    except Exception as e:
        print(f"  --> INFERENCE: FAIL ({e})")
        sys.exit(1)

    # 3. Grad-CAM Generation
    print("\n[Step 3] Testing Grad-CAM Heatmap & Overlay Generation...")
    try:
        gradcam = GradCAM(model, target_layer)
        colored_heatmap_rgb, overlay_rgb, raw_map = gradcam.generate_visualizations(
            input_tensor=tensor.to(device),
            original_rgb_380=preprocessed_rgb_380,
            target_class=result["class_id"],
            alpha=0.45
        )
        gradcam.remove_hooks()
        
        print(f"  Raw Heatmap Shape  : {raw_map.shape} (Range: [{raw_map.min():.2f}, {raw_map.max():.2f}])")
        print(f"  Colored Map Shape  : {colored_heatmap_rgb.shape}")
        print(f"  Overlay Shape      : {overlay_rgb.shape}")
        
        assert raw_map.shape == (380, 380), "Grad-CAM heatmap shape mismatch"
        assert colored_heatmap_rgb.shape == (380, 380, 3), "Colored heatmap shape mismatch"
        assert overlay_rgb.shape == (380, 380, 3), "Overlay image shape mismatch"
        print("  --> GRADCAM: PASS")
    except Exception as e:
        print(f"  --> GRADCAM: FAIL ({e})")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()

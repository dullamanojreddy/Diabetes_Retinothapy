import numpy as np
import torch
from PIL import Image
from app.ml.model import model_manager
from app.ml.preprocessing import preprocess_fundus
from app.ml.gradcam import GradCAM

def test_gradcam_generation():
    if not model_manager.is_loaded:
        model_manager.load_model()
        
    model = model_manager.get_model()
    target_layer = model_manager.get_gradcam_layer()
    device = model_manager.device
    
    pil_img = Image.new("RGB", (380, 380), color=(160, 75, 40))
    tensor, rgb_380 = preprocess_fundus(pil_img)
    
    gradcam = GradCAM(model, target_layer)
    colored_rgb, overlay_rgb, raw_map = gradcam.generate_visualizations(
        input_tensor=tensor.to(device),
        original_rgb_380=rgb_380,
        target_class=0,
        alpha=0.45
    )
    gradcam.remove_hooks()
    
    assert raw_map.shape == (380, 380)
    assert raw_map.min() >= 0.0
    assert raw_map.max() <= 1.0
    assert colored_rgb.shape == (380, 380, 3)
    assert overlay_rgb.shape == (380, 380, 3)

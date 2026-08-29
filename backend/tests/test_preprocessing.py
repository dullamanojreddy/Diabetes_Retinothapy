import numpy as np
import torch
from PIL import Image
from app.ml.preprocessing import crop_retina, preprocess_fundus, TARGET_SIZE

def test_crop_retina_with_black_border():
    # Create image with black borders and a central circle
    img = np.zeros((400, 400, 3), dtype=np.uint8)
    img[50:350, 50:350] = 128  # Central bright square
    
    cropped = crop_retina(img, tolerance=10)
    assert cropped.shape[0] < 400
    assert cropped.shape[1] < 400
    assert cropped.shape[0] == 300
    assert cropped.shape[1] == 300

def test_preprocess_fundus_returns_tensor_and_image():
    pil_img = Image.new("RGB", (500, 500), color=(150, 80, 50))
    tensor, rgb_380 = preprocess_fundus(pil_img)
    
    assert isinstance(tensor, torch.Tensor)
    assert tensor.shape == (1, 3, 380, 380)
    assert tensor.dtype == torch.float32
    assert isinstance(rgb_380, np.ndarray)
    assert rgb_380.shape == (380, 380, 3)
    assert rgb_380.dtype == np.uint8

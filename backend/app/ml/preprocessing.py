import cv2
import numpy as np
import torch
from PIL import Image

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
TARGET_SIZE = (380, 380)

def crop_retina(image_np: np.ndarray, tolerance: int = 10) -> np.ndarray:
    """
    Crops the circular fundus region to remove black or empty borders.
    Uses intensity thresholding to locate the retinal field of view.
    """
    if image_np.ndim == 2:
        gray = image_np
    else:
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
        
    mask = gray > tolerance
    if not np.any(mask):
        return image_np
        
    # Find bounding box of non-background region
    coords = np.argwhere(mask)
    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0) + 1
    
    # Check if bounding box is valid and reasonably sized
    h, w = gray.shape
    crop_h = y_max - y_min
    crop_w = x_max - x_min
    
    if crop_h > (0.2 * h) and crop_w > (0.2 * w):
        cropped = image_np[y_min:y_max, x_min:x_max]
        return cropped
    
    return image_np

def preprocess_fundus(image_input: Image.Image | np.ndarray) -> tuple[torch.Tensor, np.ndarray]:
    """
    Deterministic retinal fundus preprocessing pipeline:
    1. Ensure RGB format
    2. Crop retinal FOV border
    3. Resize to 380x380
    4. Normalize using ImageNet mean & standard deviation
    5. Return (torch_tensor_batch, preprocessed_rgb_numpy)
    """
    if isinstance(image_input, Image.Image):
        img_np = np.array(image_input.convert("RGB"))
    else:
        img_np = image_input.copy()
        if img_np.ndim == 2:
            img_np = cv2.cvtColor(img_np, cv2.COLOR_GRAY2RGB)
        elif img_np.shape[2] == 4:
            img_np = cv2.cvtColor(img_np, cv2.COLOR_RGBA2RGB)

    # 1. Crop retina FOV
    cropped_np = crop_retina(img_np)
    
    # 2. Resize to 380x380
    resized_np = cv2.resize(cropped_np, TARGET_SIZE, interpolation=cv2.INTER_AREA)
    
    # 3. Normalize for PyTorch model
    img_float = resized_np.astype(np.float32) / 255.0
    normalized = (img_float - IMAGENET_MEAN) / IMAGENET_STD
    
    # Transpose to (C, H, W) and add batch dimension -> (1, 3, 380, 380)
    tensor = torch.from_numpy(normalized).permute(2, 0, 1).unsqueeze(0).float()
    
    return tensor, resized_np

import io
from pathlib import Path
from PIL import Image
import numpy as np

def load_image_bytes(contents: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(contents))
        img = img.convert("RGB")
        return img
    except Exception as e:
        raise ValueError(f"Invalid or corrupted image content: {str(e)}")

def save_numpy_image(img_array: np.ndarray, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if img_array.dtype != np.uint8:
        if img_array.max() <= 1.0:
            img_array = (img_array * 255).astype(np.uint8)
        else:
            img_array = np.clip(img_array, 0, 255).astype(np.uint8)
    
    img = Image.fromarray(img_array)
    img.save(output_path, format="JPEG", quality=92)
    return output_path

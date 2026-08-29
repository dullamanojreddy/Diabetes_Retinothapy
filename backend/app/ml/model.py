import os
from pathlib import Path
from typing import Optional, Dict, Any
import torch
import torch.nn as nn
import torchvision.models as models
from app.core.config import settings
from app.core.logging_config import logger

def build_efficientnet_b3(num_classes: int = 5) -> nn.Module:
    """
    Constructs the EfficientNet-B3 model with a 5-class linear output head
    matching the trained model architecture.
    """
    model = models.efficientnet_b3(weights=None)
    in_features = model.classifier[1].in_features  # 1536
    model.classifier[1] = nn.Linear(in_features, num_classes)
    return model

class ModelManager:
    """
    Singleton manager for loading and serving the trained EfficientNet-B3 model.
    Loads once on startup and keeps the model in memory.
    """
    _instance: Optional["ModelManager"] = None
    
    def __new__(cls) -> "ModelManager":
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.device = None
            cls._instance.target_layer = None
            cls._instance.is_loaded = False
            cls._instance.metadata = {}
        return cls._instance

    def get_device(self, requested_device: str = "auto") -> torch.device:
        if requested_device == "auto":
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        return torch.device(requested_device)

    def load_model(self, model_path: Optional[str | Path] = None, device_str: Optional[str] = None) -> None:
        path = Path(model_path) if model_path else settings.absolute_model_path
        dev = self.get_device(device_str or settings.DEVICE)
        self.device = dev
        
        logger.info(f"Initializing EfficientNet-B3 on device: {self.device}")
        model = build_efficientnet_b3(num_classes=5)
        
        if path.exists():
            logger.info(f"Loading checkpoint from: {path}")
            try:
                checkpoint = torch.load(str(path), map_location=self.device)
                if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                    state_dict = checkpoint["model_state_dict"]
                    self.metadata = {
                        "epoch": checkpoint.get("epoch"),
                        "val_macro_f1": checkpoint.get("val_macro_f1"),
                        "val_loss": checkpoint.get("val_loss"),
                    }
                    logger.info(f"Checkpoint metadata: {self.metadata}")
                elif isinstance(checkpoint, dict) and "state_dict" in checkpoint:
                    state_dict = checkpoint["state_dict"]
                elif isinstance(checkpoint, dict):
                    state_dict = checkpoint
                else:
                    state_dict = checkpoint
                
                # Strip possible 'module.' prefix from DataParallel training
                clean_state_dict = {}
                for k, v in state_dict.items():
                    key = k.replace("module.", "")
                    clean_state_dict[key] = v
                    
                model.load_state_dict(clean_state_dict, strict=True)
                logger.info("Successfully loaded model state dict with strict=True.")
            except Exception as e:
                logger.error(f"Error loading checkpoint state dict: {e}")
                raise e
        else:
            logger.warning(f"Checkpoint not found at {path}. Model initialized with default weights for dev/testing.")
            
        model.to(self.device)
        model.eval()
        
        self.model = model
        self.target_layer = model.features[-1]
        self.is_loaded = True
        logger.info(f"ModelManager ready. Target Grad-CAM layer: {type(self.target_layer).__name__}")

    def get_model(self) -> nn.Module:
        if self.model is None or not self.is_loaded:
            raise RuntimeError("Model has not been initialized. Call load_model() first.")
        return self.model

    def get_gradcam_layer(self) -> nn.Module:
        if self.target_layer is None:
            raise RuntimeError("Target layer not available. Call load_model() first.")
        return self.target_layer

model_manager = ModelManager()

import cv2
import numpy as np
import torch
import torch.nn as nn
from typing import Optional, Tuple

class GradCAM:
    """
    Grad-CAM (Gradient-weighted Class Activation Mapping) implementation for
    generating transparent visual explainability heatmaps from convolutional feature layers.
    """
    def __init__(self, model: nn.Module, target_layer: nn.Module):
        self.model = model
        self.target_layer = target_layer
        self.activations: Optional[torch.Tensor] = None
        self.gradients: Optional[torch.Tensor] = None
        self.hooks = []
        self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output

        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0]

        self.hooks.append(self.target_layer.register_forward_hook(forward_hook))
        self.hooks.append(self.target_layer.register_full_backward_hook(backward_hook))

    def generate_heatmap(
        self,
        input_tensor: torch.Tensor,
        target_class: Optional[int] = None
    ) -> np.ndarray:
        """
        Computes the Grad-CAM activation heatmap for the given input tensor and target class.
        Returns a 2D float numpy array with values in [0, 1].
        """
        self.model.eval()
        
        # Ensure gradients are tracked for this forward/backward pass
        tensor = input_tensor.clone().requires_grad_(True)
        
        output = self.model(tensor)
        
        if target_class is None:
            target_class = int(output.argmax(dim=1).item())
            
        self.model.zero_grad()
        score = output[0, target_class]
        score.backward(retain_graph=True)
        
        if self.gradients is None or self.activations is None:
            raise RuntimeError("Grad-CAM hooks failed to capture gradients or activations.")
            
        # Global Average Pooling of gradients across spatial dimensions (H, W)
        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)  # (1, C, 1, 1)
        
        # Weighted combination of forward activation maps
        cam = torch.sum(weights * self.activations, dim=1, keepdim=True)  # (1, 1, H, W)
        
        # Apply ReLU to retain only positive influences
        cam = torch.relu(cam)
        
        cam_np = cam.squeeze().detach().cpu().numpy()
        
        # Min-max normalization
        cam_min, cam_max = cam_np.min(), cam_np.max()
        if cam_max > cam_min:
            cam_np = (cam_np - cam_min) / (cam_max - cam_min)
        else:
            cam_np = np.zeros_like(cam_np)
            
        return cam_np

    def generate_visualizations(
        self,
        input_tensor: torch.Tensor,
        original_rgb_380: np.ndarray,
        target_class: Optional[int] = None,
        alpha: float = 0.45
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generates:
        1. Colored heatmap RGB (380, 380, 3)
        2. Blended overlay RGB (380, 380, 3)
        3. Raw 2D normalized heatmap (380, 380)
        """
        raw_heatmap = self.generate_heatmap(input_tensor, target_class=target_class)
        
        # Resize heatmap to 380x380 matching image dimensions
        h, w = original_rgb_380.shape[:2]
        resized_heatmap = cv2.resize(raw_heatmap, (w, h), interpolation=cv2.INTER_LINEAR)
        
        # Convert to 8-bit image for colormap
        uint8_map = np.uint8(255 * resized_heatmap)
        colored_bgr = cv2.applyColorMap(uint8_map, cv2.COLORMAP_JET)
        colored_rgb = cv2.cvtColor(colored_bgr, cv2.COLOR_BGR2RGB)
        
        # Alpha blend with original fundus image
        overlay_rgb = np.uint8(alpha * colored_rgb + (1.0 - alpha) * original_rgb_380)
        
        return colored_rgb, overlay_rgb, resized_heatmap

    def remove_hooks(self):
        for hook in self.hooks:
            hook.remove()
        self.hooks = []

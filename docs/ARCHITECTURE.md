# System Architecture - Explainable DR Screening

## High-Level Architecture Overview

The Explainable DR Screening platform is structured into two decoupled tiers communicating over REST APIs:

1. **Frontend Layer**: A React 18 single-page application built with TypeScript, Vite, and Tailwind CSS.
2. **Backend ML & API Layer**: A FastAPI asynchronous service integrating PyTorch, Torchvision, OpenCV, and SQLite for persistence.

```
                    ┌─────────────────────────┐
                    │    Web Browser Client   │
                    │ (React / TS / Tailwind) │
                    └────────────┬────────────┘
                                 │
                                 │ HTTP POST /api/predict (multipart)
                                 │ HTTP GET  /api/health
                                 │ HTTP GET  /api/history
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     FastAPI Gateway     │
                    │ (Lifespan / CORS / Auth)│
                    └────────────┬────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
          ▼                      ▼                      ▼
  ┌───────────────┐      ┌───────────────┐      ┌───────────────┐
  │ Preprocessing │      │ Model Manager │      │   Grad-CAM    │
  │ (Retina Crop  │      │(EfficientNet) │      │ (features[-1] │
  │  & Normalise) │      │  Checkpoint   │      │  Activation)  │
  └───────┬───────┘      └───────┬───────┘      └───────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │    Prediction Service   │
                    │   • 5-Class Softmax     │
                    │   • Referable Risk      │
                    │   • Clinical Rationale  │
                    └────────────┬────────────┘
                                 │
                     ┌───────────┴───────────┐
                     ▼                       ▼
           ┌───────────────────┐   ┌───────────────────┐
           │   SQLite Audit    │   │  Static Artifacts │
           │   (history.db)    │   │ (Heatmap/Overlay) │
           └───────────────────┘   └───────────────────┘
```

## Component Breakdown

### 1. Model Manager (`app/ml/model.py`)
- Implements the Singleton pattern.
- Instantiates the exact EfficientNet-B3 network with custom 5-class linear output head.
- Loads state dict weights strictly from `backend/models/best_efficientnet_b3.pth`.
- Selects CUDA acceleration if available, fallback to CPU.
- Exposes `model.features[-1]` as the target feature extraction layer for Grad-CAM.

### 2. Preprocessing Pipeline (`app/ml/preprocessing.py`)
- **`crop_retina(image_np)`**: Automatic boundary detection and dark border removal.
- **`preprocess_fundus(image_input)`**: Standardizes image to $380 \times 380$ dimensions with ImageNet channel normalization.

### 3. Grad-CAM Engine (`app/ml/gradcam.py`)
- Hooks into `model.features[-1]` forward activations and backward gradients.
- Calculates channel weights via Global Average Pooling:
  $$\alpha_k^c = \frac{1}{Z} \sum_i \sum_j \frac{\partial y^c}{\partial A_{i,j}^k}$$
- Generates Class Activation Map:
  $$L_{\text{Grad-CAM}}^c = \text{ReLU}\left(\sum_k \alpha_k^c A^k\right)$$
- Colorizes using OpenCV JET colormap and computes alpha blended overlay with original fundus.

### 4. Prediction Service (`app/services/prediction_service.py`)
- Orchestrates the full lifecycle: validation $\rightarrow$ preprocessing $\rightarrow$ inference $\rightarrow$ Grad-CAM $\rightarrow$ clinical explanation text generation $\rightarrow$ database logging.
- Formats responses into validated Pydantic schemas.

### 5. Storage Layer (`backend/storage/`)
- `uploads/`: Sanitized incoming uploads.
- `results/`: Processed original images, heatmaps, and overlays.
- `history.db`: SQLite database for screening audit records.

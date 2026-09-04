# System Architecture - Explainable DR Screening

## High-Level Architecture Overview

The system is structured as a decoupled two-tier client-server application adhering strictly to the SIH-Oriented Implementation Blueprint:

1. **Frontend Layer**: React 18 single-page application built with TypeScript, Vite, and Tailwind CSS.
2. **Backend API & Gating Layer**: FastAPI asynchronous microservice orchestrating file validation, multi-signal fundus validation, technical quality checks, EfficientNet-B3 inference, Grad-CAM generation, and JSON history logging.

```text
                    ┌─────────────────────────┐
                    │    Web Browser Client   │
                    │ (React / TS / Tailwind) │
                    └────────────┬────────────┘
                                 │
                                 │ HTTP POST /api/prediction (multipart)
                                 │ HTTP GET  /api/health & /ready
                                 │ HTTP GET  /api/history
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     FastAPI Gateway     │
                    │ (Lifespan / CORS / Rts) │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     FILE VALIDATION     │
                    │  Size / Extension / MIME│
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │    IMAGE VALIDATION     │
                    │   Pillow Decode / RGB   │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │    FUNDUS IMAGE GATE    │
                    │ Multi-Signal Retinal CV │
                    └────────────┬────────────┘
                                 │ Pass
                                 ▼
                    ┌─────────────────────────┐
                    │   QUALITY ASSESSMENT    │
                    │  Blur / Exposure/ Range │
                    └────────────┬────────────┘
                                 │ Pass (ACCEPT)
                                 ▼
                    ┌─────────────────────────┐
                    │  EXISTING PREPROCESSING │
                    │   preprocess_fundus()   │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     EfficientNet-B3     │
                    │   best...epoch7.pth     │
                    └────────────┬────────────┘
                                 │
                       ┌─────────┴─────────┐
                       ▼                   ▼
                5-Class Softmax       Referable DR
                  Prediction        Threshold (0.13)
                       │                   │
                       └─────────┬─────────┘
                                 │
                                 ▼
                          ┌─────────────┐
                          │  Grad-CAM   │
                          │ features[-1]│
                          └──────┬──────┘
                                 │
                                 ▼
                          ┌─────────────┐
                          │History Store│
                          │history.json │
                          └──────┬──────┘
                                 │
                                 ▼
                         Structured Response
                                 │
                                 ▼
                          React Results UI
```

---

## Component Breakdown

### 1. Pre-Inference Safety & Validation Gates
- **`app/utils/file_utils.py`**:
  - Enforces extension allow-list (`.jpg`, `.jpeg`, `.png`), MIME type, and maximum upload size (10MB).
  - Sanitizes filenames against path traversal.
  - Creates unique temporary files with guaranteed deletion in `finally` blocks.
- **`app/utils/image_utils.py`**:
  - Safely decodes image bytes with Pillow.
  - **Phase 2 Hardened Multi-Signal Deterministic Fundus Gate**:
    Evaluates 7 independent structural and physical signals before any model execution:
    1. `aspect_ratio_score`: Aspect ratio consistency with standard retinal fundus photography (0.70 - 1.45).
    2. `fov_score`: Circular/elliptical optical aperture geometry (area ratio, circularity, camera mask).
    3. `dark_boundary_score`: Camera peripheral unilluminated optical boundary (dark corners from camera mask).
    4. `retinal_color_score`: Retinal hemoglobin absorption physics ($R > G > B$, low blue reflectance, hemoglobin absorption). Color alone NEVER classifies an image as fundus.
    5. `texture_score`: Biological macroscopic retinal luminance variance and gradient ($fg\_std > 12.0$).
    6. `edge_density_score`: Organic vascular network edge density vs synthetic/text patterns.
    7. `vessel_like_score`: Green channel CLAHE + black-hat morphological tubular vessel branching.
  - Intercepts non-retinal images (cartoons, Sun, Miss Minutes, solid orange/red backgrounds, orange circles, kettles, faces, landscapes, screenshots, text documents) before preprocessing and inference with verified zero inference calls.
  - Calculates technical quality metrics: dimensions, brightness, contrast, blur score. Distinguishes authentic blurry fundus images (`LOW_QUALITY`) from non-retinal invalid images (`INVALID_IMAGE`).

### 2. Model Manager (`app/ml/model.py`)
- Singleton pattern initializing `EfficientNet-B3` checkpoint (`best_efficientnet_b3.pth`) once on application startup.
- Centralized GPU/CPU device selection.
- Sets model to evaluation mode (`model.eval()`).
- Exposes `model.features[-1]` for Grad-CAM explainability.

### 3. Preprocessing Pipeline (`app/ml/preprocessing.py`)
- Preserved working pipeline:
  - `crop_retina()`: Removes black empty borders to center the retinal FOV.
  - `preprocess_fundus()`: Resizes to $380 \times 380$ using area interpolation, normalizes using ImageNet mean ($\mu=[0.485, 0.456, 0.406]$) and standard deviation ($\sigma=[0.229, 0.224, 0.225]$), and outputs a model-ready float tensor.

### 4. Grad-CAM Engine (`app/ml/gradcam.py`)
- Hooks into `model.features[-1]` to capture activations and backward gradients without modifying model weights.
- Generates Class Activation Maps for the predicted or requested DR grade.
- Synthesizes transparent colored heatmaps and alpha-blended overlays.

### 5. Prediction Service (`app/services/prediction_service.py`)
- Single orchestration point: file validation $\rightarrow$ fundus gate $\rightarrow$ quality checks $\rightarrow$ preprocessing $\rightarrow$ inference $\rightarrow$ referable logic $\rightarrow$ Grad-CAM $\rightarrow$ history logging $\rightarrow$ cleanup.
- Implements fail-closed behavior: returns HTTP 400 for bad files and HTTP 422 for non-retinal or low-quality images without disease prediction.

### 6. Persistence (`app/services/history_service.py`)
- Thread-safe, atomic JSON history storage in `backend/storage/history.json`.
- Stores metadata, results, and references to artifacts in `backend/storage/results/`.

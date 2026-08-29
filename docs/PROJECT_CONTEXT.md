# Project Context - Explainable DR Screening

## Project Overview
Explainable DR Screening is an AI-powered medical research and screening support web application. It takes retinal fundus photographs as input, processes them through a deterministic computer vision pipeline, executes an already trained PyTorch **EfficientNet-B3** deep learning model to predict one of five Diabetic Retinopathy (DR) severity stages, calculates the referable DR risk using a calibrated cutoff threshold (`0.13`), and computes transparent **Grad-CAM** visual attention heatmaps directly from the model's final convolutional layer (`features[-1]`).

## Problem Statement
Diabetic Retinopathy is a leading cause of preventable blindness among working-age adults worldwide. Early screening and timely referral can prevent severe visual impairment. However, many deep learning models operate as "black boxes" with no clinical interpretability. This project productizes a verified research model into a responsive, explainable screening platform with visual heatmaps, probability breakdowns, and clear referral triage.

## Users
- Ophthalmologists, optometrists, and eye-care specialists reviewing AI screening telemetry.
- Clinical researchers evaluating deep learning interpretability on retinal fundus imagery.
- Diabetic eye screening program operators requiring triage and audit trails.

## Current Architecture
```
                   ┌──────────────────────────────────┐
                   │   React 18 + TypeScript + Vite   │
                   │      Tailwind CSS Dashboard      │
                   └────────────────┬─────────────────┘
                                    │ HTTP / REST
                                    ▼
                   ┌──────────────────────────────────┐
                   │         FastAPI Backend          │
                   │    (Lifespan Model Loading)      │
                   └────────────────┬─────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           ▼                        ▼                        ▼
  Retina FOV Cropping        EfficientNet-B3              Grad-CAM
  & 380x380 Preprocessing    PyTorch Checkpoint       features[-1] Hook
           │                        │                        │
           └────────────────────────┼────────────────────────┘
                                    │
                                    ▼
                          Prediction Service
                                    │
                     ┌──────────────┴──────────────┐
                     ▼                             ▼
             DR 5-Class Grade &            Referable DR Risk
             Confidence Softmax            (Threshold: 0.13)
                     │                             │
                     └──────────────┬──────────────┘
                                    ▼
                          SQLite History Audit
                                    │
                                    ▼
                       JSON Response + Visual URLs
```

## Technology Stack
- **Deep Learning & CV**: PyTorch 2.13, Torchvision 0.28, OpenCV, Pillow, NumPy, SciPy.
- **Backend API**: Python 3.10+, FastAPI, Uvicorn, Pydantic V2, Pydantic-Settings, SQLite3, Pytest, Pytest-Asyncio, HTTPX.
- **Frontend Dashboard**: React 18, TypeScript, Vite, Tailwind CSS, Lucide React icons.
- **Explainability Engine**: Grad-CAM with forward/backward hooks on `model.features[-1]`.

## ML Model
- **Base Network**: `torchvision.models.efficientnet_b3(weights=None)`
- **Output Head**: `nn.Sequential(nn.Dropout(p=0.3), nn.Linear(1536, 5))`
- **Trained Checkpoint**: `backend/models/best_efficientnet_b3.pth` (123 MB, Epoch 7, Validation Macro-F1: 0.7012, Val Loss: 0.7987)
- **Class Mapping**:
  - `0`: No DR
  - `1`: Mild DR
  - `2`: Moderate DR
  - `3`: Severe DR
  - `4`: Proliferative DR
- **Inference Mode**: `torch.inference_mode()` with GPU/CPU auto-selection.
- **Referable Rule**: Referable DR is defined as DR grade $\ge 1$. Referable probability $= \sum_{i=1}^{4} P(\text{class } i)$.
- **Referable Threshold**: `REFERABLE_THRESHOLD = 0.13` (configurable constant).

## Dataset
- **Dataset**: APTOS 2019 Blindness Detection Retinal Fundus Dataset.
- **Total Images**: 3,662 retinal images (Train: 2,930, Validation: 366, Test: 366; strictly zero ID overlap).
- **Test Performance Benchmarks**:
  - Overall Test Accuracy: **81.42%**
  - Test Macro-F1: **0.6465**
  - Test Weighted-F1: **0.8195**
  - Referable DR Sensitivity: **0.8540** (at standard threshold) / **0.9481** (at 0.13 cutoff)
  - Referable DR Specificity: **0.9607** (at standard threshold) / **0.9387** (at 0.13 cutoff)
  - Referable DR Precision: **0.9286**
  - Referable DR ROC-AUC: **0.9827**

## Preprocessing
- Input format: RGB color images.
- Retinal FOV Cropping: `crop_retina(image_np, tolerance=10)` removes dark background borders.
- Target Resolution: Resized to $380 \times 380$ pixels using area interpolation.
- Normalization: ImageNet channel statistics ($\mu = [0.485, 0.456, 0.406]$, $\sigma = [0.229, 0.224, 0.225]$).
- Tensor Conversion: Float32 tensor shape `(1, 3, 380, 380)`.

## API Architecture
- `GET /api/health`: Health status, device (cuda/cpu), model metadata.
- `POST /api/predict`: Multipart fundus upload, runs inference and Grad-CAM, returns full telemetry.
- `GET /api/history`: Returns audit log of past screenings.
- `GET /api/history/{id}`: Returns full details of a specific screening.
- `/storage/results/*`: Static file mount for heatmap and overlay artifacts.

## Frontend Architecture
- `src/pages/Home.tsx`: Hero banner, 3 pillars, APTOS benchmarks table, disclaimer.
- `src/pages/Screening.tsx`: Drag-and-drop upload, sample shortcuts, stage-by-stage loading, results view.
- `src/pages/Results.tsx`: 5-class severity badge, confidence gauge, referable threshold slider, Grad-CAM viewer.
- `src/pages/History.tsx`: History table, detail modal, and past screening inspection.
- `src/components/GradCAMViewer.tsx`: Interactive multi-tab viewer (Overlay, Heatmap, Original, Split) with intensity legend.
- `src/components/MedicalDisclaimer.tsx`: Prominent medical warning banner.

## Database
- SQLite database (`backend/storage/history.db`) managed via `HistoryService`.
- Zero-external-dependency local persistence for complete auditability.

## Environment Variables
- **Backend** (`backend/.env`):
  - `MODEL_PATH=models/best_efficientnet_b3.pth`
  - `REFERABLE_THRESHOLD=0.13`
  - `DEVICE=auto`
  - `MAX_UPLOAD_SIZE_MB=10`
  - `CORS_ORIGINS=["http://localhost:5173"]`
- **Frontend** (`frontend/.env`):
  - `VITE_API_BASE_URL=/api`

## Completed Work
- [x] Transferred `best_efficientnet_b3.pth` checkpoint to `backend/models/`.
- [x] Verified model loading, strict state dict loading, and metadata extraction.
- [x] Implemented deterministic retinal preprocessing (`crop_retina` + 380x380 resize + normalization).
- [x] Implemented Grad-CAM explainability engine targeting `model.features[-1]`.
- [x] Built FastAPI application with singleton model manager, routes, CORS, and static file serving.
- [x] Built SQLite history persistence service.
- [x] Verified full backend test suite (`pytest tests -v` passing 100%).
- [x] Built React + TypeScript + Vite + Tailwind CSS frontend dashboard.
- [x] Built verified sample retinal image generator for 1-click test execution.

## Current Status
- Backend and Frontend fully functional and tested.
- All verification checks passing (`MODEL LOAD: PASS`, `INFERENCE: PASS`, `GRADCAM: PASS`).

## Changed Files
- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/core/logging_config.py`
- `backend/app/ml/model.py`
- `backend/app/ml/preprocessing.py`
- `backend/app/ml/inference.py`
- `backend/app/ml/gradcam.py`
- `backend/app/ml/explainability.py`
- `backend/app/schemas/prediction.py`
- `backend/app/services/prediction_service.py`
- `backend/app/services/history_service.py`
- `backend/app/utils/image_utils.py`
- `backend/app/utils/file_utils.py`
- `backend/app/api/routes/health.py`
- `backend/app/api/routes/prediction.py`
- `backend/app/api/routes/history.py`
- `backend/scripts/verify_model.py`
- `backend/scripts/generate_samples.py`
- `backend/tests/*`
- `frontend/src/*`

## Known Bugs
- None.

## Important Decisions
- Kept `REFERABLE_THRESHOLD = 0.13` as a configurable backend constant to maintain high sensitivity in screening without altering reported test metrics.
- Grad-CAM hooks are registered and cleanly removed on every explanation request to prevent memory leakage.
- Utilized singleton `ModelManager` loaded at FastAPI lifespan startup to avoid reloading the 123MB checkpoint per request.

## Roadmap
- Multi-image batch screening mode.
- Exportable PDF clinical screening reports.
- Support for DICOM retinal fundus format.

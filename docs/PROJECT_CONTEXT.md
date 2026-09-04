# PROJECT_CONTEXT.md - Explainable DR Screening System

## Overview
Explainable DR Screening is an AI-powered medical research and clinical screening support platform designed for early detection and triage of Diabetic Retinopathy (DR). The system accepts digital color retinal fundus photographs, executes multi-signal deterministic input and quality validation gates, processes images through an established preprocessing pipeline, runs an already trained PyTorch **EfficientNet-B3** 5-class deep learning classifier, determines referable DR triage using a calibrated cutoff threshold (`0.13`), generates transparent **Grad-CAM** visual attention heatmaps from layer `features[-1]`, persists audit records to a lightweight local JSON history index, and delivers typed telemetry to a modern React dashboard.

## Problem Statement
Diabetic Retinopathy is a leading cause of preventable blindness worldwide. While deep learning models can achieve high classification accuracy, they frequently operate as opaque "black boxes" and can produce false confidence on out-of-domain images (such as cartoon characters or solar images being forced into disease categories). This project productizes a verified research model into an end-to-end clinical screening workflow featuring deterministic pre-inference safety gates, transparent Grad-CAM heatmaps, referable risk scoring, and complete audit logging.

## Scope / Non-Goals
- **In Scope**:
  - Production engineering, safety gating, explainability, API contracts, frontend state management, test suites, and documentation.
  - Multi-signal deterministic fundus validation gate and technical quality checks.
  - Differentiated error responses (`INVALID_FILE` -> 400, `INVALID_IMAGE` -> 422, `LOW_QUALITY` -> 422 with no DR prediction).
  - Pure JSON file history persistence (`storage/history.json`).
- **Non-Goals / Out of Scope**:
  - Retraining, fine-tuning, or altering the EfficientNet-B3 model checkpoint (`best_efficientnet_b3.pth`).
  - Training a secondary neural network for retinal validation (addressed deterministically via multi-signal computer vision heuristics).
  - Database migrations or external database server dependencies.
  - Making definitive diagnostic claims (the system is explicitly a screening and decision-support tool with mandatory disclaimers).

## Current Stack
- **Machine Learning & CV**: PyTorch 2.13, Torchvision 0.28, OpenCV, Pillow, NumPy, SciPy.
- **Backend API**: Python 3.10+, FastAPI, Uvicorn, Pydantic V2, Pydantic-Settings, Pytest, Pytest-Asyncio, HTTPX.
- **Frontend Dashboard**: React 18, TypeScript, Vite, Tailwind CSS, Lucide React icons.
- **Explainability Engine**: Grad-CAM registered on `model.features[-1]`.
- **Storage**: Local filesystem (`storage/uploads/`, `storage/results/`, `storage/history.json`).

## Architecture
```text
                    ┌─────────────────────────┐
                    │  React 18 + TypeScript  │
                    │  Tailwind CSS Frontend  │
                    └────────────┬────────────┘
                                 │
                            Image Upload
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     FastAPI Backend     │
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

## ML Model
- **Model Architecture**: `torchvision.models.efficientnet_b3(weights=None)`
- **Classification Head**: `nn.Sequential(nn.Dropout(p=0.3), nn.Linear(1536, 5))`
- **Trained Checkpoint**: `backend/models/best_efficientnet_b3.pth` (123 MB, Epoch 7, Validation Macro-F1: 0.7012, Val Loss: 0.7987)
- **Class Mapping**:
  - `0`: No DR
  - `1`: Mild DR
  - `2`: Moderate DR
  - `3`: Severe DR
  - `4`: Proliferative DR
- **Inference Mode**: `torch.inference_mode()` with GPU/CPU auto-selection.
- **Referable Rule**: Referable DR is defined as DR grade $\ge 1$. Referable probability $= \sum_{i=1}^{4} P(\text{class } i)$.
- **Referable Decision Cutoff**: `REFERABLE_THRESHOLD = 0.13` (calibrated on validation split for high screening sensitivity).

## Dataset and Splits
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

## API Contracts
- `GET /api/health`: Liveness probe (`status`, `model_loaded`, `model`, `device`, `version`, `timestamp`).
- `GET /api/health/ready`: Readiness probe (`status`, `model_loaded`, `model_version`, `storage_available`, `timestamp`). Returns 503 if uninitialized.
- `POST /api/prediction` (alias: `POST /api/predict`): Multipart fundus photograph upload.
  - **Success (200)**: Conforms to Section 6 discriminated schema (`screening_id`, `status: "VALID"`, `diagnosis`, `probabilities`, `referable`, `quality`, `explainability`, `model`, `created_at`).
  - **Bad File (400)**: `status: "INVALID_FILE"`, detail message.
  - **Non-Retinal Image (422)**: `status: "INVALID_IMAGE"`, `quality: { status: "INVALID", reasons: [...] }`. No DR prediction returned.
  - **Low Quality Retinal Image (422)**: `status: "LOW_QUALITY"`, `quality: { status: "LOW_QUALITY", reasons: [...] }`. No DR prediction returned.
- `GET /api/history`: Paginated screening history.
- `GET /api/history/{screening_id}`: Detailed screening record inspection by ID.
- `/results/*` & `/storage/results/*`: Static artifact routes for Grad-CAM overlays and preprocessed images.

## Storage
- `backend/storage/uploads/`: Server-side temporary storage with guaranteed cleanup in `finally` blocks.
- `backend/storage/results/`: Grad-CAM heatmaps, overlays, and preprocessed fundus images.
- `backend/storage/samples/`: Verified sample retinal images for one-click testing.
- `backend/storage/history.json`: Thread-safe, atomic JSON history index recording valid screenings and non-prediction outcomes.

## Frontend Flow
- State machine: `IDLE` -> `FILE_SELECTED` -> `ANALYZING` -> `VALID_RESULT` / `INVALID_FILE` / `INVALID_IMAGE` / `LOW_QUALITY` / `API_ERROR`.
- `Screening.tsx`: Handles upload, drag-and-drop, sample shortcuts, loading indicator, and differentiated error states.
- `Results.tsx`: Displays 5-class severity card, referable risk gauge, probability distribution, Grad-CAM viewer, and audit summary.
- `History.tsx`: Displays paginated audit log, outcome badges, and detailed modal viewer.
- `MedicalDisclaimer.tsx`: Persistent medical research and screening assistance advisory.

## Completed Work
- [x] Multi-signal deterministic fundus image gate implemented in `image_utils.py` (color dominance, FOV aperture, dark corners, vascular texture variation).
- [x] Technical quality checks implemented (dimensions, brightness, contrast, blur score).
- [x] File and security validation implemented in `file_utils.py` (extension allow-list, size cap, zero-byte rejection, path traversal protection, cleanup).
- [x] Prediction contract updated to Section 6 discriminated schema with backward compatibility.
- [x] Differentiated HTTP 400 and HTTP 422 rejection responses returning structured JSON without disease classification.
- [x] Health readiness probe `/api/health/ready` implemented with fail-closed 503 behavior.
- [x] Pure JSON history persistence implemented in `history_service.py` (`storage/history.json`).
- [x] Acceptance test suite covering AT-01 through AT-10 passing 100% in `tests/test_prediction.py`.
- [x] Frontend types, API client, hooks, error states, and history updated and verified via `npm run build`.

## Current Status
- Backend and Frontend are fully functional, integrated, and verified.
- 15/15 pytest tests passing (`tests/test_prediction.py`, `tests/test_gradcam.py`, `tests/test_health.py`, `tests/test_preprocessing.py`).
- Frontend production build compiles cleanly (`npm run build` succeeds).

## Changed Files
- `backend/app/core/config.py`
- `backend/.env.example`
- `backend/app/utils/image_utils.py`
- `backend/app/utils/file_utils.py`
- `backend/app/schemas/prediction.py`
- `backend/app/services/history_service.py`
- `backend/app/services/prediction_service.py`
- `backend/app/api/routes/prediction.py`
- `backend/app/api/routes/health.py`
- `backend/app/api/routes/history.py`
- `backend/app/main.py`
- `backend/tests/test_prediction.py`
- `frontend/src/types/prediction.ts`
- `frontend/src/services/api.ts`
- `frontend/src/hooks/usePrediction.ts`
- `frontend/src/components/ErrorState.tsx`
- `frontend/src/components/PredictionCard.tsx`
- `frontend/src/components/ReferableRisk.tsx`
- `frontend/src/components/ScreeningSummary.tsx`
- `frontend/src/pages/Screening.tsx`
- `frontend/src/pages/Results.tsx`
- `frontend/src/pages/History.tsx`
- `frontend/src/App.tsx`
- `frontend/src/utils/formatting.ts`

## Known Bugs
- None.

## Decisions and Rationale
- **Model Freeze**: Preserved `best_efficientnet_b3.pth` and its inference pipeline to prevent performance regression on validated APTOS benchmarks.
- **Deterministic Heuristic Fundus Gate**: Avoided training a secondary model while effectively preventing non-retinal inputs (Sun, Marvel characters, photos) from receiving false DR classifications.
- **Fail-Closed Gate Behavior**: Rejection states return HTTP 422 with structured reasons and suppress DR severity predictions.
- **Pure JSON Persistence**: Adopted `storage/history.json` to eliminate database migration overhead while ensuring audit persistence.

## Test Status
- **Pytest Suite**: 15 tests collected, 15 passed in 9.35s (100% pass rate).
- **Frontend Build**: Vite + TypeScript compiled 1,488 modules cleanly with zero errors.

## Deployment Status
- Local development ready via FastAPI (`uvicorn app.main:app --port 8000`) and Vite (`npm run dev`).
- Production frontend bundled in `frontend/dist/`.

## Pending Tasks
- Prepare demonstration images (valid DR grades, sun/cartoon non-retinal image, blurry image) for live walkthrough.

## Roadmap
- DICOM format support.
- Multi-image bilateral (left + right eye) examination session grouping.
- Exportable PDF clinical summary reports.

## Do Not Break / Protected Components
- **Model Checkpoint**: `backend/models/best_efficientnet_b3.pth` (Epoch 7 weights).
- **Preprocessing Function**: `preprocess_fundus()` in `backend/app/ml/preprocessing.py`.
- **Inference Function**: `run_inference()` in `backend/app/ml/inference.py`.
- **Grad-CAM Target Layer**: `model.features[-1]` forward/backward hooks.
- **API Aliases**: `/api/prediction` and `/api/predict` must remain functional.

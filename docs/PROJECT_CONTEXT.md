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
## Protected Working Core

Protected components:
- `backend/models/best_efficientnet_b3.pth`
- `backend/app/ml/model.py`
- `backend/app/ml/inference.py`
- `backend/app/ml/preprocessing.py`
- `backend/app/ml/gradcam.py`

Existing API aliases:
- `POST /api/prediction`
- `POST /api/predict`

Regression baseline:
- 16 backend regression tests passing
- Frontend production build passing

> [!IMPORTANT]
> NO future agent may replace or modify these protected core components without explicit approval.


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
- **Phase 0 (System Freeze)**: Complete. EfficientNet-B3 (`best_efficientnet_b3.pth`), `preprocess_fundus()`, and `GradCAM` are strictly protected and frozen.
- **Phase 1 (Referable Mapping Level 2+)**: Complete. Referable DR clinical mapping aligned with Grades 2, 3, 4 with configurable minimum grade (`MIN_REFERABLE_GRADE=2`).
- **Phase 2 (Adversarial Hardening of the Fundus Gate)**: Complete. Multi-signal deterministic heuristic gate hardened against adversarial orange/red backgrounds, circular graphics, and full adversarial matrix with verified zero-inference interception.
- **Phase 3 (Complete Image-Quality Assessment)**: Complete. Implemented `QualityService` (`quality_service.py`) evaluating Focus, Illumination, Contrast, Field of View, and Glare. Categorizes images into `GOOD`, `BORDERLINE`, and `UNGRADEABLE` with clinical `recapture_guidance`. Integrated into `prediction_service.py` with verified zero inference on ungradeable captures.
- **Phase 4 (Borderline Fundus Enhancement and Recapture Guidance)**: Complete. Implemented `FundusEnhancer` (`backend/app/ml/enhancement.py`) applying conservative LAB CLAHE (`clipLimit=2.0`, `tileGridSize=(8, 8)`) and mild illumination normalization strictly to `BORDERLINE` captures, with safety verification and automatic reversion to untouched original on degradation. `GOOD` and `UNGRADEABLE` captures strictly bypass enhancement.
- **Phase 5 (Retinal Structure Analysis)**: Complete. Implemented classical CV anatomical localization in `backend/app/retina/`: optic disc detection (`optic_disc.py`), fovea localization (`fovea.py`), and green-channel vessel segmentation and skeletonization (`vessels.py`). Orchestrated via `retinal_analysis.py` with complete failure isolation.
- **Phase 6 (Lesion Candidate Analysis — Research Only)**: Complete. Implemented research-oriented candidate lesion evidence in `backend/app/retina/`: microaneurysms (`microaneurysms.py`), hard exudates (`exudates.py`), hemorrhages (`hemorrhages.py`), and neovascularization cluster heuristics (`neovascularization.py`). Orchestrated via `lesion_analysis.py` with explicit `research_only: True` telemetry and clinical disclaimer; strictly isolated from the frozen EfficientNet classifier.
- **Phase 7 (Post-Hoc Confidence Calibration)**: Complete. Implemented `TemperatureScaler` (`backend/app/ml/calibration.py`) applying $p = \text{softmax}(\log(p) / T)$ with persisted parameters in `backend/models/calibration.json` and optimization script `backend/scripts/calibrate_model.py`. Accurately mitigates overconfidence while strictly preserving predicted class rank and argmax.
- **Phase 8 (Automated Annotated Screening Report)**: Complete. Implemented `ReportService` (`backend/app/services/report_service.py`) and API endpoints `GET /api/reports/{id}` and `GET /api/reports/{id}/json` in `backend/app/api/routes/reports.py`. Features print-ready CSS layout, HTML entity escaping against XSS, complete failure isolation for missing artifacts, and zero model inference execution during report rendering.
- **Phase 9 (Frontend Extensions)**: Complete. Implemented typed React cards (`QualityAssessmentCard.tsx`, `RetinalStructuresCard.tsx`, `LesionEvidenceCard.tsx`, `ConfidenceCalibrationCard.tsx`, `ReportActions.tsx`) seamlessly integrated into `Results.tsx` without breaking existing UI components or layout. All optional fields degrade gracefully without crashing.
- **Phase 10 (Timing and Performance Instrumentation)**: Complete. Implemented `PipelineTimer` (`backend/app/services/timing_service.py`) utilizing monotonic `time.perf_counter()` to instrument all major pipeline stages (`file_validation`, `preprocessing`, `inference`, `gradcam`, `retinal_structures`, `lesion_analysis`, `calibration`). Tracks warm vs cold start executions and exposes structured `TimingInfo` in API responses and history records.
- **70/70 pytest tests passing** (67 baseline regression tests preserved + 3 Phase 10 tests).
- **Frontend production build compiles cleanly** (`npm run build` succeeds).

## Phase 2 Architecture & Gating Details

### Gating Pipeline Order
```text
UPLOAD -> FILE VALIDATION -> IMAGE DECODE -> FUNDUS VALIDATION GATE -> QUALITY GATE -> PREPROCESSING -> EFFICIENTNET -> GRAD-CAM
```
The fundus gate executes BEFORE `preprocess_fundus()`, `run_inference()`, `GradCAM`, and `generate_explanation()`.
For any invalid or non-retinal image, the pipeline aborts immediately, returning `status: "INVALID_IMAGE"`, with `quality.status: "INVALID"` and descriptive reasons. Zero model inference calls are made.

### Exposed Structured Validation Signals
The gate exposes 7 structured continuous signals in `FundusValidationSignals` (`quality.signals`):
1. `aspect_ratio_score`: Aspect ratio consistency with standard retinal fundus photography (expected 0.70 - 1.45).
2. `fov_score`: Circular/elliptical optical aperture geometry (area ratio, circularity, camera mask).
3. `dark_boundary_score`: Camera peripheral unilluminated optical boundary (dark corners from camera mask).
4. `retinal_color_score`: Retinal hemoglobin absorption physics ($R > G > B$, low blue reflectance, hemoglobin absorption).
5. `texture_score`: Biological macroscopic retinal luminance variance and gradient ($fg\_std > 12.0$).
6. `edge_density_score`: Organic vascular network edge density vs synthetic/text patterns.
7. `vessel_like_score`: Green channel CLAHE + black-hat morphological tubular vessel branching.

### Hard Rejection Conditions
1. **No Plausible FOV Aperture**: Rectangular full-bleed images without circular camera aperture (`fov_score < 0.50` or `not has_camera_mask and area_ratio >= 0.92`).
2. **Missing Peripheral Camera Mask**: Bright corners inconsistent with fundus optical barrels (`dark_boundary_score < 0.35` and `not has_camera_mask`).
3. **Non-Retinal Color Spectrum**: Strong blue dominance, green exceeding red, or lack of red dominance (`retinal_color_score < 0.60`).
4. **Flat / Synthetic Background**: Rejects solid orange, solid red, flat graphics, uniform backgrounds (`texture_score < 0.35`).
5. **In-Focus Synthetic Non-Retinal Images**: In-focus images (`blur_score >= MIN_BLUR_SCORE`) lacking vascular arborization (`vessel_like_score < 0.48`).
6. **Blurry Image Discrimination**: Blurry images (`blur_score < MIN_BLUR_SCORE`) that possess authentic camera aperture and biological macro-texture pass the fundus gate and are caught by the technical quality gate (`LOW_QUALITY`), preserving authentic fundus screening.

### Test Fixtures in Adversarial Matrix
- Local deterministic fixtures in `backend/storage/validation/non_retinal/`:
  - `plain_orange.jpg`: Solid orange background (adversarial test case: $R > G > B$, color alone never qualifies an image)
  - `plain_red.jpg`: Solid red background
  - `orange_circle.jpg`: Synthetic orange disk on black background
  - `kettle.jpg`: Kettle / product / object
  - `cartoon.jpg`: Cartoon illustration
  - `face.jpg`: Face / person
  - `landscape.jpg`: Outdoor landscape
  - `text_document.jpg`: Text document
  - `screenshot.jpg`: Computer UI screenshot
  - `blue_background.jpg`: Blue object / background
  - `uniform_gray.jpg`: Uniform gray background
- Root sample fixtures:
  - `sun.jpg`: Yellow sun with bright blue sky
  - `missminutes.webp`: Cartoon character on white background
- Valid fundus fixture:
  - `backend/storage/samples/sample_no_dr.jpg`: Authentic valid fundus photograph

## Changed Files in Phase 2
- `backend/app/utils/image_utils.py`: Added `FundusValidationSignals`, multi-signal evaluation (7 signals), and hardened hard-rejection rules.
- `backend/app/schemas/prediction.py`: Added `signals: Optional[Dict[str, float]]` to `QualityInfo`.
- `backend/app/services/prediction_service.py`: Populated `signals` dict in both valid and rejected responses.
- `backend/tests/test_non_retinal_gate.py`: Added zero-inference assertions on full adversarial matrix, regression execution, and signal assertions.
- `backend/storage/validation/non_retinal/*.jpg`: 11 local deterministic test fixtures.
- `docs/PROJECT_CONTEXT.md`: Documented Phase 2 status, architecture, and signals.
- `docs/ARCHITECTURE.md`: Updated architecture documentation with multi-signal gate details.

## Known Limitations
- The fundus validation gate uses classical deterministic CV and morphological signal processing without external neural networks or cloud APIs, maintaining sub-millisecond latency.
- Authentic severely blurry images are handled by the technical quality gate as `LOW_QUALITY` rather than `INVALID_IMAGE` because they are authentic fundus captures requiring recapture rather than domain rejection.

## Test Status
- **Pytest Suite**: 22 tests collected, 22 passed in 3.59s (100% pass rate).
- **Zero-Inference Proof**: Verified with unittest.mock that `run_inference`, `preprocess_fundus`, `GradCAM`, and `generate_explanation` receive exactly 0 calls for every non-retinal image.
- **Frontend Build**: Vite + TypeScript compiled 1,488 modules cleanly with zero errors.

## Deployment Status
- Local development ready via FastAPI (`uvicorn app.main:app --port 8000`) and Vite (`npm run dev`).
- Production frontend bundled in `frontend/dist/`.

## Do Not Break / Protected Components
- **Model Checkpoint**: `backend/models/best_efficientnet_b3.pth` (Epoch 7 weights - FROZEN).
- **Preprocessing Function**: `preprocess_fundus()` in `backend/app/ml/preprocessing.py` (PROTECTED).
- **Inference Function**: `run_inference()` in `backend/app/ml/inference.py` (PROTECTED).
- **Grad-CAM Target Layer**: `model.features[-1]` forward/backward hooks in `backend/app/ml/gradcam.py` (PROTECTED).
- **API Aliases**: `/api/prediction` and `/api/predict` must remain functional.

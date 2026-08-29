# Explainable DR Screening 👁️🔬

> **Production-grade AI platform for Diabetic Retinopathy screening with transparent Grad-CAM visual explainability heatmaps.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-EfficientNet--B3-EE4C2C.svg)](https://pytorch.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-3178C6.svg)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![Tests](https://img.shields.io/badge/Tests-Passing%20100%25-brightgreen.svg)]()

---

## 🌟 Overview

**Explainable DR Screening** is an end-to-end medical AI application that takes a color retinal fundus image, applies deterministic field-of-view cropping and normalization, executes an already-trained **EfficientNet-B3** PyTorch model, classifies the disease across 5 standardized severity grades, calculates referable diabetic retinopathy risk using a calibrated cutoff threshold (`0.13`), and generates transparent **Grad-CAM** visual attention maps directly from the model's final convolutional layer (`features[-1]`).

---

## ✨ Features

- 📸 **Fundus Upload & Validation**: Fast drag-and-drop file upload supporting PNG, JPG, JPEG, and WEBP with client & server-side validation.
- 🔬 **Deterministic Preprocessing**: Automatic circular FOV border detection (`crop_retina`), $380 \times 380$ interpolation, and ImageNet standardization.
- 🎯 **5-Class DR Classification**:
  - `0`: No DR
  - `1`: Mild DR
  - `2`: Moderate DR
  - `3`: Severe DR
  - `4`: Proliferative DR
- 📊 **Softmax Probability Distribution**: Real-time breakdown across all 5 clinical categories summing to 100%.
- ⚠️ **Referable DR Risk Evaluation**: High-sensitivity triage against configured decision threshold (`0.13`).
- 🧠 **Authentic Grad-CAM Explainability**: Visual heatmaps generated via PyTorch hooks on `model.features[-1]`, complete with interactive Overlay, Heatmap, and Side-by-Side tabs.
- 📋 **Clinical Rationale & Guidance**: Deterministic, screening-level diagnostic explanations and referral recommendations.
- 🗄️ **Screening Audit Trail**: Local SQLite database logging past evaluations for complete traceability.
- ⚡ **1-Click Test Samples**: Pre-generated sample fundus images for instant demo testing.
- 🛡️ **Prominent Medical Disclaimer**: Clear clinical research labeling.

---

## 🏛️ System Architecture

```
User (Web Browser)
  ↓
Upload retinal fundus image
  ↓
Frontend validation + preview (React + TypeScript)
  ↓
FastAPI Backend (/api/predict)
  ↓
Exact preprocessing pipeline (FOV Crop + 380x380)
  ↓
EfficientNet-B3 (PyTorch Checkpoint)
  ↓
5-class DR prediction + Referable DR (Threshold 0.13) + Grad-CAM (features[-1])
  ↓
Structured API response (JSON + Artifact URLs)
  ↓
React Results Dashboard & Grad-CAM Viewer
```

---

## 📊 Dataset & Model Benchmarks

Trained and evaluated on the benchmark **APTOS 2019 Blindness Detection** dataset (3,662 total fundus images; disjoint Train/Val/Test splits).

### Test Set Performance
| Metric | Value |
| :--- | :--- |
| **Overall Accuracy** | **81.42%** |
| **Weighted-F1** | **0.8195** |
| **Validation Macro-F1** | **0.7012** (Epoch 7) |
| **Referable DR Sensitivity** | **85.40%** (Standard) / **94.81%** (Threshold 0.13) |
| **Referable DR Specificity** | **96.07%** (Standard) / **93.87%** (Threshold 0.13) |
| **Referable DR Precision** | **92.86%** |
| **Referable DR ROC-AUC** | **0.9827** |

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
- Python 3.10+ (64-bit)
- Node.js 18+ and npm

### 2. Backend Setup
```bash
cd backend
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate

# Install dependencies:
pip install -r requirements.txt

# Run Model Verification:
python scripts/verify_model.py

# Start FastAPI server:
uvicorn app.main:app --reload --port 8000
```
- API Server: `http://localhost:8000`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- Web Application: `http://localhost:5173`

---

## 🧪 Testing

Run the automated backend test suite:
```bash
cd backend
pytest tests -v
```

---

## 📚 Documentation Index

- [Architecture Design](docs/ARCHITECTURE.md)
- [ML Model Specification](docs/MODEL.md)
- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Local Development Guide](docs/DEVELOPMENT.md)
- [Project Context & Memory System](docs/PROJECT_CONTEXT.md)

---

## ⚠️ Medical Disclaimer

> **IMPORTANT:** This AI system is intended for **research and screening support only**. It is **not a medical diagnosis** and should not replace examination or advice from a qualified eye-care professional (ophthalmologist or optometrist).

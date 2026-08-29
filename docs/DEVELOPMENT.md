# Local Development Guide - Explainable DR Screening

## Prerequisites
- Windows, macOS, or Linux
- Python 3.10 or 3.11
- Node.js 18+ and npm

## Project Structure
```
Diabetes Retinothapy/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # Health, Prediction, and History endpoints
│   │   ├── core/                # Config, logging, settings
│   │   ├── ml/                  # EfficientNet-B3, Preprocessing, Grad-CAM, Inference
│   │   ├── schemas/             # Pydantic validation schemas
│   │   ├── services/            # Business & orchestration logic
│   │   └── utils/               # File and image helpers
│   ├── models/
│   │   └── best_efficientnet_b3.pth  # Trained PyTorch weights
│   ├── scripts/
│   │   ├── verify_model.py      # End-to-end model verification script
│   │   └── generate_samples.py  # Test fundus image generator
│   ├── storage/                 # Uploads, heatmaps, and SQLite database
│   ├── tests/                   # Pytest automated test suite
│   ├── requirements.txt
│   └── conftest.py
│
├── frontend/
│   ├── src/
│   │   ├── components/          # UI components (Uploader, Preview, GradCAM, etc.)
│   │   ├── pages/               # Home, Screening, Results, History
│   │   ├── services/            # Typed API client
│   │   ├── hooks/               # usePrediction state hook
│   │   └── utils/               # Formatting, colors, and helpers
│   ├── public/                  # Static assets & test samples
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── docs/                        # Complete technical documentation
└── README.md
```

## Running Locally

### Step 1: Start Backend (Terminal 1)
```powershell
cd backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```
- API is running at: `http://localhost:8000`
- Interactive Swagger docs at: `http://localhost:8000/docs`

### Step 2: Start Frontend (Terminal 2)
```powershell
cd frontend
npm run dev
```
- Frontend application runs at: `http://localhost:5173`

## Running Tests
To run the automated backend test suite:
```powershell
cd backend
.\.venv\Scripts\pytest tests -v
```

To run model verification:
```powershell
cd backend
.\.venv\Scripts\python scripts\verify_model.py
```

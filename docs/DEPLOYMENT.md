# Deployment Guide - Explainable DR Screening

## Production Deployment Checklist

### 1. Environment Preparation
Ensure the server environment satisfies:
- Python 3.10+ (64-bit)
- Node.js 18+ & npm
- (Optional) CUDA-enabled NVIDIA GPU with cuDNN for hardware acceleration.

### 2. Backend Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Or on Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify model checkpoint
python scripts/verify_model.py
```

### 3. Production Server Execution (Backend)
Run Uvicorn with multiple workers for high throughput:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. Frontend Production Build (Frontend)
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Build optimized production bundle
npm run build
```
The production bundle is compiled to `frontend/dist/`.

### 5. Serving Frontend
You can serve the static build using Nginx, Caddy, or serve it directly:
```nginx
# Sample Nginx Configuration
server {
    listen 80;
    server_name dr-screening.example.com;

    # Frontend Static Files
    location / {
        root /path/to/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API Proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        client_max_body_size 15M;
    }

    # Static Storage Proxy (Heatmaps & Overlays)
    location /storage/ {
        proxy_pass http://127.0.0.1:8000/storage/;
        proxy_set_header Host $host;
    }
}
```

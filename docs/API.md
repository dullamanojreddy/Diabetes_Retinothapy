# REST API Specification - Explainable DR Screening

## Base URL
- Development: `http://localhost:8000/api`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`

---

## Endpoints

### 1. Health Liveness Probe
`GET /api/health`

#### Description
Returns process liveness, model initialization state, and computation device.

#### Response (200 OK)
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model": "EfficientNet-B3",
  "device": "cpu",
  "version": "1.0.0",
  "timestamp": "2026-09-04T11:00:00.000Z"
}
```

---

### 2. Health Readiness Probe
`GET /api/health/ready`

#### Description
Verifies that the EfficientNet-B3 model checkpoint is loaded in memory and storage directories are writable. Fails closed with `503 Service Unavailable` if unready.

#### Response (200 OK - Ready)
```json
{
  "status": "ready",
  "model_loaded": true,
  "model_version": "b3-aptos-epoch7",
  "storage_available": true,
  "timestamp": "2026-09-04T11:00:00.000Z"
}
```

#### Response (503 Service Unavailable - Not Ready)
```json
{
  "status": "not_ready",
  "model_loaded": false,
  "model_version": "b3-aptos-epoch7",
  "storage_available": false,
  "timestamp": "2026-09-04T11:00:00.000Z"
}
```

---

### 3. Screen Fundus Image
`POST /api/prediction` (Alias: `POST /api/predict`)

#### Description
Uploads a digital retinal fundus photograph and executes the full screening workflow:
1. File security & MIME validation
2. Multi-signal fundus validation gate
3. Technical image quality assessment
4. Preprocessing (circular FOV crop + 380x380 resize + normalization)
5. EfficientNet-B3 model inference
6. Calibrated referable DR threshold evaluation (0.13)
7. Grad-CAM visual attention heatmap generation
8. JSON history index logging

#### Request Format
- Content-Type: `multipart/form-data`
- Fields:
  - `file`: (Required) Retinal image binary (`.jpg`, `.jpeg`, `.png`, max 10MB).
  - `target_class`: (Optional) Integer `0-4` to focus Grad-CAM on a specific DR grade.

#### Response (200 OK - Valid Screening)
```json
{
  "screening_id": "85fda77c-d0ad-4611-88d5-5e8252cd0cfb",
  "status": "VALID",
  "diagnosis": {
    "class_id": 4,
    "label": "Proliferative DR",
    "confidence": 0.6990
  },
  "probabilities": {
    "no_dr": 0.0016,
    "mild_dr": 0.0021,
    "moderate_dr": 0.0098,
    "severe_dr": 0.2875,
    "proliferative_dr": 0.6990
  },
  "referable": {
    "probability": 0.9984,
    "threshold": 0.13,
    "status": "REFERABLE"
  },
  "quality": {
    "status": "ACCEPT",
    "reasons": []
  },
  "explainability": {
    "available": true,
    "overlay_url": "/results/overlay_85fda77c.jpg",
    "heatmap_url": "/results/heatmap_85fda77c.jpg",
    "original_url": "/results/original_85fda77c.jpg"
  },
  "model": {
    "name": "EfficientNet-B3",
    "version": "b3-aptos-epoch7"
  },
  "created_at": "2026-09-04T11:00:00.000Z"
}
```

#### Rejection Response (422 Unprocessable Content - Non-Retinal Image)
```json
{
  "screening_id": "3b1239c4-954f-4d92-b34e-0a5814bfb229",
  "status": "INVALID_IMAGE",
  "quality": {
    "status": "INVALID",
    "reasons": [
      "Image does not exhibit retinal fundus characteristics (FOV circularity, retinal color profile, or vascular structure)."
    ],
    "width": 400,
    "height": 400,
    "brightness": 120.5,
    "contrast": 35.2,
    "blur_score": 450.0
  },
  "created_at": "2026-09-04T11:00:00.000Z"
}
```

#### Rejection Response (422 Unprocessable Content - Low Quality Fundus)
```json
{
  "screening_id": "2c901e12-421b-419b-a012-70b134dae103",
  "status": "LOW_QUALITY",
  "quality": {
    "status": "LOW_QUALITY",
    "reasons": [
      "Image is excessively blurry or out of focus (blur score: 4.2 < 8.0)."
    ],
    "width": 512,
    "height": 512,
    "brightness": 85.0,
    "contrast": 18.0,
    "blur_score": 4.2
  },
  "created_at": "2026-09-04T11:00:00.000Z"
}
```

#### Error Response (400 Bad Request - Invalid File)
```json
{
  "detail": "Unsupported file format '.pdf'. Allowed formats: .jpg, .jpeg, .png"
}
```

---

### 4. History List
`GET /api/history?limit=50`

#### Description
Returns paginated history records from `storage/history.json`, including both valid predictions and gate rejection outcomes.

#### Response (200 OK)
```json
{
  "total": 12,
  "items": [
    {
      "screening_id": "85fda77c-d0ad-4611-88d5-5e8252cd0cfb",
      "timestamp": "2026-09-04T11:00:00.000Z",
      "filename": "fundus_scan_01.jpg",
      "status": "VALID",
      "predicted_class": 4,
      "predicted_class_name": "Proliferative DR",
      "confidence": 0.6990,
      "referable_probability": 0.9984,
      "is_referable": true,
      "probabilities": { ... },
      "overlay_url": "/results/overlay_85fda77c.jpg"
    }
  ]
}
```

---

### 5. History Detail
`GET /api/history/{screening_id}`

#### Description
Retrieves a single screening audit entry by screening ID.

#### Response (200 OK)
Returns a single `HistoryItem` object.

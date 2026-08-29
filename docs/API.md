# REST API Specification - Explainable DR Screening

## Base URL
- Development: `http://localhost:8000/api`
- OpenAPI Interactive Documentation: `http://localhost:8000/docs`

---

## Endpoints

### 1. Health Check
`GET /api/health`

#### Description
Returns system operational status, model initialization state, and computation device.

#### Response (200 OK)
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model": "EfficientNet-B3",
  "device": "cpu",
  "version": "1.0.0",
  "timestamp": "2026-08-29T21:46:00.000Z"
}
```

---

### 2. Predict Retinopathy
`POST /api/predict`

#### Description
Accepts an uploaded retinal fundus image, runs preprocessing, executes EfficientNet-B3 inference, calculates referable risk, and generates Grad-CAM explainability artifacts.

#### Request Format
- Content-Type: `multipart/form-data`
- Fields:
  - `file`: (Required) Retinal image binary (`.png`, `.jpg`, `.jpeg`, `.webp`, max 10MB).
  - `target_class`: (Optional) Integer `0-4` to override Grad-CAM explanation focus.

#### Example Response (200 OK)
```json
{
  "success": true,
  "id": "e7c4f342-6e21-4f12-9c38-89f5c2b0129a",
  "timestamp": "2026-08-29T21:46:31.250Z",
  "filename": "fundus_scan_01.jpg",
  "prediction": {
    "class_id": 4,
    "class_name": "Proliferative DR",
    "confidence": 0.6990
  },
  "referable": {
    "is_referable": true,
    "probability": 0.9984,
    "threshold": 0.13
  },
  "probabilities": {
    "No DR": 0.0016,
    "Mild DR": 0.0021,
    "Moderate DR": 0.0098,
    "Severe DR": 0.2875,
    "Proliferative DR": 0.6990
  },
  "explainability": {
    "gradcam_available": true,
    "heatmap_url": "/storage/results/heatmap_e7c4f342.jpg",
    "overlay_url": "/storage/results/overlay_e7c4f342.jpg",
    "original_url": "/storage/results/original_e7c4f342.jpg"
  },
  "explanation_text": "AI screening indicates features associated with proliferative diabetic retinopathy (such as neovascularization or preretinal/vitreous hemorrhage patterns).",
  "referral_recommendation": "Screening recommendation: Referable DR detected. Follow-up clinical evaluation by an ophthalmologist or certified eye-care professional is recommended in accordance with standard diabetic eye screening protocols.",
  "inference_time_ms": 142.5,
  "disclaimer": "This AI system is intended for research and screening support only. It is not a medical diagnosis and should not replace examination or advice from a qualified eye-care professional."
}
```

#### Error Responses
- `400 Bad Request`: Invalid file format, empty upload, or non-image content.
- `500 Internal Server Error`: Preprocessing or inference failure.

---

### 3. History List
`GET /api/history?limit=50`

#### Response (200 OK)
```json
{
  "total": 1,
  "items": [
    {
      "id": "e7c4f342-6e21-4f12-9c38-89f5c2b0129a",
      "timestamp": "2026-08-29T21:46:31.250Z",
      "filename": "fundus_scan_01.jpg",
      "predicted_class": 4,
      "predicted_class_name": "Proliferative DR",
      "confidence": 0.6990,
      "referable_probability": 0.9984,
      "is_referable": true,
      "probabilities": { ... },
      "heatmap_url": "/storage/results/heatmap_e7c4f342.jpg",
      "overlay_url": "/storage/results/overlay_e7c4f342.jpg",
      "original_url": "/storage/results/original_e7c4f342.jpg"
    }
  ]
}
```

---

### 4. History Detail
`GET /api/history/{id}`

#### Response (200 OK)
Returns a single `HistoryItem` JSON object.
- `404 Not Found`: If screening ID is not found.

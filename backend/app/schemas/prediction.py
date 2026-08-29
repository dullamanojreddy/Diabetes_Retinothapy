from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "healthy"})
    model_loaded: bool = Field(..., json_schema_extra={"example": True})
    model: str = Field(..., json_schema_extra={"example": "EfficientNet-B3"})
    device: str = Field(..., json_schema_extra={"example": "cuda"})
    version: str = Field(..., json_schema_extra={"example": "1.0.0"})
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PredictionClassInfo(BaseModel):
    class_id: int = Field(..., ge=0, le=4, description="DR severity class ID (0 to 4)")
    class_name: str = Field(..., description="Human readable DR severity name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Predicted class softmax probability")

class ReferableRiskInfo(BaseModel):
    is_referable: bool = Field(..., description="True if referable_probability >= threshold")
    probability: float = Field(..., ge=0.0, le=1.0, description="Sum of probabilities for grades 1..4")
    threshold: float = Field(..., description="Operating decision threshold (default 0.13)")

class ExplainabilityInfo(BaseModel):
    gradcam_available: bool = Field(..., description="Whether Grad-CAM generation succeeded")
    heatmap_url: str = Field(..., description="URL path to normalized Grad-CAM heatmap image")
    overlay_url: str = Field(..., description="URL path to original + Grad-CAM overlay image")
    original_url: str = Field(..., description="URL path to preprocessed retinal fundus image")

class PredictionResponse(BaseModel):
    success: bool = True
    id: str = Field(..., description="Unique screening prediction ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    filename: str = Field(..., description="Original uploaded filename")
    prediction: PredictionClassInfo
    referable: ReferableRiskInfo
    probabilities: Dict[str, float] = Field(
        ...,
        description="Softmax probability distribution across all 5 DR severity grades"
    )
    explainability: ExplainabilityInfo
    explanation_text: str = Field(..., description="Deterministic clinical screening rationale")
    referral_recommendation: str = Field(..., description="Clinical workflow action recommendation")
    inference_time_ms: float = Field(..., description="Inference execution time in milliseconds")
    disclaimer: str = Field(
        default="This AI system is intended for research and screening support only. It is not a medical diagnosis and should not replace examination or advice from a qualified eye-care professional."
    )

class HistoryItem(BaseModel):
    id: str
    timestamp: str
    filename: str
    predicted_class: int
    predicted_class_name: str
    confidence: float
    referable_probability: float
    is_referable: bool
    probabilities: Dict[str, float]
    heatmap_url: str
    overlay_url: str
    original_url: str

class HistoryListResponse(BaseModel):
    total: int
    items: List[HistoryItem]

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class QualityInfo(BaseModel):
    status: str = Field(..., description="ACCEPT | LOW_QUALITY | INVALID")
    reasons: List[str] = Field(default_factory=list, description="Validation failure or quality advisory reasons")
    width: Optional[int] = None
    height: Optional[int] = None
    brightness: Optional[float] = None
    contrast: Optional[float] = None
    blur_score: Optional[float] = None

class DiagnosisInfo(BaseModel):
    class_id: int = Field(..., ge=0, le=4, description="DR severity class ID (0 to 4)")
    label: str = Field(..., description="Human readable DR severity name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Predicted class softmax probability")

    # Compatibility property for existing frontend components expecting class_name
    @property
    def class_name(self) -> str:
        return self.label

class ReferableRiskInfo(BaseModel):
    probability: float = Field(..., ge=0.0, le=1.0, description="Sum of probabilities for grades 1..4")
    threshold: float = Field(..., description="Operating decision threshold (e.g. 0.13)")
    status: str = Field(..., description="REFERABLE or NON_REFERABLE")

    # Compatibility property for existing components
    @property
    def is_referable(self) -> bool:
        return self.status == "REFERABLE"

class ExplainabilityInfo(BaseModel):
    available: bool = Field(True, description="Whether explainability artifacts were generated")
    overlay_url: Optional[str] = Field(None, description="URL path to overlay image artifact")
    heatmap_url: Optional[str] = Field(None, description="URL path to heatmap image artifact")
    original_url: Optional[str] = Field(None, description="URL path to preprocessed/original image artifact")

    # Backward compatibility
    @property
    def gradcam_available(self) -> bool:
        return self.available

class ModelMetadata(BaseModel):
    name: str = Field("EfficientNet-B3", description="Model architecture name")
    version: str = Field("b3-aptos-epoch7", description="Model checkpoint / epoch version")

class PredictionResponse(BaseModel):
    screening_id: str = Field(..., description="Unique screening identifier (UUID)")
    status: str = Field(..., description="Screening outcome: VALID | LOW_QUALITY | INVALID_IMAGE | INVALID_FILE")
    
    # Present when status == VALID
    diagnosis: Optional[DiagnosisInfo] = None
    probabilities: Optional[Dict[str, float]] = Field(
        None,
        description="Softmax probability distribution across all 5 DR severity grades"
    )
    referable: Optional[ReferableRiskInfo] = None
    quality: QualityInfo
    explainability: Optional[ExplainabilityInfo] = None
    model: ModelMetadata = Field(default_factory=ModelMetadata)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Backward-compatible fields and clinical helpers for UI & existing tests
    success: bool = True
    id: Optional[str] = None
    timestamp: Optional[datetime] = None
    filename: Optional[str] = None
    prediction: Optional[DiagnosisInfo] = None
    explanation_text: Optional[str] = None
    referral_recommendation: Optional[str] = None
    inference_time_ms: Optional[float] = None
    disclaimer: str = Field(
        default="This AI system is intended for research and screening support only. It is not a medical diagnosis and should not replace examination or advice from a qualified eye-care professional."
    )

    def model_post_init(self, __context: Any) -> None:
        # Populate backward-compatible fields
        if self.id is None:
            self.id = self.screening_id
        if self.prediction is None and self.diagnosis is not None:
            self.prediction = self.diagnosis
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class RejectionResponse(BaseModel):
    screening_id: str
    status: str  # LOW_QUALITY | INVALID_IMAGE | INVALID_FILE
    quality: QualityInfo
    detail: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class HealthResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "healthy"})
    model_loaded: bool = Field(..., json_schema_extra={"example": True})
    model: str = Field(..., json_schema_extra={"example": "EfficientNet-B3"})
    device: str = Field(..., json_schema_extra={"example": "cuda"})
    version: str = Field(..., json_schema_extra={"example": "1.0.0"})
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ReadinessResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "ready"})
    model_loaded: bool
    model_version: str
    storage_available: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HistoryItem(BaseModel):
    screening_id: str
    timestamp: str
    filename: str
    status: str
    model_version: str = "b3-aptos-epoch7"
    predicted_class: Optional[int] = None
    predicted_class_name: Optional[str] = None
    confidence: Optional[float] = None
    referable_probability: Optional[float] = None
    is_referable: Optional[bool] = None
    probabilities: Optional[Dict[str, float]] = None
    quality: Optional[Dict[str, Any]] = None
    heatmap_url: Optional[str] = None
    overlay_url: Optional[str] = None
    original_url: Optional[str] = None
    
    # Backward compatibility
    @property
    def id(self) -> str:
        return self.screening_id

class HistoryListResponse(BaseModel):
    total: int
    items: List[HistoryItem]

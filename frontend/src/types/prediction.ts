export interface QualityInfo {
  status: "ACCEPT" | "LOW_QUALITY" | "INVALID";
  reasons: string[];
  width?: number;
  height?: number;
  brightness?: number;
  contrast?: number;
  blur_score?: number;
}

export interface DiagnosisInfo {
  class_id: number;
  label: string;
  confidence: number;
  class_name?: string; // Compatibility alias
}

export type PredictionClassInfo = DiagnosisInfo;

export interface ReferableRiskInfo {
  probability: number;
  threshold: number;
  status: "REFERABLE" | "NON_REFERABLE";
  is_referable?: boolean; // Compatibility alias
}

export interface ExplainabilityInfo {
  available: boolean;
  overlay_url?: string;
  heatmap_url?: string;
  original_url?: string;
  gradcam_available?: boolean; // Compatibility alias
}

export interface ProbabilitiesDict {
  [className: string]: number;
}

export interface ModelMetadata {
  name: string;
  version: string;
}

export interface PredictionResponse {
  screening_id: string;
  status: "VALID" | "LOW_QUALITY" | "INVALID_IMAGE" | "INVALID_FILE";
  diagnosis?: DiagnosisInfo;
  probabilities?: ProbabilitiesDict;
  referable?: ReferableRiskInfo;
  quality: QualityInfo;
  explainability?: ExplainabilityInfo;
  model?: ModelMetadata;
  created_at?: string;

  // Compatibility fields for existing UI components
  id?: string;
  success?: boolean;
  filename?: string;
  timestamp?: string;
  prediction?: DiagnosisInfo;
  explanation_text?: string;
  referral_recommendation?: string;
  inference_time_ms?: number;
  disclaimer?: string;
}

export interface RejectionResponse {
  screening_id?: string;
  status: "LOW_QUALITY" | "INVALID_IMAGE" | "INVALID_FILE";
  quality: QualityInfo;
  detail?: string;
  created_at?: string;
}

export interface HealthStatus {
  status: string;
  model_loaded: boolean;
  model: string;
  device: string;
  version: string;
  timestamp: string;
}

export interface ReadinessStatus {
  status: "ready" | "not_ready";
  model_loaded: boolean;
  model_version: string;
  storage_available: boolean;
  timestamp: string;
}

export interface HistoryItem {
  screening_id: string;
  timestamp: string;
  filename: string;
  status: "VALID" | "LOW_QUALITY" | "INVALID_IMAGE" | "INVALID_FILE";
  model_version?: string;
  predicted_class?: number;
  predicted_class_name?: string;
  confidence?: number;
  referable_probability?: number;
  is_referable?: boolean;
  probabilities?: ProbabilitiesDict;
  quality?: QualityInfo | Record<string, any>;
  heatmap_url?: string;
  overlay_url?: string;
  original_url?: string;
  
  // Compatibility alias
  id?: string;
}

export interface HistoryListResponse {
  total: number;
  items: HistoryItem[];
}

export interface PredictionClassInfo {
  class_id: number;
  class_name: string;
  confidence: number;
}

export interface ReferableRiskInfo {
  is_referable: boolean;
  probability: number;
  threshold: number;
}

export interface ExplainabilityInfo {
  gradcam_available: boolean;
  heatmap_url: string;
  overlay_url: string;
  original_url: string;
}

export interface ProbabilitiesDict {
  [className: string]: number;
}

export interface PredictionResponse {
  success: boolean;
  id: string;
  timestamp: string;
  filename: string;
  prediction: PredictionClassInfo;
  referable: ReferableRiskInfo;
  probabilities: ProbabilitiesDict;
  explainability: ExplainabilityInfo;
  explanation_text: string;
  referral_recommendation: string;
  inference_time_ms: number;
  disclaimer: string;
}

export interface HealthStatus {
  status: string;
  model_loaded: boolean;
  model: string;
  device: string;
  version: string;
  timestamp: string;
}

export interface HistoryItem {
  id: string;
  timestamp: string;
  filename: string;
  predicted_class: number;
  predicted_class_name: string;
  confidence: number;
  referable_probability: number;
  is_referable: boolean;
  probabilities: ProbabilitiesDict;
  heatmap_url: string;
  overlay_url: string;
  original_url: string;
}

export interface HistoryListResponse {
  total: number;
  items: HistoryItem[];
}

export interface QualityMetricDetail {
  status: "GOOD" | "ACCEPTABLE" | "POOR" | "DEGRADED";
  score?: number;
  value?: number;
  message?: string;
  [key: string]: any;
}

export interface QualityInfo {
  status: "ACCEPT" | "LOW_QUALITY" | "INVALID" | "GOOD" | "BORDERLINE" | "UNGRADEABLE";
  reasons: string[];
  recapture_guidance?: string[];
  grade?: "GOOD" | "ACCEPTABLE" | "POOR";
  score?: number;
  focus?: QualityMetricDetail;
  illumination?: QualityMetricDetail;
  contrast_detail?: QualityMetricDetail;
  field_of_view?: QualityMetricDetail;
  glare?: QualityMetricDetail;
  width?: number;
  height?: number;
  brightness?: number;
  contrast?: number;
  blur_score?: number;
  enhancement_applied?: boolean;
  enhancement_accepted?: boolean;
  enhancement_method?: string;
  enhancement_details?: Record<string, any>;
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

export interface StructureFinding {
  detected: boolean;
  center_x?: number;
  center_y?: number;
  radius?: number;
  bbox?: [number, number, number, number];
  confidence?: number;
  status?: string;
}

export interface VesselFinding {
  detected: boolean;
  vessel_coverage?: number;
  branch_density?: number;
  status?: string;
}

export interface RetinalStructuresInfo {
  status: "AVAILABLE" | "PARTIAL" | "UNAVAILABLE";
  optic_disc?: StructureFinding;
  fovea?: StructureFinding;
  vessels?: VesselFinding;
}

export interface CandidateFinding {
  name: string;
  candidate_count?: number;
  heuristic_score?: number;
  regions?: [number, number, number, number][];
  indicator?: string;
  status?: string;
}

export interface LesionEvidenceInfo {
  research_only: boolean;
  disclaimer: string;
  status: "AVAILABLE" | "PARTIAL" | "UNAVAILABLE";
  microaneurysms?: CandidateFinding;
  exudates?: CandidateFinding;
  hemorrhages?: CandidateFinding;
  neovascularization?: CandidateFinding;
}

export interface CalibrationInfo {
  temperature: number;
  is_calibrated: boolean;
  calibrated_confidence: number;
  uncalibrated_confidence: number;
  uncalibrated_probabilities: Record<string, number>;
  calibrated_probabilities: Record<string, number>;
  metrics?: Record<string, any>;
}

export interface TimingInfo {
  total_pipeline_ms: number;
  inference_ms: number;
  is_warmup: boolean;
  stages_ms: Record<string, number>;
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
  structures?: RetinalStructuresInfo;
  lesions?: LesionEvidenceInfo;
  calibration?: CalibrationInfo;
  timing?: TimingInfo;
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

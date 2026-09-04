import {
  HealthStatus,
  ReadinessStatus,
  PredictionResponse,
  HistoryListResponse,
  HistoryItem,
  QualityInfo
} from '../types/prediction';

const API_BASE = '/api';

export class ScreeningRejectionError extends Error {
  status: 'LOW_QUALITY' | 'INVALID_IMAGE' | 'INVALID_FILE' | 'API_ERROR';
  reasons: string[];
  screening_id?: string;
  quality?: QualityInfo;

  constructor(
    status: 'LOW_QUALITY' | 'INVALID_IMAGE' | 'INVALID_FILE' | 'API_ERROR',
    message: string,
    reasons: string[] = [],
    screening_id?: string,
    quality?: QualityInfo
  ) {
    super(message);
    this.name = 'ScreeningRejectionError';
    this.status = status;
    this.reasons = reasons;
    this.screening_id = screening_id;
    this.quality = quality;
  }
}

export async function fetchHealth(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: HTTP ${response.status}`);
  }
  return response.json();
}

export async function fetchReadiness(): Promise<ReadinessStatus> {
  const response = await fetch(`${API_BASE}/health/ready`);
  if (!response.ok) {
    throw new Error(`Readiness check failed: HTTP ${response.status}`);
  }
  return response.json();
}

export async function screenFundusImage(
  file: File,
  targetClass?: number
): Promise<PredictionResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (targetClass !== undefined && targetClass !== null) {
    formData.append('target_class', targetClass.toString());
  }

  const response = await fetch(`${API_BASE}/prediction`, {
    method: 'POST',
    body: formData,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    if (response.status === 422) {
      const statusType = data.status === 'LOW_QUALITY' ? 'LOW_QUALITY' : 'INVALID_IMAGE';
      const reasons = data.quality?.reasons || [];
      const msg = statusType === 'LOW_QUALITY'
        ? 'Retinal photograph quality is insufficient for accurate automated screening.'
        : 'The uploaded image could not be verified as a valid retinal fundus photograph.';
      throw new ScreeningRejectionError(
        statusType,
        msg,
        reasons,
        data.screening_id,
        data.quality
      );
    }

    if (response.status === 400) {
      const detailMsg = typeof data.detail === 'string' ? data.detail : 'Invalid file upload.';
      throw new ScreeningRejectionError(
        'INVALID_FILE',
        detailMsg,
        [detailMsg],
        data.screening_id
      );
    }

    const errorMsg = data.detail || `Server error occurred during screening (HTTP ${response.status}).`;
    throw new ScreeningRejectionError('API_ERROR', errorMsg);
  }

  return data as PredictionResponse;
}

// Backward-compatible alias
export const predictFundusImage = screenFundusImage;

export async function fetchHistory(limit: number = 50): Promise<HistoryListResponse> {
  const response = await fetch(`${API_BASE}/history?limit=${limit}`);
  if (!response.ok) {
    throw new Error(`Failed to load history: HTTP ${response.status}`);
  }
  return response.json();
}

export async function fetchHistoryItem(id: string): Promise<HistoryItem> {
  const response = await fetch(`${API_BASE}/history/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to load screening record: HTTP ${response.status}`);
  }
  return response.json();
}

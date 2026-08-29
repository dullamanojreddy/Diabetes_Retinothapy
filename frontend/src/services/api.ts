import { HealthStatus, PredictionResponse, HistoryListResponse, HistoryItem } from '../types/prediction';

const API_BASE = '/api';

export async function fetchHealth(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: HTTP ${response.status}`);
  }
  return response.json();
}

export async function predictFundusImage(
  file: File,
  targetClass?: number
): Promise<PredictionResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (targetClass !== undefined && targetClass !== null) {
    formData.append('target_class', targetClass.toString());
  }

  const response = await fetch(`${API_BASE}/predict`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Analysis failed' }));
    throw new Error(errorData.detail || `Prediction error: HTTP ${response.status}`);
  }

  return response.json();
}

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
